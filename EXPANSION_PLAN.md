# NOVA AI — Expansion Planning
**Web Interface · Android App · Onboarding · Coding Assistant**
*Supersedes docs/planning.md for expansion scope*

---

## How to Use This Document

Every unit of work is called a **T** (Task). Each T is self-contained: it has a goal,
exact files to create/edit, line-by-line steps, a verification checklist, and a note on
any conflict with existing code.

**Before starting any T:**
1. Open `LOG.md` (created in T0)
2. Update "Current T" to the T you're starting
3. Check off steps as you complete them
4. Log any issue you hit and how you resolved it
5. Mark the T complete in the progress table when all verification checks pass

**Golden rule:** Never start T[N+1] until T[N]'s verification checklist is fully green.

---

## Architecture (Locked — Do Not Deviate)

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR PC                                 │
│                                                                 │
│  main thread ──── PyWebView HUD (blocks — never touch)          │
│  voice_pipeline_thread ── STT→NLP→route→TTS (existing)          │
│  api_thread ──── FastAPI + Uvicorn (new — daemon)               │
│  udp_thread ────── UDP broadcaster (new — daemon)               │
│                         │                                       │
│  ┌──────────────────────▼─────────────────────┐                │
│  │  nova_core.route() ← SHARED, needs a Lock  │                │
│  └────────────────────────────────────────────┘                │
└──────────────────────────────┬──────────────────────────────────┘
                               │  Local WiFi (192.168.x.x:8000)
                               │  or Cloudflare Tunnel (remote)
              ┌────────────────┴────────────────┐
              │                                 │
   ┌──────────▼──────────┐         ┌────────────▼────────────┐
   │   Web Browser        │         │   Android App           │
   │   Expo Web Build     │         │   Expo Android APK      │
   │   (same codebase)    │         │   (same codebase)       │
   └─────────────────────┘         └─────────────────────────┘
```

**Thread safety rule:** `nova_core.route()` will be called from BOTH the voice pipeline
thread and the API server thread. A `threading.Lock` is introduced in T1 to prevent
concurrent execution. This is the single most important conflict to resolve.

---

## Tech Stack (Final — No Alternatives)

| Layer | Choice | Reason |
|---|---|---|
| PC API server | FastAPI + Uvicorn | Async-capable, clean WebSocket support |
| PC API startup | `uvicorn.Server` (not `uvicorn.run`) | Allows clean shutdown without killing the process |
| Endpoint style | `def` (not `async def`) for all blocking routes | `nova_core.route()` does blocking I/O; `async def` would freeze the event loop |
| WebSocket | FastAPI native `WebSocket` | Real-time NOVA status push to all clients |
| .env updates | `python-dotenv` `set_key()` | Surgical update — does NOT overwrite other keys |
| Config updates | `config_manager.set(dot.path, value)` | Existing API — do NOT invent `config_manager.update()` |
| LLM model | `llama-3.3-70b-versatile` | Current active model — `llama3-70b-8192` is retired |
| Frontend | Expo (React Native) | Single codebase → Web + Android APK |
| Network discovery | UDP broadcast from PC, listener in app | Auto-discovery; no manual IP entry for users |
| Packaging | PyInstaller `--onedir` (not `--onefile`) | `--onefile` causes 30-60s startup on large apps |
| Remote access | Cloudflare Tunnel (free) | No port forwarding, no static IP required |

---

## LOG.md Format Specification

When T0 creates `LOG.md`, it uses this exact structure. You update it manually as you work.

```markdown
# NOVA AI — Build Log

## Current Status
**Active T:** T1 — Route Thread Safety
**Phase:** Phase 1 — Backend Foundation
**Session started:** 2026-05-26
**Last updated:** 2026-05-26

## Progress Table
| T   | Name                        | Status        | Started    | Completed  |
|-----|-----------------------------|---------------|------------|------------|
| T0  | Log System & Cleanup        | ✅ Done       | 2026-05-26 | 2026-05-26 |
| T1  | Route Thread Safety         | 🔄 In Progress| 2026-05-26 | —          |
| T2  | FastAPI Foundation          | ⏳ Pending    | —          | —          |
...

## Active Work — T1: Route Thread Safety
### What this T does
Adds a threading.Lock around nova_core.route() so the voice pipeline
and API server cannot execute it simultaneously.

### Step checklist
- [x] Step 1: Add _route_lock to nova_core.py
- [ ] Step 2: Wrap route() call in voice_pipeline
- [ ] Step 3: Wrap route() call in api_server
- [ ] Step 4: Verify with print statements

### Issues
- None so far

### Next step
Step 2 — open main.py line 251, wrap the nova_core.route() call

---
## Completed T Logs

