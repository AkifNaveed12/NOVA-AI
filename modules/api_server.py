"""
API Server — FastAPI bridge between NOVA core and remote clients.
Runs in a daemon thread alongside the voice pipeline and PyWebView HUD.

All blocking endpoints use plain `def` (not async def) because
nova_core.route() does blocking I/O (Groq, weather, Wikipedia).
FastAPI runs plain def endpoints in its own thread pool automatically.

Covers T2 (foundation), T3 (status WS), T4 (remote command + interactive WS),
T5 (UDP discovery), T6 (onboarding), T7 (coding assistant endpoints).
"""

import os
import asyncio
import threading
import socket
import json as _json
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# ── App instance ──────────────────────────────────────────────────
app = FastAPI(title="NOVA API", version="1.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth ──────────────────────────────────────────────────────────
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def _require_auth(key: str = Depends(_api_key_header)):
    expected = os.getenv("NOVA_API_SECRET", "nova-secret-change-this")
    if not key or key != expected:
        raise HTTPException(status_code=403, detail="Invalid or missing API key.")
    return key

# ── Intents that need multi-turn voice flow ───────────────────────
INTERACTIVE_INTENTS = {"email", "check_email", "whatsapp", "task_queue", "reminder", "calendar"}

# ── WebSocket connection manager ──────────────────────────────────
class _ConnectionManager:
    def __init__(self):
        self._clients: list = []
        self._lock = threading.Lock()

    def connect(self, ws: WebSocket):
        with self._lock:
            self._clients.append(ws)

    def disconnect(self, ws: WebSocket):
        with self._lock:
            if ws in self._clients:
                self._clients.remove(ws)

    async def broadcast(self, message: dict):
        payload = _json.dumps(message)
        dead = []
        with self._lock:
            clients = list(self._clients)
        for ws in clients:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

ws_manager = _ConnectionManager()

# Captured on startup — required for thread-safe push_status() calls
_event_loop: Optional[asyncio.AbstractEventLoop] = None

@app.on_event("startup")
async def _capture_event_loop():
    global _event_loop
    _event_loop = asyncio.get_running_loop()

# ── Health ────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "online", "service": "NOVA API"}

# ── WebSocket: real-time NOVA status ─────────────────────────────
@app.websocket("/ws/status")
async def status_socket(websocket: WebSocket):
    await websocket.accept()
    ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive; client can send pings
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

def push_status(state: str, detail: str = ""):
    """
    Push NOVA's state to all connected WebSocket clients.
    Thread-safe — call from any thread (voice pipeline, speak(), etc.).
    state: 'sleeping' | 'listening' | 'processing' | 'speaking'
    """
    global _event_loop
    if not _event_loop or not _event_loop.is_running():
        return
    payload = {"type": "status", "state": state, "detail": detail}
    try:
        asyncio.run_coroutine_threadsafe(ws_manager.broadcast(payload), _event_loop)
    except Exception as e:
        print(f"[API] push_status error: {e}")

# ── Remote command endpoint ───────────────────────────────────────
class CommandRequest(BaseModel):
    command: str

@app.post("/api/command")
def handle_command(req: CommandRequest, _auth: str = Depends(_require_auth)):
    """
    Execute a text command through the full NOVA NLP pipeline.
    Interactive intents (email, WhatsApp) return interactive_required
    and the client should connect to /ws/interactive instead.
    """
    from modules.nlp_engine import process as nlp_process
    import nova_core

    text = req.command.strip()
    if not text:
        return {"status": "error", "response": "Empty command."}

    result = nlp_process(text)
    intent = result.get("intent", "conversation")

    if intent in INTERACTIVE_INTENTS:
        return {
            "status": "interactive_required",
            "intent": intent,
            "message": (
                f"The '{intent}' command requires a back-and-forth conversation. "
                "Connect to /ws/interactive to continue."
            ),
        }

    try:
        response = nova_core.route(result)
        return {"status": "success", "intent": intent, "response": response or "Done."}
    except Exception as e:
        print(f"[API] Command error: {e}")
        return {"status": "error", "response": "Command failed on the PC."}

# ── Interactive WebSocket ─────────────────────────────────────────
@app.websocket("/ws/interactive")
async def interactive_socket(websocket: WebSocket):
    """
    Multi-turn command channel for email, WhatsApp, reminders, etc.
    Client sends initial command as JSON {"text": "..."}.
    Server bridges speak() → JSON {"type":"speak","text":"..."} back to client.
    Client replies with {"text": "user reply"} for each listen() call.
    """
    await websocket.accept()
    import nova_core
    from modules.nlp_engine import process as nlp_process
    loop = asyncio.get_running_loop()

    async def _ws_speak(text: str):
        await websocket.send_text(_json.dumps({"type": "speak", "text": text}))

    async def _ws_listen() -> str:
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
            data = _json.loads(raw)
            return data.get("text", "")
        except asyncio.TimeoutError:
            return ""

    def sync_speak(text: str):
        asyncio.run_coroutine_threadsafe(_ws_speak(text), loop).result(timeout=10)

    def sync_listen() -> str:
        return asyncio.run_coroutine_threadsafe(_ws_listen(), loop).result(timeout=65)

    try:
        raw = await websocket.receive_text()
        data = _json.loads(raw)
        command = data.get("text", "")

        result = nlp_process(command)
        response = await loop.run_in_executor(
            None,
            lambda: nova_core.route(result, speak_func=sync_speak, listen_func=sync_listen),
        )
        await websocket.send_text(_json.dumps({"type": "final", "text": response or "Done."}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[API] Interactive WS error: {e}")
        try:
            await websocket.send_text(_json.dumps({"type": "error", "text": str(e)}))
        except Exception:
            pass

# ── UDP auto-discovery broadcaster (T5) ──────────────────────────
_udp_stop = threading.Event()

def _udp_broadcast_loop(port: int = 8000, broadcast_port: int = 37020):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(1)

    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"

    payload = _json.dumps({
        "service": "nova-ai",
        "ip": local_ip,
        "port": port,
        "name": hostname,
    }).encode()

    print(f"[UDP] Broadcasting NOVA presence from {local_ip}:{port}")
    while not _udp_stop.is_set():
        try:
            sock.sendto(payload, ("<broadcast>", broadcast_port))
        except Exception as e:
            print(f"[UDP] Broadcast error: {e}")
        _udp_stop.wait(timeout=5)
    sock.close()

def start_udp_broadcaster(api_port: int = 8000):
    _udp_stop.clear()
    threading.Thread(
        target=_udp_broadcast_loop, args=(api_port,),
        daemon=True, name="UDPBroadcastThread"
    ).start()

def stop_udp_broadcaster():
    _udp_stop.set()

# ── Setup endpoints (T6) ─────────────────────────────────────────
@app.get("/api/setup/status")
def setup_status():
    """Returns whether NOVA has been configured. No auth required."""
    from dotenv import load_dotenv
    load_dotenv(override=True)

    groq_key = os.getenv("GROQ_API_KEY", "")
    user_name = ""
    try:
        from modules.config_manager import config_manager
        user_name = config_manager.get("user.name", "")
    except Exception:
        pass

    is_complete = bool(groq_key and "your_key" not in groq_key.lower() and len(groq_key) > 10)
    return {
        "is_complete": is_complete,
        "user_name": user_name,
        "has_email": bool(os.getenv("GMAIL_ADDRESS")),
        "has_spotify": bool(os.getenv("SPOTIFY_CLIENT_ID")),
    }

def _validate_groq_key(key: str) -> bool:
    """Makes a minimal Groq call to verify the key before saving."""
    try:
        from groq import Groq
        client = Groq(api_key=key)
        client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
        )
        return True
    except Exception as e:
        print(f"[Setup] Groq key validation failed: {e}")
        return False

class SetupData(BaseModel):
    user_name: str
    groq_key: str
    email_address: str = ""
    email_app_password: str = ""
    default_city: str = "Wah Cantt"
    whatsapp_contacts: list = []

@app.post("/api/setup")
def save_setup(data: SetupData, _auth: str = Depends(_require_auth)):
    """
    Save user configuration surgically using set_key().
    Validates Groq key before saving — never accepts an invalid key.
    """
    if not data.groq_key or len(data.groq_key) < 10:
        return {"status": "error", "field": "groq_key", "message": "Groq API key is too short."}

    if not _validate_groq_key(data.groq_key):
        return {
            "status": "error",
            "field": "groq_key",
            "message": "Groq API key is invalid. Check it at console.groq.com/keys.",
        }

    env_path = Path(".env")
    if not env_path.exists():
        env_path.touch()

    from dotenv import set_key
    set_key(str(env_path), "GROQ_API_KEY", data.groq_key)
    if data.email_address:
        set_key(str(env_path), "GMAIL_ADDRESS", data.email_address)
    if data.email_app_password:
        set_key(str(env_path), "GMAIL_APP_PASSWORD", data.email_app_password)

    try:
        from modules.config_manager import config_manager
        config_manager.set("user.name", data.user_name.strip())
        config_manager.set("weather.default_city", data.default_city.strip())
        config_manager.set("user.default_city", data.default_city.strip())
    except Exception as e:
        return {"status": "error", "message": f"Config update failed: {e}"}

    if data.whatsapp_contacts:
        try:
            from modules.config_manager import config_manager as _cm
            for contact in data.whatsapp_contacts:
                name = contact.get("name", "").strip()
                phone = contact.get("phone", "").strip()
                if name and phone:
                    _cm.add_contact(
                        name=name, phone=phone,
                        platform="whatsapp", aliases=[name.lower()]
                    )
        except Exception as e:
            print(f"[Setup] Contact save error: {e}")

    from dotenv import load_dotenv
    load_dotenv(override=True)

    # Reinitialise GroqBrain with the new key (it was initialised before setup with empty key)
    try:
        import nova_core
        from modules.groq_brain import GroqBrain
        from modules.config_manager import config_proxy
        nova_core.groq_brain = GroqBrain(config_proxy)
    except Exception as e:
        print(f"[Setup] GroqBrain reinit error: {e}")

    # Reset coding assistant so it picks up the new key on next call
    try:
        from modules.coding_assistant import reset_coding_assistant
        reset_coding_assistant()
    except Exception as e:
        print(f"[Setup] CodingAssistant reset error: {e}")

    return {"status": "success", "message": f"Setup complete. Welcome, {data.user_name}!"}

# ── Coding assistant endpoints (T7) ──────────────────────────────
class ChatMessage(BaseModel):
    message: str

@app.post("/api/chat/code")
def code_chat(req: ChatMessage, _auth: str = Depends(_require_auth)):
    """Coding assistant chat. Returns Markdown-formatted response."""
    from modules.coding_assistant import get_coding_assistant
    try:
        assistant = get_coding_assistant()
        response = assistant.chat(req.message)
        return {"status": "success", "reply": response}
    except RuntimeError as e:
        return {"status": "error", "reply": str(e)}
    except Exception as e:
        print(f"[API] Code chat error: {e}")
        return {"status": "error", "reply": "Internal error. Check server logs."}

@app.post("/api/chat/code/reset")
def code_chat_reset(_auth: str = Depends(_require_auth)):
    """Clear coding assistant conversation history."""
    from modules.coding_assistant import get_coding_assistant
    try:
        get_coding_assistant().reset()
        return {"status": "success", "message": "Conversation cleared."}
    except Exception:
        return {"status": "success", "message": "Nothing to clear."}

# ── System info (F2) ─────────────────────────────────────────────
@app.get("/api/system/info")
def system_info(_auth: str = Depends(_require_auth)):
    import psutil, time, datetime
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')
    net = psutil.net_io_counters()
    battery = psutil.sensors_battery()
    uptime_str = str(datetime.timedelta(
        seconds=int(time.time() - psutil.boot_time())))
    return {
        "cpu_percent": cpu,
        "ram_used_gb": round(ram.used / 1e9, 1),
        "ram_total_gb": round(ram.total / 1e9, 1),
        "ram_percent": ram.percent,
        "disk_used_gb": round(disk.used / 1e9, 1),
        "disk_total_gb": round(disk.total / 1e9, 1),
        "disk_percent": disk.percent,
        "net_sent_mb": round(net.bytes_sent / 1e6, 1),
        "net_recv_mb": round(net.bytes_recv / 1e6, 1),
        "battery_percent": battery.percent if battery else None,
        "battery_charging": battery.power_plugged if battery else None,
        "uptime": uptime_str,
    }

# ── File operations (F3/F4) ───────────────────────────────────────
import subprocess as _subprocess

# Only these roots are accessible — prevents path traversal
_SAFE_ROOTS = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.cwd(),
]

def _is_safe_path(raw: str) -> bool:
    try:
        p = Path(raw).resolve()
        return any(
            p == r.resolve() or r.resolve() in p.parents
            for r in _SAFE_ROOTS
        )
    except Exception:
        return False

_TEXT_EXTENSIONS = {
    '.py', '.js', '.ts', '.dart', '.java', '.c', '.cpp', '.h', '.cs',
    '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.html', '.css',
    '.scss', '.xml', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.env', '.txt', '.md', '.csv', '.sh', '.bat', '.ps1', '.sql',
}

@app.get("/api/files/list")
def list_files(path: str = "", _auth: str = Depends(_require_auth)):
    if not path:
        roots = []
        for r in _SAFE_ROOTS:
            if r.exists():
                roots.append({"name": r.name, "path": str(r),
                               "type": "directory", "size": None,
                               "extension": None})
        return {"entries": roots, "path": ""}
    if not _is_safe_path(path):
        raise HTTPException(403, "Path outside allowed directories.")
    p = Path(path)
    if not p.exists():
        raise HTTPException(404, "Path not found.")
    if not p.is_dir():
        raise HTTPException(400, "Not a directory.")
    entries = []
    for item in sorted(p.iterdir(),
                       key=lambda x: (x.is_file(), x.name.lower())):
        try:
            stat = item.stat()
            entries.append({
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
                "size": stat.st_size if item.is_file() else None,
                "modified": stat.st_mtime,
                "extension": item.suffix.lower() if item.is_file() else None,
            })
        except PermissionError:
            pass
    return {"entries": entries, "path": str(p)}

@app.get("/api/files/read")
def read_file(path: str, _auth: str = Depends(_require_auth)):
    if not _is_safe_path(path):
        raise HTTPException(403, "Path outside allowed directories.")
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "File not found.")
    if p.suffix.lower() not in _TEXT_EXTENSIONS:
        raise HTTPException(400, f"File type '{p.suffix}' is not a readable text file.")
    if p.stat().st_size > 500_000:
        raise HTTPException(400, "File too large (max 500 KB).")
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        return {"path": str(p), "content": content,
                "lines": content.count("\n") + 1}
    except Exception as e:
        raise HTTPException(500, f"Read error: {e}")

