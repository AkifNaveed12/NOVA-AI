# NOVA App — Feature Expansion Plan
**Voice · System Info · Coding Agent · File Browser · Utilities**
*Continues from EXPANSION_PLAN.md — tasks labeled F1–F9*

---

## How to Use This Document
Same rules as EXPANSION_PLAN.md:
- Each F-task is self-contained with steps, files, and a verification checklist
- Never start F[N+1] until F[N] verification is green
- Log progress in LOG.md under the active F task

---

## Priority Order

| F | Feature | Impact | Effort |
|---|---------|--------|--------|
| F1 | Voice assistant in app | ⭐⭐⭐⭐⭐ | Low |
| F2 | System info dashboard | ⭐⭐⭐⭐ | Medium |
| F3 | Coding agent (read/write/run on PC) | ⭐⭐⭐⭐⭐ | High |
| F4 | File browser | ⭐⭐⭐⭐ | High |
| F5 | Screenshot viewer | ⭐⭐⭐ | Low |
| F6 | Clipboard sync | ⭐⭐⭐ | Low |
| F7 | Notes & Tasks viewer | ⭐⭐⭐ | Medium |
| F8 | Search shortcuts (YouTube/Google) | ⭐⭐ | Low |
| F9 | Activity log viewer | ⭐⭐ | Low |

---

## F1 — Voice Assistant in App
**Goal:** Phone mic → transcribe on-device → send to NOVA PC pipeline.
The app becomes a full voice remote, not just text.
**Depends on:** Nothing (uses existing /api/command)
**Effort:** 4 hours

### What changes
- `pubspec.yaml` — add `speech_to_text: ^6.6.2`
- `AndroidManifest.xml` — add RECORD_AUDIO permission
- `remote_tab.dart` — add mic FAB button with push-to-talk

### Steps

**Step 1 — pubspec.yaml**
Add under dependencies:
```yaml
speech_to_text: ^6.6.2
```

**Step 2 — AndroidManifest.xml**
Add inside `<manifest>`:
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO"/>
```

**Step 3 — Remote tab mic button**
- Replace the send button with two modes: text input + mic FAB
- Mic button: hold to record, release to send
- Show waveform animation while recording
- On result: populate text field and auto-send
- Show "Listening..." indicator while recording

### Verification
- [ ] Mic permission prompt appears on first use
- [ ] Hold mic button → recording indicator appears
- [ ] Release → text appears in field → auto-sends to NOVA
- [ ] NOVA's response appears in chat
- [ ] Voice and text input both work independently

---

## F2 — System Info Dashboard
**Goal:** Live PC stats visible from phone — CPU, RAM, disk, battery, network, uptime.
**Depends on:** F1 (or can be done independently)
**Effort:** 1 day

### Backend: new endpoint in api_server.py

```python
@app.get("/api/system/info")
def system_info(_auth: str = Depends(_require_auth)):
    import psutil, time, datetime
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')
    net = psutil.net_io_counters()
    battery = psutil.sensors_battery()
    boot_time = psutil.boot_time()
    uptime_sec = int(time.time() - boot_time)
    uptime_str = str(datetime.timedelta(seconds=uptime_sec))
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
```

### Flutter: System tab or section in Dashboard
- New tab "System" in bottom nav (4 tabs total)
- Polls every 5 seconds
- Circular progress gauges for CPU/RAM/Disk
- Battery bar with charging icon
- Network sent/received counters
- Uptime display

### Verification
- [ ] `GET /api/system/info` returns correct stats
- [ ] App shows live updating values
- [ ] Disk/RAM/CPU gauges update every 5 seconds
- [ ] Battery shows charging state correctly

---

## F3 — Coding Agent (Read · Write · Run on PC)
**Goal:** The coding assistant can read your PC files, write/create files, run terminal
commands, and fix bugs — all from your phone. Becomes a mobile Claude Code.
**Depends on:** Existing coding assistant (T7/T11)
**Effort:** 2 days

### Architecture

```
Phone (Code Tab)
  │  "Read main.py and find the bug"
  ▼
api/files/read?path=...   ──► reads file, injects content into chat
  │
  ▼
CodingAssistant.chat(file_content + user_message)
  │  "Found bug on line 42. Here's the fix:"
  ▼
api/files/write           ──► writes fixed file back to PC
  │
  ▼
api/terminal/run          ──► runs "python main.py" to test it
  │  stdout/stderr
  ▼
App shows output
```

### Backend endpoints to add in api_server.py

#### File operations
```python
import os, subprocess
from pathlib import Path