### T0: Log System & Cleanup — ✅ Done 2026-05-26
Created LOG.md. Noted config.json has stale model name — flagged for T2.
```

---

## Phase 0: Foundations

---

### T0 — Log System & Pre-flight Cleanup
**Goal:** Create `LOG.md`, fix two pre-existing config bugs that will break later tasks,
and confirm the current codebase runs clean.
**Depends on:** Nothing
**Estimated effort:** 30 minutes

#### Steps

**Step 1 — Create `LOG.md` at the project root**

Create the file `LOG.md` using the exact format from the "LOG.md Format Specification"
section above. Fill in today's date. Set T0 as "In Progress". Leave all other Ts as
"⏳ Pending".

**Step 2 — Fix stale model name in `config.json`**

Open `config.json`. Find:
```json
"groq": {
    "model": "llama3-70b-8192",
```
Change to:
```json
"groq": {
    "model": "llama-3.3-70b-versatile",
```
Reason: `llama3-70b-8192` is decommissioned. Every Groq call that reads this config key
would silently fail with a 404 from the API.

**Step 3 — Remove duplicate user name fields in `config.json`**

`config.json` currently has `"nova": { "user_name": "Akif" }` AND `"user": { "name": "Akif" }`.
The onboarding system (T6) will write to `user.name`. Remove `nova.user_name` to have one
source of truth. Find and delete the line:
```json
"user_name": "Akif",
```
from the `"nova"` block only.

Then in `modules/groq_brain.py`, find any reference to `config.get('nova', {}).get('user_name', 'Akif')`
and change it to `config.get('user', {}).get('name', 'User')`. Do the same in `modules/personality.py`
greeting method default arg.

**Step 4 — Verify clean startup**

Run `python main.py` and confirm:
- HUD opens
- No import errors in console
- "NOVA AI — Initializing..." prints
- Close the HUD window

**Step 5 — Update `LOG.md`**

Mark T0 complete. Set T1 as the active task.

#### Files modified
- `LOG.md` — created
- `config.json` — model name fixed, duplicate user_name removed
- `modules/groq_brain.py` — user_name config key updated
- `modules/personality.py` — user_name config key updated

#### Verification
- [ ] `LOG.md` exists at project root with correct format
- [ ] `config.json` model is `llama-3.3-70b-versatile`
- [ ] Only one `user.name` field in config.json
- [ ] `python main.py` starts without errors

---

## Phase 1: Backend Foundation

---

### T1 — Route Thread Safety
**Goal:** Prevent the voice pipeline and the API server from calling `nova_core.route()`
at the same time, which would cause race conditions in stateful modules (GroqBrain
history, config manager, etc.).
**Depends on:** T0
**Estimated effort:** 30 minutes

#### The Conflict Being Solved

```
voice_pipeline_thread ──► nova_core.route("play music")   ┐
                                                            ├── simultaneous = data corruption
api_thread            ──► nova_core.route("open chrome")  ┘
```

`GroqBrain.conversation_history` is a list. Two threads appending to it at the same time
produces a corrupted history. The fix is one shared lock.

#### Steps

**Step 1 — Add the lock to `nova_core.py`**

Open `nova_core.py`. After the `groq_brain = GroqBrain(_config)` line, add:

```python
import threading
_route_lock = threading.Lock()
```

**Step 2 — Wrap the `route()` function body**

Still in `nova_core.py`, find the `route()` function. Wrap the entire body in the lock:

```python
def route(nlp_result, speak_func=None, listen_func=None) -> str:
    with _route_lock:
        intent   = nlp_result.get("intent", "conversation")
        # ... rest of function unchanged ...
```

Do NOT wrap `dispatch_local()` — it is always called from inside `route()` which already
holds the lock. Double-locking a non-reentrant lock causes deadlock.

**Step 3 — Verify**

Add a temporary print at the top of `route()`:
```python
print(f"[Core] Route acquired lock for intent: {nlp_result.get('intent')}")
```
Run `python main.py`, say a command, confirm the print appears. Remove the print.

#### Files modified
- `nova_core.py` — `_route_lock` added, `route()` body wrapped

#### Verification
- [ ] `_route_lock = threading.Lock()` present in nova_core.py
- [ ] `with _route_lock:` is the first line inside `route()` body
- [ ] `dispatch_local()` is NOT wrapped separately
- [ ] Voice pipeline still works after change

---

### T2 — FastAPI Foundation
**Goal:** Create `modules/api_server.py` with: the FastAPI app, CORS middleware, API key
authentication, a health endpoint, and a clean Uvicorn startup that can be killed
without crashing the main process.
**Depends on:** T1
**Estimated effort:** 1 hour

#### Steps

**Step 1 — Add dependencies to `requirements.txt`**

Open `requirements.txt`. Add under the `# ── Web & APIs` section:
```
fastapi==0.110.0
uvicorn==0.27.1
python-multipart==0.0.9
```

Install them:
```bash
pip install fastapi==0.110.0 uvicorn==0.27.1 python-multipart==0.0.9
```

**Step 2 — Add `NOVA_API_SECRET` to `.env`**

Open `.env`. Add:
```
NOVA_API_SECRET=nova-secret-change-this
```
This is the shared key the app will send in the `X-API-Key` header. Users set this once
during setup. Keep the default value simple but instruct users to change it.

**Step 3 — Create `modules/api_server.py`**

Create the file with this exact content:

```python
"""
API Server — FastAPI bridge between NOVA core and remote clients.
Runs in a daemon thread alongside the voice pipeline and PyWebView HUD.
All endpoints use plain `def` (not async def) because nova_core.route()
does blocking I/O (Groq, weather, Wikipedia). FastAPI runs plain def
endpoints in its own thread pool automatically.
"""

import os
import threading
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Optional

# ── App instance ──────────────────────────────────────────────────
app = FastAPI(title="NOVA API", version="1.0.0", docs_url="/docs")

# ── CORS — required for browser clients ──────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten to specific origins in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth — shared secret in X-API-Key header ─────────────────────
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def _require_auth(key: str = Depends(_api_key_header)):
    expected = os.getenv("NOVA_API_SECRET", "nova-secret-change-this")
    if not key or key != expected:
        raise HTTPException(status_code=403, detail="Invalid or missing API key.")
    return key

# ── WebSocket connection manager ─────────────────────────────────
class _ConnectionManager:
    def __init__(self):
        self._clients: list[WebSocket] = []
        self._lock = threading.Lock()

    def connect(self, ws: WebSocket):
        with self._lock:
            self._clients.append(ws)

    def disconnect(self, ws: WebSocket):
        with self._lock:
            if ws in self._clients:
                self._clients.remove(ws)

    async def broadcast(self, message: dict):
        import asyncio, json
        payload = json.dumps(message)
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

# ── Health ────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "online", "service": "NOVA API"}

# ── Uvicorn server instance (allows clean shutdown) ───────────────
_server: Optional[uvicorn.Server] = None

def start_api_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Called from main.py in a daemon thread.
    Uses uvicorn.Server (not uvicorn.run) so it can be shut down cleanly.
    """
    global _server
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="error",     # suppress access logs — they clutter NOVA console output
        loop="asyncio",
    )
    _server = uvicorn.Server(config)
    _server.run()

def stop_api_server():
    """Call from main.py shutdown sequence."""
    if _server:
        _server.should_exit = True
```

**Step 4 — Launch the API thread in `main.py`**

Open `main.py`. Find the line:
```python
pipeline_thread = threading.Thread(target=voice_pipeline, daemon=True)
```
Directly above it, add:
```python
from modules.api_server import start_api_server
api_thread = threading.Thread(target=start_api_server, daemon=True, name="APIServerThread")
api_thread.start()
print("[API] Server starting on http://0.0.0.0:8000")
```

In the shutdown block at the bottom of `main()` (where `wake_word.stop()` is called), add:
```python
from modules.api_server import stop_api_server
stop_api_server()
```

**Step 5 — Test**

Run `python main.py`. Open a browser and go to `http://localhost:8000/api/health`.
You should see: `{"status": "online", "service": "NOVA API"}`.
Also open `http://localhost:8000/docs` to see the auto-generated API docs.

**Step 6 — Update `LOG.md`**

#### Files created/modified
- `modules/api_server.py` — created
- `main.py` — api_thread launch + stop_api_server in shutdown
- `requirements.txt` — fastapi, uvicorn, python-multipart added
- `.env` — NOVA_API_SECRET added

#### Verification
- [ ] `pip install` completes without errors
- [ ] `GET http://localhost:8000/api/health` returns `{"status":"online",...}`
- [ ] `GET http://localhost:8000/docs` shows Swagger UI
- [ ] PyWebView HUD still opens normally (no conflict)
- [ ] Voice pipeline still works (say a command, get a response)

---

### T3 — WebSocket Status Bridge
**Goal:** Push NOVA's real-time state (sleeping / listening / processing / speaking) to all
connected clients over WebSocket so the app UI can show a live indicator.
**Depends on:** T2
**Estimated effort:** 45 minutes

#### The Problem

HTTP is request-response. The app has no way to know NOVA's current state unless it polls
every second. WebSocket solves this: the PC pushes state changes the instant they happen.

#### Steps

**Step 1 — Add the WebSocket endpoint to `modules/api_server.py`**

Open `modules/api_server.py`. Add this after the health endpoint:

```python
@app.websocket("/ws/status")
async def status_socket(websocket: WebSocket):
    await websocket.accept()
    ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive — client can send pings if needed
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
```

**Step 2 — Add a public `push_status()` function**

Still in `api_server.py`, add below the WebSocket endpoint:

```python
def push_status(state: str, detail: str = ""):
    """
    Called from main.py whenever NOVA's state changes.
    Runs the coroutine in the uvicorn event loop (thread-safe bridge).
    state: 'sleeping' | 'listening' | 'processing' | 'speaking'
    """
    import asyncio
    payload = {"type": "status", "state": state, "detail": detail}
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(ws_manager.broadcast(payload), loop)
    except Exception as e:
        print(f"[API] WebSocket push failed: {e}")
```

**Step 3 — Hook `push_status()` into `main.py`**

In `main.py`, find every `hud.update_status("...")` call in `voice_pipeline`. After each
one, add a matching `push_status()` call. There are 4 state changes:

```python
# At "sleeping":
hud.update_status("sleeping")
push_status("sleeping")

# At "listening":
hud.update_status("listening")
push_status("listening")

# At "processing":
hud.update_status("processing")
push_status("processing")

# At "speaking" (inside the speak() function):
hud.update_status("speaking")
push_status("speaking")
```

Add the import at the top of the `voice_pipeline` function (inside, so it doesn't cause
circular import at module load):
```python
from modules.api_server import push_status
```

**Step 4 — Test with browser console**

Run `python main.py`. Open browser console on any page and run:
```javascript
const ws = new WebSocket("ws://localhost:8000/ws/status");
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```
Say "Hey NOVA". You should see `{type: "status", state: "listening", detail: ""}` appear
in the console, then "processing", then "speaking", then "sleeping".

#### Files modified
- `modules/api_server.py` — WebSocket endpoint + `push_status()` added
- `main.py` — `push_status()` called at each state transition

#### Verification
- [ ] `/ws/status` endpoint exists in api_server.py
- [ ] `push_status()` is exported from api_server.py
- [ ] Browser WebSocket test receives all 4 state transitions correctly
- [ ] No errors in console when no clients are connected (empty broadcast)

---

### T4 — Remote Command Endpoint
**Goal:** Expose `POST /api/command` so the app can send text commands that execute on the
PC through the same NLP pipeline as the microphone, with proper thread safety.
**Depends on:** T3
**Estimated effort:** 1 hour

#### The Interactive Command Problem

Some commands (email, whatsapp, reminders) require a multi-turn voice flow:
NOVA asks → user answers → NOVA acts. These are impossible over a single HTTP POST.

**Solution:** Two modes:
1. **Direct commands** (weather, music, open app, etc.) — handled synchronously, response returned in the HTTP reply
2. **Interactive commands** — the endpoint detects these and returns `{"requires_interactive": true}` so the app can open a dedicated WebSocket chat channel for that flow

The interactive WebSocket channel is built in T5.

#### Steps

**Step 1 — Define the interactive intent set in `api_server.py`**

Open `modules/api_server.py`. Add near the top (after imports):

```python
# These intents require back-and-forth voice flow — cannot run over plain HTTP POST
INTERACTIVE_INTENTS = {"email", "check_email", "whatsapp", "task_queue", "reminder", "calendar"}
```

**Step 2 — Add the command endpoint**

Add to `api_server.py`:

```python
class CommandRequest(BaseModel):
    command: str

@app.post("/api/command")
def handle_command(req: CommandRequest, _auth: str = Depends(_require_auth)):
    """
    Executes a text command through the full NOVA pipeline.
    Uses plain def (not async def) because nova_core.route() is blocking.
    FastAPI runs this in its thread pool automatically.
    """
    from modules.nlp_engine import process as nlp_process
    import nova_core

    text = req.command.strip()
    if not text:
        return {"status": "error", "response": "Empty command."}

    result = nlp_process(text)
    intent = result.get("intent", "conversation")

    # Detect interactive flows — tell the client to use /ws/interactive instead
    if intent in INTERACTIVE_INTENTS:
        return {
            "status": "interactive_required",
            "intent": intent,
            "message": f"The '{intent}' command needs a back-and-forth conversation. "
                       "Connect to /ws/interactive to continue."
        }

    # Execute via NOVA pipeline (lock is inside nova_core.route)
    try:
        response = nova_core.route(result)   # no speak_func/listen_func for remote
        return {"status": "success", "intent": intent, "response": response or "Done."}
    except Exception as e:
        print(f"[API] Command error: {e}")
        return {"status": "error", "response": "Command failed on the PC."}
```

**Step 3 — Add the interactive WebSocket channel**

This allows multi-turn flows (email, WhatsApp) over WebSocket with a custom speak/listen
bridge so the conversation happens in the app:

```python
@app.websocket("/ws/interactive")
async def interactive_socket(websocket: WebSocket):
    """
    Multi-turn command channel. Used for email, WhatsApp, reminders.
    Client sends text → server processes one turn → server sends response text
    → client displays it and sends next user reply → repeat.
    """
    await websocket.accept()
    import asyncio, nova_core
    from modules.nlp_engine import process as nlp_process

    # Thread-safe speak: sends text to client instead of TTS
    async def ws_speak(text: str):
        import json
        await websocket.send_text(json.dumps({"type": "speak", "text": text}))

    # Thread-safe listen: waits for client to send next message
    async def ws_listen() -> str:
        import json
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
            data = json.loads(raw)
            return data.get("text", "")
        except asyncio.TimeoutError:
            return ""

    # Blocking wrappers for speak/listen (route() runs in thread pool)
    def sync_speak(text: str):
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(ws_speak(text), loop).result(timeout=10)

    def sync_listen() -> str:
        loop = asyncio.get_event_loop()
        return asyncio.run_coroutine_threadsafe(ws_listen(), loop).result(timeout=65)

    try:
        # First message from client is the initial command
        import json
        raw = await websocket.receive_text()
        data = json.loads(raw)
        command = data.get("text", "")

        result = nlp_process(command)
        # Run the blocking route() in a thread pool so we don't block the event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: nova_core.route(result, speak_func=sync_speak, listen_func=sync_listen)
        )
        await websocket.send_text(json.dumps({"type": "final", "text": response or "Done."}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[API] Interactive WS error: {e}")
        try:
            await websocket.send_text(json.dumps({"type": "error", "text": str(e)}))
        except Exception:
            pass
```

**Step 4 — Test `POST /api/command`**

Use curl or the Swagger UI at `http://localhost:8000/docs`:
```bash
curl -X POST http://localhost:8000/api/command \
  -H "X-API-Key: nova-secret-change-this" \
  -H "Content-Type: application/json" \
  -d '{"command": "what is the weather"}'
```
Expected response:
```json
{"status": "success", "intent": "weather", "response": "The weather in Wah Cantt..."}
```

Also test an interactive intent:
```bash
curl -X POST http://localhost:8000/api/command \
  -H "X-API-Key: nova-secret-change-this" \
  -H "Content-Type: application/json" \
  -d '{"command": "send email"}'
```
Expected: `{"status": "interactive_required", "intent": "email", ...}`

#### Files modified
- `modules/api_server.py` — `INTERACTIVE_INTENTS`, `CommandRequest`, `/api/command`, `/ws/interactive`

#### Verification
- [ ] `POST /api/command` with weather returns weather string
- [ ] `POST /api/command` with email returns `interactive_required`
- [ ] Missing/wrong API key returns 403
- [ ] Concurrent voice + API commands don't crash (test by saying a command and sending API request simultaneously)

---

### T5 — UDP Network Auto-Discovery
**Goal:** The PC broadcasts its IP address on the local network every 5 seconds so the
phone app can find it automatically — no manual IP entry required.
**Depends on:** T2
**Estimated effort:** 45 minutes

#### Steps

**Step 1 — Add UDP broadcaster to `api_server.py`**

Add at the bottom of `modules/api_server.py`:

```python
import socket, json as _json, time as _time

_udp_stop = threading.Event()

def _udp_broadcast_loop(port: int = 8000, broadcast_port: int = 37020):
    """
    Broadcasts PC's IP and API port on UDP every 5 seconds.
    Phone app listens on UDP port 37020 to discover the PC automatically.
    Payload: {"service": "nova-ai", "ip": "192.168.1.x", "port": 8000}
    """
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
        "name": hostname
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
    t = threading.Thread(target=_udp_broadcast_loop, args=(api_port,),
                         daemon=True, name="UDPBroadcastThread")
    t.start()

def stop_udp_broadcaster():
    _udp_stop.set()
```

**Step 2 — Start the broadcaster in `main.py`**

In `main.py`, right after the `api_thread.start()` line added in T2:
```python
from modules.api_server import start_udp_broadcaster
start_udp_broadcaster(api_port=8000)
```

In the shutdown block:
```python
from modules.api_server import stop_udp_broadcaster
stop_udp_broadcaster()
```

**Step 3 — Test with a simple Python UDP listener**

On any device on the same network (or in a second terminal on the same PC), run:
```python
import socket, json
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("", 37020))
while True:
    data, addr = s.recvfrom(1024)
    print(json.loads(data))
```
You should see the broadcast payload every 5 seconds.

#### Files modified
- `modules/api_server.py` — UDP broadcaster added
- `main.py` — `start_udp_broadcaster` + `stop_udp_broadcaster` called

#### Verification
- [ ] UDP listener script receives broadcast every 5 seconds
- [ ] Payload contains correct local IP and port 8000
- [ ] No errors when no UDP listener is active (broadcast fails silently)
- [ ] `stop_udp_broadcaster()` cleanly stops the loop

---

## Phase 2: Onboarding

---

### T6 — Onboarding Backend
**Goal:** Add setup-detection, a setup endpoint that safely writes to `.env` and
`config.json`, and a validation check for the Groq API key before saving it.
**Depends on:** T2
**Estimated effort:** 1.5 hours

#### The .env Overwrite Problem (from the original guide)

The original plan used `open(".env", "w")` which destroys all existing keys. The fix
is `python-dotenv`'s `set_key()` which updates individual keys surgically.

#### Steps

**Step 1 — Add setup-status endpoint to `api_server.py`**

```python
@app.get("/api/setup/status")
def setup_status():
    """
    Returns whether NOVA has been configured.
    'is_complete' is True only when a real Groq key exists.
    """
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
```

**Step 2 — Add Groq key validation helper**

```python
def _validate_groq_key(key: str) -> bool:
    """Makes a minimal Groq API call to verify the key is valid before saving."""
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
```

**Step 3 — Add the setup endpoint**

```python
from pathlib import Path
from dotenv import set_key

class SetupData(BaseModel):
    user_name: str
    groq_key: str                   # required — no "default key" option (security)
    email_address: str = ""
    email_app_password: str = ""
    default_city: str = "Wah Cantt"
    whatsapp_contacts: list = []    # [{"name": "Mama", "phone": "+923001234567"}]

@app.post("/api/setup")
def save_setup(data: SetupData, _auth: str = Depends(_require_auth)):
    """
    Saves user configuration. Uses set_key() — never overwrites other .env entries.
    Validates Groq key before saving. Returns error if key is invalid.
    """
    # 1. Validate Groq key (mandatory — no embedded default key)
    if not data.groq_key or len(data.groq_key) < 10:
        return {"status": "error", "field": "groq_key", "message": "Groq API key is too short."}

    if not _validate_groq_key(data.groq_key):
        return {"status": "error", "field": "groq_key",
                "message": "Groq API key is invalid. Check it at console.groq.com."}

    env_path = Path(".env")
    if not env_path.exists():
        env_path.touch()

    # 2. Write keys surgically — set_key() updates one key at a time
    set_key(str(env_path), "GROQ_API_KEY", data.groq_key)

    if data.email_address:
        set_key(str(env_path), "GMAIL_ADDRESS", data.email_address)
    if data.email_app_password:
        set_key(str(env_path), "GMAIL_APP_PASSWORD", data.email_app_password)

    # 3. Update config.json via config_manager (never write JSON directly)
    try:
        from modules.config_manager import config_manager
        config_manager.set("user.name", data.user_name.strip())
        config_manager.set("weather.default_city", data.default_city.strip())
        config_manager.set("user.default_city", data.default_city.strip())
    except Exception as e:
        return {"status": "error", "message": f"Config update failed: {e}"}

    # 4. Save WhatsApp contacts to contacts.json
    if data.whatsapp_contacts:
        try:
            from modules.config_manager import config_manager as cm
            for contact in data.whatsapp_contacts:
                name = contact.get("name", "").strip()
                phone = contact.get("phone", "").strip()
                if name and phone:
                    cm.add_contact(
                        name=name,
                        phone=phone,
                        platform="whatsapp",
                        aliases=[name.lower()]
                    )
        except Exception as e:
            print(f"[Setup] Contact save error: {e}")

    # 5. Reload env in the running process
    from dotenv import load_dotenv
    load_dotenv(override=True)

    # 6. Reinitialise GroqBrain with the new key (it was init'd with the old empty key)
    try:
        import nova_core
        from modules.groq_brain import GroqBrain
        from modules.config_manager import config_proxy
        nova_core.groq_brain = GroqBrain(config_proxy)
    except Exception as e:
        print(f"[Setup] GroqBrain reinit error: {e}")

    return {"status": "success", "message": f"Setup complete. Welcome, {data.user_name}!"}
```

**Step 4 — Handle the "no API key" startup case**

The existing `GroqBrain.__init__` prints a warning if the key is missing but doesn't
crash. This is fine. The API server will still start. The setup endpoint is available
from the first second of launch. No changes needed to startup sequence.

**Step 5 — Test setup flow**

```bash
# Check status (should show is_complete: false on a fresh install)
curl http://localhost:8000/api/setup/status \
  -H "X-API-Key: nova-secret-change-this"

# Run setup
curl -X POST http://localhost:8000/api/setup \
  -H "X-API-Key: nova-secret-change-this" \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "Alyan",
    "groq_key": "gsk_your_real_key_here",
    "email_address": "you@gmail.com",
    "email_app_password": "your_app_password",
    "default_city": "Islamabad",
    "whatsapp_contacts": [{"name": "Mama", "phone": "+923001234567"}]
  }'

# Check status again (should show is_complete: true)
curl http://localhost:8000/api/setup/status \
  -H "X-API-Key: nova-secret-change-this"
```

#### Files modified
- `modules/api_server.py` — 3 new endpoints + `_validate_groq_key` helper

#### Verification
- [ ] `GET /api/setup/status` returns `is_complete: false` before setup
- [ ] `POST /api/setup` with invalid Groq key returns error with `field: "groq_key"`
- [ ] `POST /api/setup` with valid data returns success
- [ ] `.env` is updated but existing keys (OPENWEATHER_API_KEY, etc.) are preserved
- [ ] `config.json` `user.name` is updated correctly
- [ ] `GET /api/setup/status` returns `is_complete: true` after successful setup
- [ ] Groq conversation works in voice pipeline after reinit

---

## Phase 3: Coding Assistant

---

### T7 — Coding Assistant Module
**Goal:** Build `modules/coding_assistant.py` — a Groq-powered code assistant with correct
model name, bounded history, lazy initialization, error handling, and a dedicated API endpoint.
**Depends on:** T6 (Groq key must exist at this point)
**Estimated effort:** 1 hour

#### Steps

**Step 1 — Create `modules/coding_assistant.py`**

```python
"""
MODULE 26 — Coding Assistant
==============================
A focused Groq-powered coding assistant. Separate from the main
GroqBrain to maintain independent conversation history and a
code-specific system prompt. Used exclusively through the web/app
interface — never routed through TTS (code is unreadable via speech).

Model: llama-3.3-70b-versatile (same as GroqBrain — confirmed active)
History window: 20 messages (10 turns) — larger than voice brain because
                code context is critical for follow-up questions.
"""

import os
from groq import Groq


_SYSTEM_PROMPT = """You are a senior software engineer assistant embedded in NOVA AI.
Your job is to help the user write, debug, review, and understand code.

Rules:
- Always use Markdown. Wrap all code in fenced code blocks with the correct language tag.
- Be concise. Explain the WHY, not the WHAT. Well-named code explains itself.
- When debugging: state the root cause first, then the fix.
- When writing code: write clean, minimal, production-quality code. No unnecessary comments.
- When reviewing: list concrete issues with file:line references where possible.
- Supported languages: Python, JavaScript, TypeScript, C++, SQL, Bash, React/HTML/CSS.
- If you are unsure, say so. Do not hallucinate APIs or library functions."""


class CodingAssistant:
    HISTORY_WINDOW = 20   # Keep last 20 messages (10 turns)
    MODEL = "llama-3.3-70b-versatile"
    MAX_TOKENS = 2048     # Code responses can be long

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set. Complete setup first.")
        self.client = Groq(api_key=api_key)
        self.history: list[dict] = []

    def chat(self, user_message: str) -> str:
        """Send a message and get a code-focused response."""
        import time

        # Trim history before appending (never after — same fix as GroqBrain)
        if len(self.history) >= self.HISTORY_WINDOW:
            self.history = self.history[-(self.HISTORY_WINDOW - 1):]

        self.history.append({"role": "user", "content": user_message})

        messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + self.history

        for attempt in range(3):
            try:
                completion = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=messages,
                    temperature=0.2,      # Low temp = more accurate code
                    max_tokens=self.MAX_TOKENS,
                )
                response = completion.choices[0].message.content.strip()
                self.history.append({"role": "assistant", "content": response})
                return response

            except Exception as e:
                err = str(e).lower()
                if "rate_limit" in err or "429" in err:
                    wait = 2 ** attempt
                    print(f"[CodingAssistant] Rate limit. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"[CodingAssistant] Error: {e}")
                    self.history.pop()
                    return f"Error: {e}"

        self.history.pop()
        return "Rate limit reached. Please wait a few seconds and try again."

    def reset(self):
        """Clear conversation history."""
        self.history = []
        return "Conversation cleared."


# ── Lazy singleton — created only after setup is complete ────────
_assistant: CodingAssistant | None = None

def get_coding_assistant() -> CodingAssistant:
    """Returns the singleton, initialising on first call. Raises if key not set."""
    global _assistant
    if _assistant is None:
        _assistant = CodingAssistant()
    return _assistant

def reset_coding_assistant():
    """Force re-creation (e.g., after a new Groq key is saved during setup)."""
    global _assistant
    _assistant = None
```

**Step 2 — Add coding assistant endpoints to `api_server.py`**

```python
class ChatMessage(BaseModel):
    message: str

@app.post("/api/chat/code")
def code_chat(req: ChatMessage, _auth: str = Depends(_require_auth)):
    """
    Coding assistant chat endpoint. Uses plain def — Groq call is blocking.
    Returns Markdown-formatted response for the frontend to render.
    """
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
    """Clears the coding assistant's conversation history."""
    from modules.coding_assistant import get_coding_assistant
    try:
        assistant = get_coding_assistant()
        assistant.reset()
        return {"status": "success", "message": "Conversation cleared."}
    except Exception:
        return {"status": "success", "message": "Nothing to clear."}
```

**Step 3 — Reinitialise coding assistant after setup**

In the `save_setup` endpoint (T6), after the GroqBrain reinit block, add:
```python
    # Reset coding assistant so it picks up the new key on next use
    from modules.coding_assistant import reset_coding_assistant
    reset_coding_assistant()
```

**Step 4 — Test**

```bash
curl -X POST http://localhost:8000/api/chat/code \
  -H "X-API-Key: nova-secret-change-this" \
  -H "Content-Type: application/json" \
  -d '{"message": "Write a Python function to reverse a string"}'
```
Expected: JSON with `reply` field containing Markdown-formatted code block.

#### Files created/modified
- `modules/coding_assistant.py` — created
- `modules/api_server.py` — `/api/chat/code` and `/api/chat/code/reset` added
- `modules/api_server.py` — `reset_coding_assistant()` called in `save_setup`

#### Verification
- [ ] `POST /api/chat/code` returns a valid Markdown response
- [ ] Follow-up question uses context from previous message (ask "make it recursive")
- [ ] `POST /api/chat/code/reset` clears history (follow-up no longer remembers previous)
- [ ] Request before setup returns descriptive error, not a Python traceback
- [ ] Rate limit retries work (verify by checking log output)

---

## Phase 4: Frontend

---

### T8 — Expo Project Setup
**Goal:** Create the `nova-app/` Expo project with navigation, screens scaffolded, and
the shared API client that handles auth headers and UDP discovery.
**Depends on:** T4 (UDP discovery must work before testing app connection)
**Estimated effort:** 2 hours

#### Prerequisites (install once)

```bash
node --version    # must be >= 18
npm install -g expo-cli
```

#### Steps

**Step 1 — Create the Expo project**

In the NOVA_AI project root:
```bash
npx create-expo-app nova-app --template blank
cd nova-app
npx expo install expo-router expo-speech @react-native-async-storage/async-storage
npx expo install expo-av react-native-markdown-display
npm install axios
```

**Step 2 — Configure `nova-app/app.json`**

Set the app name and bundle ID:
```json
{
  "expo": {
    "name": "NOVA AI",
    "slug": "nova-ai",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "scheme": "novaai",
    "web": {
      "bundler": "metro",
      "output": "static",
      "favicon": "./assets/favicon.png"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#0a0a1a"
      },
      "package": "com.novaai.app"
    }
  }
}
```

**Step 3 — Create `nova-app/src/api/client.js`**

This is the shared API client used by every screen:

```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const UDP_BROADCAST_PORT = 37020;
const DEFAULT_PORT = 8000;

// ── Persistent config ────────────────────────────────────────────
export async function getServerConfig() {
  const ip     = await AsyncStorage.getItem('nova_server_ip')   || '';
  const apiKey = await AsyncStorage.getItem('nova_api_key')     || 'nova-secret-change-this';
  return { ip, apiKey };
}

export async function saveServerConfig(ip, apiKey) {
  await AsyncStorage.setItem('nova_server_ip', ip);
  await AsyncStorage.setItem('nova_api_key', apiKey);
}

// ── Base URL helper ──────────────────────────────────────────────
export function getBaseUrl(ip) {
  return `http://${ip}:${DEFAULT_PORT}`;
}

// ── Authenticated axios instance ─────────────────────────────────
export async function novaApi() {
  const { ip, apiKey } = await getServerConfig();
  return axios.create({
    baseURL: getBaseUrl(ip),
    headers: { 'X-API-Key': apiKey },
    timeout: 15000,
  });
}

// ── Health check (used on connection screen) ─────────────────────
export async function checkConnection(ip, apiKey) {
  try {
    const res = await axios.get(`http://${ip}:${DEFAULT_PORT}/api/health`, {
      headers: { 'X-API-Key': apiKey },
      timeout: 5000,
    });
    return res.data?.status === 'online';
  } catch {
    return false;
  }
}

// ── UDP auto-discovery (React Native — uses Expo AV for UDP) ─────
// NOTE: Standard Expo does not expose raw UDP sockets.
// Use the manual IP input with QR code as primary method.
// UDP auto-discovery requires a bare Expo (ejected) workflow — skip for now.
// Implementation note left here for future native module addition.
export async function discoverServer() {
  return null;  // placeholder — manual IP is the primary path
}
```

> **Note on UDP discovery in Expo:** Standard Expo (managed workflow) does not expose
> raw UDP sockets. The app will use manual IP entry + QR code scan as the discovery
> method. The PC's UDP broadcaster (T5) is still useful for future native module
> integration or a companion desktop app. This is not a blocker.

**Step 4 — Create the navigation structure**

Create `nova-app/app/_layout.js`:
```javascript
import { Slot, useRouter, useSegments } from 'expo-router';
import { useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function RootLayout() {
  const router = useRouter();
  const segments = useSegments();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    (async () => {
      const ip = await AsyncStorage.getItem('nova_server_ip');
      const setupDone = await AsyncStorage.getItem('nova_setup_complete');
      if (!ip) {
        router.replace('/connect');
      } else if (!setupDone) {
        router.replace('/setup/step1');
      }
      setChecked(true);
    })();
  }, []);

  if (!checked) return null;
  return <Slot />;
}
```

Create these empty screen files (fill in T9-T11):
```
nova-app/app/connect.js          ← Enter PC IP + API key
nova-app/app/setup/step1.js      ← Name
nova-app/app/setup/step2.js      ← Groq key
nova-app/app/setup/step3.js      ← Email (optional)
nova-app/app/setup/step4.js      ← Contacts (optional)
nova-app/app/setup/step5.js      ← City + Done
nova-app/app/(tabs)/_layout.js   ← Tab bar
nova-app/app/(tabs)/index.js     ← Dashboard
nova-app/app/(tabs)/remote.js    ← Voice/text remote
nova-app/app/(tabs)/code.js      ← Coding assistant
```

**Step 5 — Test Expo boots**

```bash
cd nova-app
npx expo start --web
```
Open `http://localhost:8081` in browser. Should show a blank white screen (screens are empty stubs).