class FileWriteRequest(BaseModel):
    path: str
    content: str
    create_dirs: bool = True

@app.post("/api/files/write")
def write_file(req: FileWriteRequest, _auth: str = Depends(_require_auth)):
    if not _is_safe_path(req.path):
        raise HTTPException(403, "Path outside allowed directories.")
    p = Path(req.path)
    if req.create_dirs:
        p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(req.content, encoding="utf-8")
        return {"status": "success", "path": str(p),
                "bytes": len(req.content.encode())}
    except Exception as e:
        raise HTTPException(500, f"Write error: {e}")

class MkdirRequest(BaseModel):
    path: str

@app.post("/api/files/mkdir")
def make_dir(req: MkdirRequest, _auth: str = Depends(_require_auth)):
    if not _is_safe_path(req.path):
        raise HTTPException(403, "Path outside allowed directories.")
    Path(req.path).mkdir(parents=True, exist_ok=True)
    return {"status": "success", "path": req.path}

@app.delete("/api/files/delete")
def delete_file(path: str, _auth: str = Depends(_require_auth)):
    if not _is_safe_path(path):
        raise HTTPException(403, "Path outside allowed directories.")
    p = Path(path)
    if not p.exists():
        raise HTTPException(404, "Path not found.")
    try:
        if p.is_dir():
            import shutil
            shutil.rmtree(str(p))
        else:
            p.unlink()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, f"Delete error: {e}")

