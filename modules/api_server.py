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

# ── Module 1: PC Context endpoint ─────────────────────────────────
@app.get("/api/context/current")
def get_context(auth: str = Depends(_require_auth)):
    """Return the latest PC context snapshot from context_scanner.

    Used by Flutter dashboard to display:
    - Active window title (currently working on: VS Code — main.py)
    - Top CPU processes
    - Recently modified files
    - System stats (CPU %, RAM %)
    - Battery status
    Also includes a pre-formatted Groq injection string.
    """
    try:
        from modules.context_scanner import context_scanner
        snap = context_scanner.get_latest_snapshot()
        summary = context_scanner.get_context_summary()
        return {
            "status": "success",
            "summary": summary,
            "snapshot": snap,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ── Module 2: Semantic Memory search endpoint ─────────────────────
@app.get("/api/memory/search")
def search_memory(query: str, top_k: int = 5, auth: str = Depends(_require_auth)):
    """Search user facts semantically and return top results with similarity scores."""
    try:
        from modules.semantic_memory import semantic_memory
        results = semantic_memory.search(query, top_k=top_k)
        return {
            "status": "success",
            "query": query,
            "results": [
                {"key": k, "value": v, "similarity": s}
                for k, v, s in results
            ]
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}



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

@app.websocket("/ws/mouse")
async def mouse_socket(websocket: WebSocket):
    """
    Low-latency WebSocket channel for mouse coordinates, clicks, and scroll.
    """
    await websocket.accept()
    from modules.mouse_control import move_mouse_relative, click_mouse, scroll_mouse
    try:
        while True:
            raw = await websocket.receive_text()
            data = _json.loads(raw)
            msg_type = data.get("type")
            if msg_type == "move":
                move_mouse_relative(data.get("dx", 0.0), data.get("dy", 0.0))
            elif msg_type == "click":
                click_mouse(data.get("button", "left"))
            elif msg_type == "scroll":
                scroll_mouse(data.get("amount", 0))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[API] Mouse WS error: {e}")

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

@app.get("/api/files/search")
def search_files(query: str = "", _auth: str = Depends(_require_auth)):
    """Search for files in safe directory trees instantly using Indexer or manual walk."""
    if not query or len(query.strip()) < 2:
        return {"entries": []}
    
    query = query.strip()
    results = []
    
    # 1. Try Windows Search Indexer
    try:
        import win32com.client
        connection = win32com.client.Dispatch("ADODB.Connection")
        recordset = win32com.client.Dispatch("ADODB.Recordset")
        
        connection.Open("Provider=Search.CollatorDSO;Extended Properties='Application=Windows';")
        
        scope_clauses = []
        for r in _SAFE_ROOTS:
            if r.exists():
                scope_clauses.append(f"SCOPE='file:{r}'")
        
        if scope_clauses:
            scope_query = " OR ".join(scope_clauses)
            sql = (
                f"SELECT System.ItemName, System.ItemPathDisplay, System.ItemSize, System.DateModified "
                f"FROM SystemIndex WHERE ({scope_query}) "
                f"AND System.ItemName LIKE '%{query}%'"
            )
            
            recordset.Open(sql, connection)
            
            count = 0
            while not recordset.EOF and count < 100:
                name = recordset.Fields("System.ItemName").Value
                path_str = recordset.Fields("System.ItemPathDisplay").Value
                size = recordset.Fields("System.ItemSize").Value
                modified = recordset.Fields("System.DateModified").Value
                
                if name and path_str and _is_safe_path(path_str):
                    p = Path(path_str)
                    results.append({
                        "name": name,
                        "path": path_str,
                        "type": "directory" if p.is_dir() else "file",
                        "size": size,
                        "modified": float(modified) if modified else None,
                        "extension": p.suffix.lower() if p.is_file() else None,
                    })
                    count += 1
                recordset.MoveNext()
            
            recordset.Close()
        connection.Close()
    except Exception as e:
        print(f"[API Search] Windows Indexer failed: {e}. Falling back to manual walk.")
        
    # 2. Fallback to manual directory walk
    if not results:
        count = 0
        query_lower = query.lower()
        for r in _SAFE_ROOTS:
            if not r.exists():
                continue
            for root, dirs, files in os.walk(str(r)):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in {'node_modules', 'build', 'venv', '.git'}]
                for name in dirs + files:
                    if query_lower in name.lower():
                        item = Path(root) / name
                        try:
                            stat = item.stat()
                            results.append({
                                "name": name,
                                "path": str(item),
                                "type": "directory" if item.is_dir() else "file",
                                "size": stat.st_size if item.is_file() else None,
                                "modified": stat.st_mtime,
                                "extension": item.suffix.lower() if item.is_file() else None,
                            })
                            count += 1
                        except Exception:
                            pass
                        if count >= 100:
                            break
                if count >= 100:
                    break
                    
    results.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))
    return {"entries": results}

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