#### Files created
- `nova-app/` — entire Expo project
- `nova-app/src/api/client.js` — API client
- `nova-app/app/_layout.js` — root navigation

#### Verification
- [ ] `npx expo start --web` opens without errors
- [ ] Navigation file exists with auto-redirect logic
- [ ] `client.js` exports `novaApi`, `checkConnection`, `saveServerConfig`

---

### T9 — Connection + Onboarding UI
**Goal:** Build the Connect screen (IP entry + test), and all 5 setup wizard screens.
**Depends on:** T8, T6
**Estimated effort:** 3 hours

#### Step 1 — Connect Screen (`nova-app/app/connect.js`)

```javascript
import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { checkConnection, saveServerConfig } from '../src/api/client';

export default function ConnectScreen() {
  const router = useRouter();
  const [ip, setIp] = useState('');
  const [apiKey, setApiKey] = useState('nova-secret-change-this');
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState('');

  const handleConnect = async () => {
    if (!ip.trim()) { setError('Enter your PC\'s IP address.'); return; }
    setTesting(true); setError('');
    const ok = await checkConnection(ip.trim(), apiKey.trim());
    setTesting(false);
    if (ok) {
      await saveServerConfig(ip.trim(), apiKey.trim());
      router.replace('/setup/step1');
    } else {
      setError('Could not connect. Make sure NOVA is running on your PC and both devices are on the same WiFi.');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Connect to NOVA</Text>
      <Text style={styles.hint}>Find your PC's IP: Settings → WiFi → your network → IPv4 Address</Text>
      <TextInput style={styles.input} placeholder="192.168.1.x" value={ip}
        onChangeText={setIp} keyboardType="numeric" placeholderTextColor="#555" />
      <TextInput style={styles.input} placeholder="API Key" value={apiKey}
        onChangeText={setApiKey} placeholderTextColor="#555" />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <TouchableOpacity style={styles.btn} onPress={handleConnect} disabled={testing}>
        {testing ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>Connect →</Text>}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a1a', justifyContent: 'center', padding: 32 },
  title: { color: '#00d4ff', fontSize: 28, fontWeight: 'bold', marginBottom: 8 },
  hint: { color: '#666', fontSize: 13, marginBottom: 24 },
  input: { backgroundColor: '#111', color: '#fff', borderRadius: 10, padding: 14,
           marginBottom: 12, borderWidth: 1, borderColor: '#222' },
  btn: { backgroundColor: '#00d4ff', borderRadius: 10, padding: 16, alignItems: 'center', marginTop: 8 },
  btnText: { color: '#000', fontSize: 16, fontWeight: 'bold' },
  error: { color: '#ff4444', fontSize: 13, marginBottom: 8 },
});
```

