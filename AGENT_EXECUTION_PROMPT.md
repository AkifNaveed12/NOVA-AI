# NOVA AI — Hackathon Feature Execution Prompt

## For: Anti-Gravity Coding Agent

## Branch: feature/hackathon-sprint

---

## YOUR IDENTITY AND ROLE

You are a senior Python engineer executing a pre-approved implementation plan on an existing, 100% working production codebase. Your job is to ADD new features exactly as specified — nothing more, nothing less.

**The system is working. Your primary obligation is to keep it working.**

---

## MANDATORY FIRST STEPS — DO NOT SKIP

Before writing a single line of code, you MUST complete all of these:

### Step 1 — Read these files in full (every session, no exceptions):

```
IMPLEMENTATION_PLAN.md   ← primary specification for this sprint
EXPANSION_PLAN.md        ← existing architecture decisions
FEATURES_PLAN.md         ← existing feature specs
LOG.md                   ← current task progress
main.py                  ← entry point, thread architecture
nova_core.py             ← routing logic and _route_lock
modules/api_server.py    ← existing FastAPI server
modules/memory_system.py ← SQLite schema and db_singleton
modules/coding_assistant.py ← agentic pattern to follow for new agents
```

### Step 2 — Understand the system architecture before touching anything:

**Thread model (6 threads — do not add more unless IMPLEMENTATION_PLAN.md says to):**

```
main thread         → pywebview HUD (never touch from other threads)
voice_pipeline      → STT → NLP → nova_core.route() → TTS
wake_word_thread    → daemon: "Hey NOVA" detection → threading.Event
gesture_thread      → daemon: OpenCV + MediaPipe
reminder_thread     → daemon: DB poll every 30s
api_thread          → daemon: FastAPI/Uvicorn on port 8000
```

**Key rules that must not be broken:**

1. `nova_core.route()` is protected by `_route_lock` — never call it without going through nova_core
2. All HUD updates from non-main threads must use `root.after(0, fn)` pattern
3. All modules return plain strings to main.py — they do NOT call HUD or TTS directly
4. SQLite WAL mode is enabled — all writes go through db_singleton or db_manager
5. The `speak()` function in main.py is the ONLY TTS caller — modules never call pyttsx3 directly
6. API endpoints use plain `def` (NOT `async def`) because they do blocking I/O

### Step 3 — Check current LOG.md status:

Read LOG.md to see which tasks are done. Never redo a completed task. Pick up from the first incomplete task.

### Step 4 — Run the existing system:

Confirm `python main.py` starts without errors before making any changes. If it doesn't start, STOP and report the error — do not proceed.

---

## EXECUTION RULES — ABSOLUTE

### RULE 1: One task at a time

Complete and verify each task (A-T0, A-T1, A-T2...) fully before starting the next.
Never start T[N+1] until T[N]'s verification checklist passes completely.

### RULE 2: No unauthorized changes

Only modify files explicitly listed in IMPLEMENTATION_PLAN.md for the current task.

**These files are READ-ONLY unless IMPLEMENTATION_PLAN.md explicitly says to edit them:**

```
main.py                  ← only edit where A-T6 and B-T3 specify
nova_core.py             ← DO NOT TOUCH
modules/nlp_engine.py    ← DO NOT TOUCH
modules/groq_brain.py    ← DO NOT TOUCH
modules/hud_interface.py ← DO NOT TOUCH
modules/wake_word.py     ← DO NOT TOUCH
modules/stt.py           ← DO NOT TOUCH
modules/gesture_engine.py ← DO NOT TOUCH
nova_app/lib/screens/home/dashboard_tab.dart  ← DO NOT TOUCH
nova_app/lib/screens/home/remote_tab.dart     ← DO NOT TOUCH
nova_app/lib/screens/home/code_tab.dart       ← DO NOT TOUCH
nova_app/lib/screens/home/trackpad_tab.dart   ← DO NOT TOUCH
nova_app/lib/screens/home/system_tab.dart     ← DO NOT TOUCH
nova_app/lib/screens/home/files_tab.dart      ← DO NOT TOUCH
```

### RULE 3: Never change any existing function signature

If you need to extend a function, add a new function or add optional parameters with defaults.

### RULE 4: Never change any UI

No color changes. No layout changes. No widget additions to existing screens. The HUD stays exactly as it is. Only add NEW screens/tabs as specified in IMPLEMENTATION_PLAN.md.

### RULE 5: No speculative improvements

Do not refactor existing code. Do not rename variables. Do not "improve" working code. Do not add logging to existing functions. If it works, leave it alone.

### RULE 6: Additive-only changes to shared files

When IMPLEMENTATION_PLAN.md tells you to add to `api_server.py` or `memory_system.py`:

* Add the new code BELOW the last existing line of that section
* Never modify existing endpoints or functions
* New endpoints must use the same `_require_auth` dependency pattern as existing ones

### RULE 7: Every new module follows this structure

```python
"""
MODULE — [Name]
[One paragraph description]
"""
# imports
# constants / prompts
# class definition
#   __init__ with dependency injection (db, speak_func, etc.)
#   public methods
#   private helper methods
```

---

## TASK EXECUTION SEQUENCE

Execute tasks in this exact order. Do not skip. Do not reorder.

```
A-T0  → Branch + install deps + config.json additions + folder creation
A-T1  → modules/document_parser.py
A-T2  → modules/assignment_detector.py
A-T3  → modules/assignment_generator.py
A-T4  → modules/document_writer.py
A-T5  → modules/assignment_manager.py
A-T6  → modules/folder_watcher.py + surgical main.py additions
A-T7  → modules/whatsapp_scanner.py (optional, config-guarded)
A-T8  → New API endpoints in api_server.py + Flutter assignment_tab.dart
B-T0  → DB migration in memory_system.py _create_tables()
B-T1  → modules/face_auth.py
B-T2  → New API endpoints in api_server.py (face auth)
B-T3  → Surgical main.py additions for PC startup face scan
B-T4  → nova_app/lib/screens/face_login_screen.dart
```

---

## HOW TO MAKE SURGICAL ADDITIONS TO main.py

main.py has clearly marked sections. Only insert in the exact locations specified.

**For A-T6 (FolderWatcher) — insert BEFORE `wake_word.start()`:**

```python
from modules.assignment_manager import AssignmentManager
from modules.folder_watcher import FolderWatcher
assignment_manager = AssignmentManager(
    db_manager=db_manager,
    speak_func=speak,
    listen_func=lambda: stt.transcribe(stt.listen())
)
folder_watcher = FolderWatcher(
    inbox_path=config.get("assignment_pipeline", {}).get("inbox_folder", "nova_inbox"),
    assignment_manager=assignment_manager
)
folder_watcher.start()
```

In the shutdown block, find `wake_word.stop()` and add after it:

```python
folder_watcher.stop()
```

**For B-T3 (Face scan) — insert AFTER `db_manager = DatabaseManager()` and BEFORE `hud = NOVAHud()`:**

```python
from modules.face_auth import FaceAuth as _FaceAuth
_face_cfg = config.get("face_login", {})
if _face_cfg.get("enabled", False):
    _face_module = _FaceAuth(db_manager, camera_index=_face_cfg.get("camera_index", 0))
    _user_name = config.get("user", {}).get("name", "User")
    if _face_module.is_registered(_user_name):
        print("[FaceLogin] Scanning for registered face...")
        _auth_result = _face_module.verify_from_webcam(_user_name)
        if _auth_result.get("authenticated"):
            print(f"[FaceLogin] Welcome back, {_user_name}! (similarity: {_auth_result.get('similarity')})")
        else:
            print("[FaceLogin] Face not recognized. Continuing with standard startup.")
    else:
        print("[FaceLogin] No face registered. Use voice: 'Register my face'")
```

---

## HOW TO ADD TO memory_system.py (B-T0)

Find the `_create_tables()` method. Scroll to the LAST `self.conn.execute("""CREATE TABLE IF NOT EXISTS` block. Add AFTER it, before the method ends:

```python
        # ── Hackathon Feature Tables ──────────────────────────────
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS face_identities (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name   TEXT NOT NULL,
                embedding   BLOB NOT NULL,
                model       TEXT DEFAULT 'Facenet',
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS face_sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                token       TEXT NOT NULL,
                user_name   TEXT NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at  TIMESTAMP NOT NULL
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                source          TEXT,
                raw_text        TEXT,
                subject         TEXT,
                title           TEXT,
                deadline        TEXT,
                output_format   TEXT,
                output_path     TEXT,
                status          TEXT DEFAULT 'pending',
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
```

Do NOT change any other part of `_create_tables()`.

---

## HOW TO ADD TO api_server.py (A-T8 and B-T2)

Scroll to the absolute bottom of `api_server.py`. Add new endpoint sections AFTER everything existing.

Pattern every new endpoint must follow:

```python
# ── [Feature Name] Endpoints ─────────────────────────────────────

class SomeRequestModel(BaseModel):
    field: str

@app.get("/api/new/endpoint")
def new_endpoint(_auth: str = Depends(_require_auth)):
    from modules.some_module import SomeClass   # ← always import inside function
    try:
        ...
        return {"status": "success", ...}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

The `/api/auth/face/verify` endpoint is the ONE exception — it does NOT have `_auth` because it IS the authentication. See IMPLEMENTATION_PLAN.md B-T2 for its exact signature.

---

## DEPENDENCY INSTALLATION GUIDE (A-T0)

### Tesseract binary — MUST be installed manually (cannot pip install):

```
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
   File: tesseract-ocr-w64-setup-5.x.x.exe