# ── Notes API (F7) ───────────────────────────────────────────────
class NoteRequest(BaseModel):
    content: str
    tags: str = ""

def _db_conn():
    import sqlite3
    conn = sqlite3.connect("data/memory.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/notes")
def get_notes(limit: int = 20, _auth: str = Depends(_require_auth)):
    try:
        conn = _db_conn()
        rows = conn.execute(
            "SELECT id, content, tags, created_at FROM Notes "
            "WHERE user_id = 1 ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return {"notes": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(500, f"Database error: {e}")

@app.post("/api/notes")
def add_note_api(req: NoteRequest, _auth: str = Depends(_require_auth)):
    from modules.notes_reminders import NotesModule
    NotesModule().save_note(req.content, req.tags)
    return {"status": "success"}

@app.delete("/api/notes/{note_id}")
def delete_note_api(note_id: int, _auth: str = Depends(_require_auth)):
    try:
        conn = _db_conn()
        conn.execute("DELETE FROM Notes WHERE id = ? AND user_id = 1", (note_id,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, f"Database error: {e}")

# ── Tasks API (F7) ────────────────────────────────────────────────
class TaskRequest(BaseModel):
    title: str
    priority: str = "medium"
    due_date: str = ""

@app.get("/api/tasks")
def get_tasks(include_done: bool = False, _auth: str = Depends(_require_auth)):
    try:
        conn = _db_conn()
        where = "user_id = 1" if include_done else "user_id = 1 AND is_done = 0"
        rows = conn.execute(
            f"SELECT id, title, priority, is_done, due_date, created_at "
            f"FROM Tasks WHERE {where} ORDER BY priority DESC, created_at ASC LIMIT 50"
        ).fetchall()
        conn.close()
        return {"tasks": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(500, f"Database error: {e}")

@app.post("/api/tasks")
def add_task_api(req: TaskRequest, _auth: str = Depends(_require_auth)):
    from modules.calendar_tasks import TasksModule
    TasksModule().add_task(req.title, req.priority, req.due_date or None)
    return {"status": "success"}

@app.patch("/api/tasks/{task_id}/done")
def mark_task_done_api(task_id: int, _auth: str = Depends(_require_auth)):
    try:
        conn = _db_conn()
        conn.execute("UPDATE Tasks SET is_done = 1 WHERE id = ? AND user_id = 1", (task_id,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, f"Database error: {e}")

@app.delete("/api/tasks/{task_id}")
def delete_task_api(task_id: int, _auth: str = Depends(_require_auth)):
    from modules.calendar_tasks import TasksModule
    TasksModule().delete_task(task_id)
    return {"status": "success"}


# ── Assignment Pipeline Endpoints (Feature A) ────────────────────
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
import shutil

@app.post("/api/assignment/upload")
def upload_assignment(file: UploadFile = File(...),
                      _auth: str = Depends(_require_auth)):
    """Mobile upload path — user uploads assignment file from phone."""
    inbox = Path("nova_inbox")
    inbox.mkdir(exist_ok=True)
    dest = inbox / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # FolderWatcher will pick this up automatically
    return {"status": "received", "message": f"File {file.filename} queued for processing."}

@app.get("/api/assignment/status")
def get_assignment_status(_auth: str = Depends(_require_auth)):
    """Returns the last 5 assignment records from DB."""
    try:
        from modules.memory_system import db_singleton
        rows = db_singleton.conn.execute(
            "SELECT id, subject, status, output_path, created_at "
            "FROM assignments ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
        results = [dict(r) for r in rows]
        return {"assignments": results}
    except Exception as e:
        return {"assignments": [], "error": str(e)}

@app.get("/api/assignment/download/{assignment_id}")
def download_assignment(assignment_id: int, _auth: str = Depends(_require_auth)):
    """Download a completed assignment file."""
    try:
        from modules.memory_system import db_singleton
        row = db_singleton.conn.execute(
            "SELECT output_path, output_format FROM assignments WHERE id = ?",
            (assignment_id,)
        ).fetchone()
        if not row or not row["output_path"]:
            raise HTTPException(404, "Assignment not found or not yet complete.")
        path = Path(row["output_path"])
        if not path.exists():
            raise HTTPException(404, "Output file missing from disk.")
        media_type = "application/pdf" if str(path).endswith(".pdf") else \
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return FileResponse(str(path), media_type=media_type, filename=path.name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Face Auth Endpoints (Feature B) ──────────────────────────────
import base64
import cv2
import numpy as np

class FaceFrameRequest(BaseModel):
    user_name: str
    frame_b64: str     # base64-encoded JPEG frame from phone camera

def _decode_frame(frame_b64: str) -> np.ndarray:
    """Decode base64 image to numpy array."""
    img_bytes = base64.b64decode(frame_b64)
    np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

@app.post("/api/auth/face/register")
def face_register(req: FaceFrameRequest, _auth: str = Depends(_require_auth)):
    """Register a face from a phone/browser camera frame."""
    from modules.memory_system import db_singleton
    from modules.face_auth import FaceAuth
    auth = FaceAuth(db_singleton)
    frame = _decode_frame(req.frame_b64)
    result = auth.register_from_frame(req.user_name, frame)
    return result

@app.post("/api/auth/face/verify")
def face_verify(req: FaceFrameRequest):
    """
    Verify a face. No API key required — this IS the authentication.
    Returns a session token on success.
    """
    from modules.memory_system import db_singleton
    from modules.face_auth import FaceAuth
    auth = FaceAuth(db_singleton)
    frame = _decode_frame(req.frame_b64)
    result = auth.verify_from_frame(req.user_name, frame)
    if result.get("authenticated"):
        token = auth.create_session(req.user_name)
        return {"authenticated": True, "session_token": token,
                "user_name": req.user_name}
    return {"authenticated": False, "similarity": result.get("similarity", 0),
            "message": result.get("error", "Face not recognized.")}

@app.get("/api/auth/face/status")
def face_status(user_name: str, _auth: str = Depends(_require_auth)):
    """Check if a user has a registered face."""
    from modules.memory_system import db_singleton
    from modules.face_auth import FaceAuth
    auth = FaceAuth(db_singleton)
    return {"registered": auth.is_registered(user_name), "user_name": user_name}

class FaceWebcamRequest(BaseModel):
    user_name: str

@app.post("/api/auth/face/register/webcam")
def face_register_webcam(req: FaceWebcamRequest, _auth: str = Depends(_require_auth)):
    """Trigger the PC webcam to register the user's face."""
    from modules.memory_system import db_singleton
    from modules.face_auth import FaceAuth
    auth = FaceAuth(db_singleton)
    result = auth.register_from_webcam(req.user_name)
    return result

@app.post("/api/auth/face/verify/webcam")
def face_verify_webcam(req: FaceWebcamRequest):
    """Trigger the PC webcam to verify the user's face and return a session token."""
    from modules.memory_system import db_singleton
    from modules.face_auth import FaceAuth
    auth = FaceAuth(db_singleton)
    result = auth.verify_from_webcam(req.user_name)
    if result.get("authenticated"):
        token = auth.create_session(req.user_name)
        return {"authenticated": True, "session_token": token, "user_name": req.user_name}
    return {"authenticated": False, "message": result.get("error", "Webcam authentication failed.")}


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