#### Step 2 — Setup Wizard (steps 1–5)

Each step follows the same pattern. Here is Step 1 (name) as the full example;
Steps 2–5 follow the same pattern with different fields.

**`nova-app/app/setup/step1.js`** — Name:
```javascript
import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function SetupStep1() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [error, setError] = useState('');

  const next = async () => {
    if (!name.trim()) { setError('Please enter your name.'); return; }
    await AsyncStorage.setItem('setup_user_name', name.trim());
    router.push('/setup/step2');
  };

  return (
    <View style={styles.container}>
      <Text style={styles.step}>Step 1 of 5</Text>
      <Text style={styles.title}>What's your name?</Text>
      <Text style={styles.subtitle}>NOVA will use this to greet you.</Text>
      <TextInput style={styles.input} placeholder="Your name" value={name}
        onChangeText={setName} placeholderTextColor="#555" autoFocus />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <TouchableOpacity style={styles.btn} onPress={next}>
        <Text style={styles.btnText}>Next →</Text>
      </TouchableOpacity>
    </View>
  );
}
// styles same as connect.js — extract to src/styles/setup.js to avoid repetition
```

**`nova-app/app/setup/step2.js`** — Groq API key:

Stores key in AsyncStorage. Shows a link to `console.groq.com/keys`. Has a "Test Key"
button that calls `POST /api/setup` with just the key to validate before proceeding.