2. Install → default path: C:\Program Files\Tesseract-OCR\
3. Add to Windows PATH:
   System Properties → Environment Variables → System Variables → Path → New:
   C:\Program Files\Tesseract-OCR\
4. Open NEW terminal and verify: tesseract --version
```

### pip install (run in this order):

```bash
pip install watchdog==4.0.1
pip install PyMuPDF==1.24.3
pip install python-docx==1.1.2
pip install pytesseract==0.3.10
pip install fpdf2==2.7.9
pip install reportlab==4.2.0
pip install beautifulsoup4==4.12.3
pip install langdetect==1.0.9
pip install deepface==0.0.93
pip install tf-keras==2.16.0
```

### Pre-download Facenet model (REQUIRED before running any face feature):

```bash
python -c "from deepface import DeepFace; DeepFace.build_model('Facenet'); print('Facenet model ready.')"
```

Downloads ~90MB once to `~/.deepface/weights/`. Fully offline after this.

### Add to requirements.txt (append at the bottom, do not change existing entries):

```
# Hackathon Sprint — Feature A + B
watchdog==4.0.1
PyMuPDF==1.24.3
python-docx==1.1.2
pytesseract==0.3.10
fpdf2==2.7.9
reportlab==4.2.0
beautifulsoup4==4.12.3
langdetect==1.0.9
deepface==0.0.93
tf-keras==2.16.0
```

---

## CRITICAL GOTCHAS — READ ALL OF THESE

### Gotcha 1: DeepFace import is slow (2-4 seconds, TensorFlow init)

NEVER import at module top level. Always lazy-import inside the function body:

```python
# WRONG — slows entire NOVA startup
from deepface import DeepFace

# CORRECT — only loads when face feature is actually used
def _get_embedding(self, frame):
    from deepface import DeepFace
    result = DeepFace.represent(...)
```

### Gotcha 2: Tesseract path on Windows

Add this block at the top of document_parser.py, AFTER all imports, BEFORE the class:

```python
import pytesseract as _pytesseract_cfg
import os as _os_cfg
if _os_cfg.name == 'nt':
    _tess = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if _os_cfg.path.exists(_tess):
        _pytesseract_cfg.pytesseract.tesseract_cmd = _tess
```

### Gotcha 3: python-docx import name mismatch

* requirements.txt entry: `python-docx==1.1.2`
* Python import: `import docx` (NOT `import python_docx`)
* When reading: `doc = docx.Document(path)`
* When writing: `doc = docx.Document()` then `doc.save(path)`

### Gotcha 4: fpdf2 import

* requirements.txt entry: `fpdf2==2.7.9`
* Python import: `from fpdf import FPDF`
* Do NOT install the old `fpdf` package — only `fpdf2`

### Gotcha 5: DeepFace.represent() with numpy array vs file path

```python
# For numpy arrays from OpenCV (our use case):
DeepFace.represent(
    img_path=frame,              # numpy ndarray, BGR format from cv2
    model_name="Facenet",
    enforce_detection=True,
    detector_backend="opencv"    # opencv backend is CPU-only and stable
)
```

### Gotcha 6: FolderWatcher fires on_created twice on Windows

The `_processed: set` in FolderWatcher deduplicates this. Do NOT remove it. This is by design.

### Gotcha 7: speak() is thread-safe but blocks

When AssignmentManager calls speak_func (which is main.py's `speak()`), it blocks until speech finishes. This is correct behavior — the pipeline waits while speaking. Don't wrap it in threading.

### Gotcha 8: Groq model name

Always use `llama-3.3-70b-versatile`. Never use `llama3-70b-8192` (decommissioned).

### Gotcha 9: SQLite row_factory

Check if `memory_system.py` sets `self.conn.row_factory = sqlite3.Row`. If it does, you can access rows as `row["column_name"]`. If it doesn't, use `row[0]`, `row[1]` etc. Do not change the row_factory setting.

### Gotcha 10: fpdf2 Unicode (for Urdu/Arabic text in assignments)

If you detect non-ASCII text in an assignment, the default FPDF font will fail. Add this fallback to document_writer.py's `_write_pdf`:

```python
# Check for non-ASCII content
if any(ord(c) > 127 for c in content[:100]):
    # Fall back to DOCX for non-Latin content
    return self._write_docx(title, content, filename_base)