# Configurable safe roots — only these directories are accessible
SAFE_ROOTS = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.cwd(),  # NOVA_AI project root
]

def _is_safe_path(path: str) -> bool:
    """Prevent path traversal attacks — only allow paths under SAFE_ROOTS."""
    try:
        p = Path(path).resolve()
        return any(p == root or root in p.parents for root in
                   [r.resolve() for r in SAFE_ROOTS])
    except Exception:
        return False

class FileWriteRequest(BaseModel):
    path: str
    content: str
    create_dirs: bool = True

class MkdirRequest(BaseModel):
    path: str

class TerminalRequest(BaseModel):
    command: str
    cwd: str = ""
    timeout: int = 30

@app.get("/api/files/list")
def list_files(path: str = "", _auth: str = Depends(_require_auth)):
    if not path:
        # Return safe roots as top-level
        roots = []
        for r in SAFE_ROOTS:
            if r.exists():
                roots.append({
                    "name": r.name, "path": str(r),
                    "type": "directory", "size": None
                })
        return {"entries": roots, "path": ""}

    if not _is_safe_path(path):
        raise HTTPException(403, "Path outside allowed directories.")
    p = Path(path)
    if not p.exists():
        raise HTTPException(404, "Path not found.")
    if not p.is_dir():
        raise HTTPException(400, "Not a directory.")

    entries = []
    for item in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
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

    TEXT_EXTENSIONS = {
        '.py', '.js', '.ts', '.dart', '.java', '.c', '.cpp', '.h',
        '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt',
        '.html', '.css', '.scss', '.xml', '.json', '.yaml', '.yml',
        '.toml', '.ini', '.cfg', '.env', '.txt', '.md', '.csv',
        '.sh', '.bat', '.ps1', '.sql', '.r',
    }
    if p.suffix.lower() not in TEXT_EXTENSIONS:
        raise HTTPException(400, f"File type {p.suffix} is not a readable text file.")
    if p.stat().st_size > 500_000:  # 500KB limit
        raise HTTPException(400, "File too large to read (max 500KB).")

    try:
        content = p.read_text(encoding='utf-8', errors='replace')
        return {"path": str(p), "content": content, "lines": content.count('\n') + 1}
    except Exception as e:
        raise HTTPException(500, f"Read error: {e}")

@app.post("/api/files/write")
def write_file(req: FileWriteRequest, _auth: str = Depends(_require_auth)):
    if not _is_safe_path(req.path):
        raise HTTPException(403, "Path outside allowed directories.")
    p = Path(req.path)
    if req.create_dirs:
        p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(req.content, encoding='utf-8')
        return {"status": "success", "path": str(p), "bytes": len(req.content.encode())}
    except Exception as e:
        raise HTTPException(500, f"Write error: {e}")

@app.post("/api/files/mkdir")
def make_dir(req: MkdirRequest, _auth: str = Depends(_require_auth)):
    if not _is_safe_path(req.path):
        raise HTTPException(403, "Path outside allowed directories.")
    Path(req.path).mkdir(parents=True, exist_ok=True)
    return {"status": "success", "path": req.path}