**`nova-app/app/setup/step3.js`** — Email (optional, Skip button):

Gmail address + App Password fields. Shows help text explaining App Passwords.
Skip button calls `next()` without setting these values.

**`nova-app/app/setup/step4.js`** — WhatsApp contacts (optional):

A list with "Add Contact" button. Each contact: Name + Phone (with country code hint).
Skip button available.

**`nova-app/app/setup/step5.js`** — City + Final submission:

Default city field. "Finish Setup" button that:
1. Reads all stored AsyncStorage setup values
2. Sends `POST /api/setup` with complete payload
3. On success: sets `nova_setup_complete` in AsyncStorage, navigates to `/(tabs)`
4. On error: shows the specific field error from the server response

#### Files created
- All screen files listed in T8

#### Verification
- [ ] Connect screen shows connection error for wrong IP
- [ ] Connect screen navigates to setup on success
- [ ] Each setup step stores its value in AsyncStorage
- [ ] Step 5 submits to `/api/setup` and navigates to tabs on success
- [ ] Invalid Groq key shows error message from server on step 2 validation
- [ ] Skip works on steps 3 and 4

---

### T10 — Dashboard + Remote Control UI
**Goal:** Build the main app tabs — Dashboard (quick action buttons) and Remote tab
(text command input + real-time NOVA status via WebSocket).
**Depends on:** T9
**Estimated effort:** 2 hours