@app.get("/api/files/open")
def open_file_on_pc(path: str, _auth: str = Depends(_require_auth)):
    """Tell the PC to open a file with its default application."""
    if not _is_safe_path(path):
        raise HTTPException(403, "Path outside allowed directories.")
    if not Path(path).exists():
        raise HTTPException(404, "File not found.")
    try:
        os.startfile(path)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, f"Open error: {e}")

# ── Terminal (F3) ─────────────────────────────────────────────────
class TerminalRequest(BaseModel):
    command: str
    cwd: str = ""
    timeout: int = 30

_TERMINAL_BLOCKED = [
    'rm -rf', 'del /s', 'del /f /s', 'format ', 'net user',
    'reg delete', 'reg add', ':(){', 'taskkill /f /im',
]

@app.post("/api/terminal/run")
def run_terminal(req: TerminalRequest, _auth: str = Depends(_require_auth)):
    cmd_lower = req.command.lower()
    if any(b in cmd_lower for b in _TERMINAL_BLOCKED):
        return {"status": "blocked", "stdout": "",
                "stderr": "Command blocked for safety.", "return_code": -1}
    cwd = req.cwd if (req.cwd and _is_safe_path(req.cwd)) else str(Path.cwd())
    try:
        result = _subprocess.run(
            req.command, shell=True, capture_output=True,
            text=True, timeout=req.timeout, cwd=cwd,
        )
        return {
            "status": "success",
            "stdout": result.stdout[-8000:],
            "stderr": result.stderr[-2000:],
            "return_code": result.returncode,
        }
    except _subprocess.TimeoutExpired:
        return {"status": "timeout", "stdout": "",
                "stderr": f"Timed out after {req.timeout}s.", "return_code": -1}
    except Exception as e:
        return {"status": "error", "stdout": "", "stderr": str(e), "return_code": -1}