@app.post("/api/terminal/run")
def run_terminal(req: TerminalRequest, _auth: str = Depends(_require_auth)):
    """
    Execute a shell command on the PC and return stdout/stderr.
    SECURITY: Only allow whitelisted commands or restrict to safe operations.
    Blocked: rm -rf, del /s, format, net user, reg delete, shutdown (use voice for these).
    """
    BLOCKED = ['rm -rf', 'del /s', 'del /f', 'format ', 'mklink',
               'net user', 'reg delete', 'reg add', ':(){', 'shutdown',
               'taskkill /f']
    cmd_lower = req.command.lower()
    if any(b in cmd_lower for b in BLOCKED):
        return {"status": "blocked",
                "stdout": "", "stderr": "Command blocked for safety.",
                "return_code": -1}

    cwd = req.cwd if req.cwd and _is_safe_path(req.cwd) else str(Path.cwd())
    try:
        result = subprocess.run(
            req.command, shell=True, capture_output=True,
            text=True, timeout=req.timeout, cwd=cwd
        )
        return {
            "status": "success",
            "stdout": result.stdout[-8000:],   # cap at 8KB
            "stderr": result.stderr[-2000:],
            "return_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "stdout": "", "stderr": "Command timed out.", "return_code": -1}
    except Exception as e:
        return {"status": "error", "stdout": "", "stderr": str(e), "return_code": -1}
```

### Flutter: Coding assistant upgrades

**New features in Code tab:**
1. **File picker panel** — drawer on left shows file browser
   - Tap a file → reads it → injects content as context into the chat
   - Shows `[context: main.py (247 lines)]` pill in the chat
2. **"Apply to file" action** — when AI responds with a code block, a
   "Save to PC" button appears → user picks path → file is written
3. **Terminal panel** — bottom drawer
   - Input field to type commands
   - Shows output with colored stdout/stderr
   - Quick buttons: `python [file]`, `pip install`, `dir`, `cd`
4. **Inline file diff** — when AI rewrites a file, show old vs new
   side by side before applying

### Verification
- [ ] `GET /api/files/list` returns correct directory listing
- [ ] `GET /api/files/read?path=...` returns file content
- [ ] `POST /api/files/write` creates/overwrites a file correctly
- [ ] `POST /api/terminal/run` returns stdout for `echo hello`
- [ ] Blocked commands return `status: blocked`, not an error
- [ ] Path traversal attempt (../../etc/passwd) returns 403
- [ ] App: attaching a file shows its content as context in chat
- [ ] App: "Save to PC" saves AI's code to the specified path
- [ ] App: terminal panel runs `dir` and shows output

---

## F4 — File Browser Tab
**Goal:** Standalone file browser tab — navigate PC folders, preview files,
open on PC, and pass files to the coding assistant.
**Depends on:** F3 (file API endpoints)
**Effort:** 1.5 days

### Flutter: new "Files" tab (5th tab)
- Breadcrumb navigation bar showing current path
- List view: folders first, then files with icons by extension
- Tap folder → navigate in
- Tap file → options sheet: Preview / Open on PC / Send to Coding Assistant
- Preview: text files shown inline, images rendered, others show metadata
- Search bar: filter files by name in current directory
- Long press → select multiple → open all on PC

### File type icons
```
📁 folder       🐍 .py      ⚡ .js/.ts     🎯 .dart
📄 .txt/.md     🔧 .json    📊 .csv        🖼 .png/.jpg
🎵 .mp3         🎬 .mp4     📦 .zip        ⚙ .exe/.bat
```

### Verification
- [ ] App opens file browser showing Desktop/Documents/Downloads/NOVA_AI
- [ ] Navigate into a folder, breadcrumb updates
- [ ] Tap .py file → preview shows code with monospace font
- [ ] "Open on PC" option triggers the file to open on PC
- [ ] "Send to Assistant" passes file content to code tab

---

## F5 — Screenshot Viewer
**Goal:** After "take screenshot" command, see the screenshot in the app.
**Depends on:** Nothing new
**Effort:** 3 hours

### Backend
```python
@app.get("/api/screenshot/latest")
def get_latest_screenshot(_auth: str = Depends(_require_auth)):
    from fastapi.responses import FileResponse
    screenshots_dir = Path("data/screenshots")
    if not screenshots_dir.exists():
        raise HTTPException(404, "No screenshots taken yet.")
    files = sorted(screenshots_dir.glob("*.png"), key=lambda f: f.stat().st_mtime)
    if not files:
        raise HTTPException(404, "No screenshots found.")
    return FileResponse(str(files[-1]), media_type="image/png")
```

Update `modules/screenshot_tools.py` to save to `data/screenshots/` with timestamp filename.

### Flutter
- After sending "take screenshot" command in Remote tab, response includes a
  "View Screenshot" button
- Tapping it loads `/api/screenshot/latest` as a full-screen image
- Pinch to zoom

### Verification
- [ ] Screenshot saves to `data/screenshots/` with timestamp name
- [ ] `GET /api/screenshot/latest` returns the image
- [ ] App displays full-screen preview

---

## F6 — Clipboard Sync
**Goal:** Read and write PC clipboard from the app.
**Depends on:** Nothing
**Effort:** 2 hours

### Backend
```python
@app.get("/api/clipboard")
def clipboard_get(_auth: str = Depends(_require_auth)):
    import pyperclip
    return {"content": pyperclip.paste()}

class ClipboardSetRequest(BaseModel):
    content: str

@app.post("/api/clipboard")
def clipboard_set(req: ClipboardSetRequest, _auth: str = Depends(_require_auth)):
    import pyperclip
    pyperclip.copy(req.content)
    return {"status": "success"}
```

### Flutter
- "Clipboard" card on Dashboard
- Shows last 60 chars of PC clipboard
- "Copy to Phone" button → copies to phone clipboard
- "Send to PC" button → phone sends its clipboard to PC
- Auto-refreshes every 10s

### Verification
- [ ] `GET /api/clipboard` returns current PC clipboard content
- [ ] `POST /api/clipboard` updates PC clipboard
- [ ] App shows PC clipboard and allows two-way sync

---

## F7 — Notes & Tasks Viewer
**Goal:** View, add, and complete notes and tasks from the app.
**Depends on:** Nothing (uses existing DB)
**Effort:** 1 day

### Backend
```python
@app.get("/api/notes")
def get_notes(_auth = Depends(_require_auth)):
    from modules.notes_reminders import NotesModule
    nm = NotesModule()
    # Return structured list
    ...

@app.post("/api/notes")
def add_note(req: NoteRequest, _auth = Depends(_require_auth)):
    ...

@app.get("/api/tasks")
def get_tasks(_auth = Depends(_require_auth)):
    from modules.calendar_tasks import TasksModule
    ...

@app.post("/api/tasks")
def add_task(req: TaskRequest, _auth = Depends(_require_auth)):
    ...

@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, req: TaskUpdateRequest, _auth = Depends(_require_auth)):
    ...