#### Tab Layout (`nova-app/app/(tabs)/_layout.js`)

```javascript
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TabsLayout() {
  return (
    <Tabs screenOptions={{ tabBarStyle: { backgroundColor: '#0a0a1a', borderTopColor: '#222' },
                           tabBarActiveTintColor: '#00d4ff', tabBarInactiveTintColor: '#555',
                           headerShown: false }}>
      <Tabs.Screen name="index" options={{ title: 'Dashboard',
        tabBarIcon: ({ color }) => <Ionicons name="home" size={22} color={color} /> }} />
      <Tabs.Screen name="remote" options={{ title: 'Remote',
        tabBarIcon: ({ color }) => <Ionicons name="mic" size={22} color={color} /> }} />
      <Tabs.Screen name="code" options={{ title: 'Dev',
        tabBarIcon: ({ color }) => <Ionicons name="code-slash" size={22} color={color} /> }} />
    </Tabs>
  );
}
```

#### Dashboard (`nova-app/app/(tabs)/index.js`)

Quick-action buttons that fire `POST /api/command`:

```javascript
const QUICK_ACTIONS = [
  { label: 'Lock PC',       command: 'lock screen',   icon: 'lock-closed' },
  { label: 'Mute',          command: 'mute',           icon: 'volume-mute' },
  { label: 'Volume Up',     command: 'volume up',      icon: 'volume-high' },
  { label: 'Volume Down',   command: 'volume down',    icon: 'volume-low' },
  { label: 'Screenshot',    command: 'take screenshot', icon: 'camera' },
  { label: 'Open YouTube',  command: 'open youtube',   icon: 'logo-youtube' },
  { label: 'Battery',       command: 'battery level',  icon: 'battery-half' },
  { label: 'CPU Usage',     command: 'cpu usage',      icon: 'speedometer' },
];
```