# ── Screenshot viewer (F5) ────────────────────────────────────────
@app.get("/api/screenshot/latest")
def get_latest_screenshot(_auth: str = Depends(_require_auth)):
    from fastapi.responses import FileResponse
    screenshots_dir = Path("data") / "screenshots"
    if not screenshots_dir.exists():
        raise HTTPException(404, "No screenshots taken yet.")
    files = sorted(screenshots_dir.glob("*.png"),
                   key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        raise HTTPException(404, "No screenshots found.")
    return FileResponse(str(files[0]), media_type="image/png")

# ── Clipboard sync (F6) ───────────────────────────────────────────
@app.get("/api/clipboard")
def clipboard_get(_auth: str = Depends(_require_auth)):
    import pyperclip
    try:
        return {"content": pyperclip.paste()}
    except Exception as e:
        return {"content": "", "error": str(e)}

class ClipboardSetRequest(BaseModel):
    content: str

@app.post("/api/clipboard")
def clipboard_set(req: ClipboardSetRequest, _auth: str = Depends(_require_auth)):
    import pyperclip
    pyperclip.copy(req.content)
    return {"status": "success"}

# ── Activity log (F9) ─────────────────────────────────────────────
@app.get("/api/activity")
def get_activity(limit: int = 50, _auth: str = Depends(_require_auth)):
    from modules.activity_log import ActivityLogger
    from modules.memory_system import db_singleton
    logger = ActivityLogger(db_singleton)
    logs = logger.get_recent(limit)
    return {"logs": logs}

# ── Uvicorn server control ────────────────────────────────────────
_server: Optional[uvicorn.Server] = None

def start_api_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Called from main.py in a daemon thread.
    Uses uvicorn.Server (not uvicorn.run) so main process can shut it down cleanly.
    """
    global _server
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="error",
        loop="asyncio",
    )
    _server = uvicorn.Server(config)
    _server.run()

def stop_api_server():
    """Signal Uvicorn to stop. Called from main.py shutdown."""
    if _server:
        _server.should_exit = True