```

### Flutter
- New "Notes" tab or section inside Dashboard
- Tabs inside: Notes | Tasks
- Notes: list + add new note (floating button)
- Tasks: checklist with priority colors (high=red, medium=yellow, low=green)
- Swipe left → delete, swipe right → mark done

### Verification
- [ ] Notes list loads from PC database
- [ ] Adding a note from app creates it on PC (verify via voice: "read my notes")
- [ ] Marking task done updates PC database

---

## F8 — Search Shortcuts
**Goal:** Quick search bar on Dashboard for YouTube/Google/Wikipedia.
**Depends on:** Nothing (existing /api/command)
**Effort:** 2 hours

### Flutter only — no backend changes
- Add a search bar at the top of Dashboard
- Dropdown pill to select: YouTube | Google | Wikipedia
- On search: sends `"search [query] on [platform]"` to `/api/command`
- Shows confirmation response

### Verification
- [ ] Typing "cristiano ronaldo" + YouTube → PC opens YouTube search
- [ ] Typing "python tutorial" + Google → PC opens Google search

---

## F9 — Activity Log Viewer
**Goal:** See what NOVA did — full command history with timestamps.
**Depends on:** Nothing (uses existing activity_log table)
**Effort:** 2 hours

### Backend
```python
@app.get("/api/activity")
def get_activity(limit: int = 50, _auth = Depends(_require_auth)):
    from modules.activity_log import ActivityLogger
    from modules.memory_system import db_singleton
    logger = ActivityLogger(db_singleton)
    logs = logger.get_recent(limit)
    return {"logs": logs}
```

### Flutter
- New "History" section in Dashboard (expandable)
- Timeline view: time → command → module triggered → response snippet
- Color-coded by module: green=system, blue=web, purple=groq, etc.
- Pull to refresh

### Verification
- [ ] `GET /api/activity?limit=10` returns last 10 commands
- [ ] App shows timeline with correct timestamps

---

## Implementation Order

```
F1 (Voice)          ← Start here — no dependencies, huge impact
F2 (System Info)    ← Backend + UI, independent
F3 (Coding Agent)   ← Backend endpoints + Code tab upgrades
F4 (File Browser)   ← Depends on F3 file endpoints
F5 (Screenshot)     ← Quick win
F6 (Clipboard)      ← Quick win
F8 (Search)         ← Trivial
F9 (Activity Log)   ← Quick win
F7 (Notes/Tasks)    ← Last (needs DB schema investigation)
```

---

## Files to Modify

| File | Tasks |
|------|-------|
| `modules/api_server.py` | F2, F3, F5, F6, F7, F9 — new endpoints |
| `modules/screenshot_tools.py` | F5 — save to data/screenshots/ |
| `nova_app/pubspec.yaml` | F1 — speech_to_text |
| `nova_app/android/.../AndroidManifest.xml` | F1 — RECORD_AUDIO |
| `nova_app/lib/screens/home/remote_tab.dart` | F1 — mic button |
| `nova_app/lib/screens/home/dashboard_tab.dart` | F2, F6, F8, F9 |
| `nova_app/lib/screens/home/code_tab.dart` | F3 — file picker, terminal |
| `nova_app/lib/screens/home/main_screen.dart` | F2, F4 — new tabs |
| `nova_app/lib/screens/home/system_tab.dart` | F2 — new file |
| `nova_app/lib/screens/home/files_tab.dart` | F4 — new file |
| `nova_app/lib/api/client.dart` | F2,F3,F4,F5,F6,F7,F9 — new methods |