Each button fires the command and shows the response in a toast/snack notification.

#### Remote Tab (`nova-app/app/(tabs)/remote.js`)

Key features:
1. **Status indicator** — WebSocket to `/ws/status` shows sleeping/listening/speaking with colour
2. **Text input** — type a command and press send
3. **Response display** — last response shown below input
4. **Interactive flow** — if server returns `interactive_required`, open the `/ws/interactive` channel
   and display the conversation as a chat thread

```javascript
// WebSocket status connection (open on mount, keep alive)
useEffect(() => {
  const ws = new WebSocket(`ws://${serverIp}:8000/ws/status`);
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'status') setNovaStatus(data.state);
  };
  ws.onerror = () => setNovaStatus('offline');
  return () => ws.close();
}, [serverIp]);
```

#### Files created/modified
- `nova-app/app/(tabs)/_layout.js`
- `nova-app/app/(tabs)/index.js`
- `nova-app/app/(tabs)/remote.js`

#### Verification
- [ ] Tab bar shows 3 tabs with correct icons
- [ ] Dashboard buttons send commands and show responses
- [ ] Status indicator changes colour when NOVA state changes
- [ ] Text command input works and shows response
- [ ] Interactive command opens chat thread with `/ws/interactive`

---

### T11 — Coding Assistant UI
**Goal:** Build the Dev tab — a ChatGPT-style interface that sends messages to
`/api/chat/code` and renders Markdown responses with syntax-highlighted code blocks.
**Depends on:** T10
**Estimated effort:** 1.5 hours

#### Steps

**Step 1 — Install Markdown renderer**

```bash
cd nova-app
npm install react-native-markdown-display
```

**Step 2 — Build `nova-app/app/(tabs)/code.js`**

```javascript
import { useState, useRef } from 'react';
import { View, TextInput, TouchableOpacity, FlatList, Text,
         KeyboardAvoidingView, Platform, StyleSheet } from 'react-native';
import Markdown from 'react-native-markdown-display';
import { novaApi } from '../../src/api/client';