```

### Gotcha 11: Assignment folder creation timing

`nova_inbox/` and `nova_outbox/` must be created BEFORE FolderWatcher starts. Create them in A-T0 by adding to the startup block in main.py (find `os.makedirs("data", exist_ok=True)` if it exists, add nearby). Or create them in FolderWatcher. **init** .

### Gotcha 12: deepface vs face_recognition library

Use ONLY `deepface`. Do NOT use the `face_recognition` library — it requires dlib which requires CMake + Visual Studio Build Tools on Windows and will fail installation.

---

## VERIFICATION CHECKLIST (run after EVERY task)

```bash
# Check 1: System still starts (MUST PASS before any new task)
python main.py
# Expected: HUD opens, "NOVA AI — Ready" printed, no ImportError, no crash in 10s
# Then close the window

# Check 2: API still online
curl http://localhost:8000/api/health -H "X-API-Key: nova-secret-change-this"
# Expected: {"status":"online","service":"NOVA API"}

# Check 3: Voice pipeline works
# Say "Hey NOVA, what time is it" → TTS responds with current time

# Check 4: Task-specific verification
# Run each item from the verification checklist in IMPLEMENTATION_PLAN.md for that task
```

**If Check 1 OR Check 2 fail after your changes:**

1. STOP immediately
2. `git diff` to see what changed
3. Revert the breaking change
4. Rerun checks 1 and 2
5. Report the failure before proceeding

---

## LOG.md UPDATE PROTOCOL

After completing each task:

1. Change task status from `🔄 Active` to `✅ Done` with today's date
2. Change next task from `⬜ Todo` to `🔄 Active`
3. Update `Active T:` in the Current Status block
4. Add any issues to the Issues Log table at the bottom

---

## GIT COMMIT PROTOCOL

After each task is verified and LOG.md is updated:

```bash
git add .
git commit -m "feat(assignment-pipeline): A-T1 — document_parser.py, PDF/DOCX/image/URL"
# Format: feat(feature-name): T-code — filename, what it does
```

Examples:

```
feat(assignment-pipeline): A-T0 — deps, config.json, nova_inbox/outbox folders
feat(assignment-pipeline): A-T1 — document_parser.py, supports PDF/DOCX/img/URL
feat(assignment-pipeline): A-T2 — assignment_detector.py, Groq metadata extraction
feat(assignment-pipeline): A-T3 — assignment_generator.py, agentic Groq writer
feat(assignment-pipeline): A-T4 — document_writer.py, PDF+DOCX output
feat(assignment-pipeline): A-T5 — assignment_manager.py, pipeline orchestrator
feat(assignment-pipeline): A-T6 — folder_watcher.py + main.py surgical integration
feat(assignment-pipeline): A-T7 — whatsapp_scanner.py, optional selenium scanner
feat(assignment-pipeline): A-T8 — API endpoints + Flutter assignment_tab.dart
feat(face-login): B-T0 — memory_system.py DB migration, 3 new tables
feat(face-login): B-T1 — face_auth.py, deepface Facenet, SQLite BLOB, sessions
feat(face-login): B-T2 — api_server.py face auth endpoints
feat(face-login): B-T3 — main.py startup face scan integration
feat(face-login): B-T4 — Flutter face_login_screen.dart
```

Branch: `feature/hackathon-sprint`
Never push to `main` or `akif/week4-dev` directly.

---

## DEFINITION OF DONE

### Feature A is complete when ALL of these are true:

* [ ] Drop any PDF/DOCX/image in `nova_inbox/` → NOVA speaks detection within 3 seconds
* [ ] Say "yes" to confirmation → assignment appears in `nova_outbox/` as PDF or DOCX
* [ ] Output file has proper title heading, body paragraphs, and is readable
* [ ] `GET /api/assignment/download/{id}` returns the file from browser/Postman
* [ ] Flutter app has Assignment tab with upload button, status list, download button
* [ ] Existing voice commands still work unchanged
* [ ] No errors in console during the full flow

### Feature B is complete when ALL of these are true:

* [ ] `python main.py` → webcam scan runs → registered face welcomed in console
* [ ] Flutter app: opens → camera shows → face recognized → home screen opens (no manual IP entry)
* [ ] 3 failed face attempts → API key input shown as fallback
* [ ] Session token stored in Flutter → next app open skips camera until token expires
* [ ] Wrong face returns `authenticated: false` (test with a photo or different person)
* [ ] All existing app flows (dashboard, remote, code) work unchanged after face login

---

## FINAL REMINDER

The codebase is stable. 25 modules are working. A Flutter app is working. An API server is running. A voice pipeline is running.

Your job is surgical addition. Read the plan. Follow it exactly. Test after every task. If anything breaks, revert before moving forward.

Start with A-T0. Read IMPLEMENTATION_PLAN.md first.