export default function CodeTab() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I\'m your coding assistant. Ask me to write, debug, or explain code.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const flatList = useRef(null);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');
    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    try {
      const api = await novaApi();
      const res = await api.post('/api/chat/code', { message: text });
      const reply = res.data?.reply || 'No response.';
      setMessages(prev => [...prev, { role: 'assistant', content: reply }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
      setTimeout(() => flatList.current?.scrollToEnd(), 100);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <FlatList ref={flatList} data={messages} keyExtractor={(_, i) => i.toString()}
        style={styles.list} contentContainerStyle={{ padding: 12 }}
        renderItem={({ item }) => (
          <View style={[styles.bubble, item.role === 'user' ? styles.userBubble : styles.novaBubble]}>
            {item.role === 'user'
              ? <Text style={styles.userText}>{item.content}</Text>
              : <Markdown style={markdownStyles}>{item.content}</Markdown>}
          </View>
        )} />
      {loading && <Text style={styles.typing}>NOVA is thinking...</Text>}
      <View style={styles.inputRow}>
        <TextInput style={styles.input} value={input} onChangeText={setInput}
          placeholder="Ask about code..." placeholderTextColor="#555"
          multiline onSubmitEditing={send} />
        <TouchableOpacity style={styles.sendBtn} onPress={send} disabled={loading}>
          <Text style={styles.sendText}>▲</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}
```

The `markdownStyles` object styles code blocks with a monospace font and dark background
to distinguish them from prose.

#### Files created
- `nova-app/app/(tabs)/code.js`

#### Verification
- [ ] Code responses render with syntax-highlighted code blocks
- [ ] Follow-up questions maintain context
- [ ] "Clear conversation" button (header right) calls `/api/chat/code/reset`
- [ ] Long responses scroll correctly

---

## Phase 5: Deployment

---

### T12 — Android APK Build
**Goal:** Generate a standalone Android APK that users can install directly (no Play Store).
**Depends on:** T11 (all screens complete)
**Estimated effort:** 1–2 hours (mostly waiting for build)

#### Steps

**Step 1 — Install EAS CLI**
```bash
npm install -g eas-cli
eas login   # login to your Expo account (free)
```

**Step 2 — Configure EAS build**
```bash
cd nova-app
eas build:configure
```
This creates `eas.json`. Edit it:
```json
{
  "build": {
    "preview": {
      "android": {
        "buildType": "apk",
        "gradleCommand": ":app:assembleRelease"
      }
    }
  }
}
```

**Step 3 — Build the APK**
```bash
eas build --platform android --profile preview
```
This runs in Expo's cloud (free tier: 30 builds/month). Returns a download link to the `.apk`.

**Step 4 — Install on Android**
Transfer the APK to your phone (via USB, email, or download link).
Enable "Install unknown apps" in Android settings for your browser/file manager.
Install and open. You should see the Connect screen.

**Step 5 — Build the web version (same codebase)**
```bash
cd nova-app
npx expo export --platform web
```
This generates a static `dist/` folder. Copy it to a `web/` directory in the NOVA_AI
project root. The FastAPI server can serve it:

In `api_server.py`, add:
```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

_web_dir = Path(__file__).parent.parent / "web"
if _web_dir.exists():
    app.mount("/", StaticFiles(directory=str(_web_dir), html=True), name="static")
```

Now `http://192.168.1.x:8000` opens the web app directly — no separate web server needed.

#### Verification
- [ ] APK installs and opens on Android device
- [ ] Connect screen successfully connects to PC on same WiFi
- [ ] All 3 tabs work from the phone
- [ ] `http://localhost:8000` serves the web app

---

### T13 — PyInstaller Packaging
**Goal:** Package the Python backend as a self-contained Windows `.exe` that users can
run without installing Python. Resolves all known PyInstaller pitfalls for this project.
**Depends on:** T12 (web build must be complete so it's bundled in the exe)
**Estimated effort:** 2–3 hours (debugging hidden imports takes time)

#### Why `--onedir` not `--onefile`

`--onefile` extracts the entire bundle to a temp directory on every launch. For a project
this size (MediaPipe, PyAudio, pywebview, Groq, FastAPI), that extraction takes 30–60
seconds on each startup. `--onedir` extracts once and is ready in ~2 seconds.

#### Steps

**Step 1 — Install PyInstaller**
```bash
pip install pyinstaller==6.5.0
```

**Step 2 — Create `nova.spec`**

Using a `.spec` file instead of command-line flags gives precise control:

```python
# nova.spec
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all data files that PyInstaller won't find automatically
datas = [
    ('modules/nova_hud.html',  'modules'),
    ('config',                  'config'),
    ('assets',                  'assets'),
    ('web',                     'web'),           # Expo web build from T12
    ('.env.example',            '.'),
]

# Add spaCy model data
try:
    datas += collect_data_files('en_core_web_sm')
except Exception:
    pass

hiddenimports = [
    # FastAPI / Uvicorn internals PyInstaller misses
    'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
    'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan', 'uvicorn.lifespan.on',
    'fastapi', 'pydantic', 'starlette',
    # Audio
    'pyaudio', 'speech_recognition', 'pyttsx3',
    'pyttsx3.drivers', 'pyttsx3.drivers.sapi5',
    # Windows COM
    'pythoncom', 'win32com.client', 'win32com.server',
    # Audio control
    'pycaw', 'pycaw.pycaw', 'comtypes',
    # ML / Vision
    'mediapipe', 'cv2', 'numpy',
    # NLP
    'spacy', 'nltk', 'dateparser',
    # Other
    'groq', 'pywebview', 'webview', 'rapidfuzz', 'fuzzywuzzy',
    'spotipy', 'pyautogui', 'psutil', 'screen_brightness_control',
    'pygame', 'pyjokes', 'wikipedia', 'deep_translator',
    'selenium', 'PIL', 'pyperclip',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'test', 'unittest'],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='NOVA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,      # set to True during debugging — hides all output when False
    icon='assets/icon.ico',  # convert nova logo to .ico first
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False,
    upx=True,
    name='NOVA',
)
```

**Step 3 — Build**
```bash
pyinstaller nova.spec
```
Output: `dist/NOVA/` folder. Share the entire `NOVA/` folder (zip it).
The entry point is `dist/NOVA/NOVA.exe`.

**Step 4 — First-run data directory**

The `.exe` needs to create `data/` (for SQLite) and `.env` on first run.
Add to `main.py`, before anything else in `main()`:

```python
import sys, os
# When running as PyInstaller bundle, set working dir to exe location
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
# Ensure required directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("config", exist_ok=True)
if not os.path.exists(".env"):
    import shutil
    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
```

**Step 5 — Test the exe**

Run `dist/NOVA/NOVA.exe`. The HUD should open. Open the phone app, connect to the PC's IP.
The setup wizard should appear (since no Groq key is configured).

#### Files created/modified
- `nova.spec` — created
- `main.py` — frozen-exe working-directory fix + auto data dir creation

#### Verification
- [ ] `pyinstaller nova.spec` completes without fatal errors
- [ ] `NOVA.exe` starts and shows HUD within 5 seconds
- [ ] `http://localhost:8000/api/health` responds from the exe
- [ ] Voice pipeline works from the exe (say a command)
- [ ] Web app loads at `http://localhost:8000`
- [ ] Phone app can connect and send commands

---

## Phase 6: Integration & Conflict Resolution

---

### T14 — End-to-End Integration Testing
**Goal:** Test every cross-system flow and resolve any remaining conflicts.
**Depends on:** T13
**Estimated effort:** 2–3 hours

#### Known Conflicts and Resolutions

| Conflict | Root Cause | Resolution |
|---|---|---|
| `nova_core.route()` called from voice + API simultaneously | Shared mutable state in GroqBrain | T1 added `_route_lock` — verify it holds under concurrent load |
| `GroqBrain` reinitialised after setup while voice pipeline is running | Module-level `groq_brain` replaced | The lock in T1 ensures the old brain finishes its current call before the reference is replaced |
| PyWebView HUD and FastAPI both need to be "the main thing" | PyWebView requires the main thread | FastAPI runs in daemon thread — PyWebView stays on main thread. No conflict if T2 is correct |
| Uvicorn's asyncio event loop vs Python's default event loop | Python 3.10+ changed default loop policy | Set `loop="asyncio"` in `uvicorn.Config` (done in T2) |
| `config_manager` singleton read/write from 3+ threads | | `config_manager._lock` already handles this — no new changes needed |
| `db_singleton` accessed from API + voice + reminder threads | | `check_same_thread=False` + WAL mode needed. Add `PRAGMA journal_mode=WAL` after creating the singleton in memory_system.py |

#### Steps

**Step 1 — Enable WAL mode in SQLite**

Open `modules/memory_system.py`. After `self.conn = sqlite3.connect(...)`, add:
```python
self.conn.execute("PRAGMA journal_mode=WAL")
```
This allows concurrent reads while a write is in progress — prevents "database is locked"
errors under the multi-threaded API + voice + reminder access pattern.

**Step 2 — Run the integration test checklist**

Test each flow in order:

```
[ ] Voice command executes while API command is in-flight (concurrent test)
[ ] Setup wizard completes → voice pipeline immediately uses new user name
[ ] Setup wizard completes → coding assistant uses new Groq key immediately
[ ] Phone: send "open chrome" → Chrome opens on PC
[ ] Phone: send "weather" → response appears in app
[ ] Phone: Dashboard "Mute" button → PC audio mutes
[ ] Phone: Dashboard "Lock PC" button → PC locks
[ ] Phone: Remote tab status indicator updates when voice command is spoken
[ ] Phone: Code tab — send "write hello world in Python" → code block renders
[ ] Phone: Code tab — follow-up "make it a function" → uses previous context
[ ] Web: open http://[pc-ip]:8000 → web app loads
[ ] Web: all above flows work in browser
[ ] Restart PC app → phone app reconnects automatically (WebSocket reconnect logic)
[ ] Send command before setup → gets helpful error, not a crash
```

**Step 3 — Add WebSocket auto-reconnect to the app**

The phone's WebSocket connection to `/ws/status` will disconnect if the PC restarts.
Add reconnect logic to the Remote screen:

```javascript
const connectWs = useCallback(() => {
  const ws = new WebSocket(`ws://${serverIp}:8000/ws/status`);
  ws.onclose = () => setTimeout(connectWs, 3000);   // reconnect after 3s
  ws.onmessage = (e) => { /* ... */ };
  wsRef.current = ws;
}, [serverIp]);

useEffect(() => { connectWs(); return () => wsRef.current?.close(); }, [connectWs]);
```

**Step 4 — Update `LOG.md`**

Mark all Ts complete. Write a final summary of what was built, any open issues,
and the IP/URL where the services run.

#### Verification
- [ ] All integration test checklist items pass
- [ ] No `database is locked` errors in console during concurrent usage
- [ ] WebSocket reconnects within 5 seconds of PC restart
- [ ] LOG.md shows all Ts as ✅ Done

---

## Appendix A — Cloudflare Tunnel (Remote Access Setup)

To use the app when not on home WiFi:

```bash
# Install once (Windows)
winget install --id Cloudflare.cloudflared

# Start tunnel (run this after NOVA starts)
cloudflared tunnel --url http://localhost:8000
```

This prints a public URL like `https://xyz-random.trycloudflare.com`.
Enter this URL in the app's Connect screen instead of a local IP.
The tunnel is temporary (URL changes each restart). For a permanent URL, set up a named
tunnel at dash.cloudflare.com (free).

---

## Appendix B — File Reference

```
NOVA_AI/
├── main.py                  ← T2: api_thread, T3: push_status, T5: udp_broadcaster
├── nova_core.py             ← T1: _route_lock
├── nova.spec                ← T13: PyInstaller spec
├── LOG.md                   ← T0: progress tracking (update throughout)
├── EXPANSION_PLAN.md        ← this file
├── modules/
│   ├── api_server.py        ← T2,T3,T4,T5,T6,T7: entire API surface
│   └── coding_assistant.py  ← T7: coding brain
├── web/                     ← T12: Expo web build output (git-ignored)
└── nova-app/                ← T8–T12: Expo project (separate git repo recommended)
    ├── app/
    │   ├── _layout.js
    │   ├── connect.js
    │   ├── setup/
    │   └── (tabs)/
    └── src/api/client.js
```

---

## Appendix C — Quick Command Reference

```bash
# Start NOVA (development)
python main.py

# Test API
curl http://localhost:8000/api/health -H "X-API-Key: nova-secret-change-this"

# Run Expo (web)
cd nova-app && npx expo start --web

# Build Android APK
cd nova-app && eas build --platform android --profile preview

# Build web
cd nova-app && npx expo export --platform web

# Build Windows exe
pyinstaller nova.spec

# Remote access tunnel
cloudflared tunnel --url http://localhost:8000
```
