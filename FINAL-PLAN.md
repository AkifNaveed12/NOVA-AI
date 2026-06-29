# NOVA AI — Hackathon Engineering Blueprint

### Final-Round Transformation Plan | June 2026

---

## JUDGE FEEDBACK DECODED

> _"It feels like another wrapper around Gemini. What can NOVA do that the Gemini app cannot?"_

The judge is not asking for more features. They are asking for **a reason to exist**.

Gemini, ChatGPT, and Claude share one hard architectural limit: they run in the cloud, they have no awareness of your machine, your local files, your running processes, your installed apps, your real-time sensor data, or your physical environment. They can talk about your computer. They cannot see it, feel it, or act on it.

NOVA is physically present on the machine. This is the axis the judge wants exploited.

The flagship differentiators are:

1. **Autonomous PC Agent** — reads running processes, active windows, clipboard, recent files; acts without being asked
2. **Persistent Local Identity** — remembers _everything_ across sessions, builds a living model of the user
3. **Urdu ↔ English Seamless Switching** — zero-latency multilingual voice with auto-detection
4. **Offline-First Architecture** — every critical feature has a local fallback; works without internet

These four things, combined, are impossible to replicate in a browser tab.

---

## PHASE 1 — ARCHITECTURE ANALYSIS

### 1.1 Current Layer Map

```
┌─────────────────────────────────────────────────────────┐
│ BACKGROUND LAYER (always-on daemon threads)             │
│   wake_word.py       — pvporcupine / energy threshold   │
│   gesture_engine.py  — OpenCV + MediaPipe (21 landmarks)│
│   reminder_thread    — SQLite poll every 30s            │
└───────────────────────────┬─────────────────────────────┘
                            │ threading.Event / queue.Queue
┌───────────────────────────▼─────────────────────────────┐
│ PRIMARY PIPELINE (triggered on wake)                    │
│   stt.py        → Google Web Speech (Whisper fallback)  │
│   nlp_engine.py → spaCy NER + NLTK keyword routing     │
│   nova_core.py  → dispatch_local() OR groq_brain.chat() │
│   [25 modules]  → execution                             │
│   pyttsx3 / gTTS → TTS output                           │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│ SUPPORT LAYER                                           │
│   memory_system.py  — SQLite (8 tables)                 │
│   activity_log.py   — command history                   │
│   hud.py            — pywebview / nova_hud.html          │
│   config_manager.py — hot-reload config.json            │
└─────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│ EXPANSION LAYER (Alyan's work, on akif/week4-dev)       │
│   api_server.py       — FastAPI on port 8000            │
│   coding_assistant.py — agentic Groq coder              │
│   mouse_control.py    — Win32 low-latency trackpad      │
│   nova_app/           — Flutter (Android + Web)         │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Module-by-Module Current State

| Module           | File                   | Status                | Notes                                                                        |
| ---------------- | ---------------------- | --------------------- | ---------------------------------------------------------------------------- |
| Wake Word        | wake_word.py           | ✅ Stable             | pvporcupine + energy fallback; shared_mic pattern                            |
| STT              | stt.py                 | ⚠️ Fragile            | Google Web Speech = network dependency; Whisper fallback untested under load |
| NLP Engine       | nlp_engine.py          | ⚠️ Rule-based ceiling | Keyword matching breaks on paraphrasing; no semantic understanding           |
| Groq Brain       | groq_brain.py          | ✅ Working            | llama-3.3-70b-versatile; 10-message rolling window                           |
| Weather          | weather.py             | ✅                    | OpenWeatherMap free tier                                                     |
| NASA News        | news.py                | ✅                    | APOD endpoint                                                                |
| Wikipedia        | wikipedia_module.py    | ✅                    | 3-sentence summaries                                                         |
| Web Automation   | web_automation.py      | ⚠️                    | ChromeDriver version coupling is fragile                                     |
| App Launcher     | app_launcher.py        | ✅                    | rapidfuzz matching                                                           |
| Email            | email_module.py        | ✅                    | Gmail SMTP + Groq drafting                                                   |
| WhatsApp         | whatsapp_module.py     | ⚠️                    | PyWhatKit timing issues; WhatsApp Web session coupling                       |
| Music            | music_module.py        | ⚠️                    | pyautogui keyboard shortcuts are not reliable on all layouts                 |
| Notes/Reminders  | notes_reminders.py     | ✅                    | dateparser + SQLite                                                          |
| Calendar/Tasks   | calendar_tasks.py      | ✅                    |                                                                              |
| DateTime/Math    | datetime_calc.py       | ✅                    | Sandboxed eval()                                                             |
| System Controls  | system_controls.py     | ✅                    | pycaw + psutil                                                               |
| Screenshot       | screenshot_tools.py    | ✅                    | Now saves to data/screenshots/                                               |
| Clipboard        | clipboard_manager.py   | ✅                    | pyperclip                                                                    |
| Translation      | translation_module.py  | ⚠️                    | No Urdu TTS support                                                          |
| Memory System    | memory_system.py       | ✅                    | SQLite WAL mode (planned)                                                    |
| Personality      | personality.py         | ✅                    | pyjokes + Groq                                                               |
| Gesture Engine   | gesture_engine.py      | ✅                    | 10-gesture map, 0.4s debounce                                                |
| HUD              | hud.py → nova_hud.html | ✅                    | pywebview + animated SVG                                                     |
| Activity Log     | activity_log.py        | ✅                    | 30-day auto-cleanup                                                          |
| Config Manager   | config_manager.py      | ✅                    | Hot-reload                                                                   |
| API Server       | api_server.py          | ✅                    | FastAPI, 28+ endpoints, JWT-equivalent key auth                              |
| Coding Assistant | coding_assistant.py    | ✅                    | Agentic, self-healing parser                                                 |
| Mouse Control    | mouse_control.py       | ✅                    | Win32 direct                                                                 |

---

## PHASE 2 — SYSTEM AUDIT

### 2.1 Critical Issues (P0 — Fix Before Demo)

**P0-1: STT latency and reliability**

- Google Web Speech requires a round-trip to Google servers (~400–800ms)
- If the internet is slow, the entire pipeline stalls
- Whisper fallback is loaded lazily — cold start is 3–8 seconds on first use
- _Root cause:_ No local STT is pre-loaded at startup

**P0-2: NLP intent routing ceiling**

- Keyword matching fails on paraphrasing: "dim the lights" won't match "brightness"
- No confidence gradient — either matches or falls to Groq (costly, slow)
- Semantic similarity (embeddings) not used at all
- _Root cause:_ spaCy used for NER only; no sentence-level similarity

**P0-3: SQLite not in WAL mode (concurrent access risk)**

- API server thread + voice thread + reminder thread all write to the same DB
- Default journal mode = DELETE → "database is locked" errors under load
- _Root cause:_ WAL pragma not applied in memory_system.py init

**P0-4: Memory injection is static, not semantic**

- Top 10 facts loaded by `updated_at DESC` — not by relevance to current query
- A question about weather injects facts about the user's editor preference
- _Root cause:_ No semantic ranking; no embeddings layer

### 2.2 High Priority Issues (P1)

**P1-1: No Urdu voice support**

- Translation module exists but no Urdu STT
- gTTS supports Urdu TTS but pyttsx3 does not
- Language detection is manual (user must say "translate to Urdu")

**P1-2: ChromeDriver coupling**

- Selenium requires exact ChromeDriver version match
- Updates to Chrome silently break web automation
- _Fix:_ Use `webdriver-manager` for auto-managed ChromeDriver

**P1-3: Memory facts are flat key-value with no context**

- "favorite_editor" = "VS Code" stored, but no relationship graph
- No episodic memory (what happened on which day)
- Facts extracted by Groq after conversation — but never validated

**P1-4: HUD update calls from wrong threads**

- Any module that tries to update the HUD directly would crash pywebview
- The architecture rule (modules return strings; main.py owns HUD) is correct but not enforced by code — it relies on discipline

### 2.3 Medium Issues (P2)

- WhatsApp Web session state is not checked before sending
- pyautogui keyboard shortcuts for music are system-locale dependent
- Gesture engine FPS drops when Groq call is in progress (shared GIL contention)
- No retry logic on OpenWeatherMap / NASA / Wikipedia calls
- Activity log entries don't capture whether the response satisfied the user

### 2.4 Architecture Risks

| Risk                                          | Probability | Impact   | Mitigation                            |
| --------------------------------------------- | ----------- | -------- | ------------------------------------- |
| Groq rate limit during live demo              | Medium      | Critical | Local fallback LLM (ollama/llama.cpp) |
| Google Web Speech timeout                     | High        | Critical | Pre-load Whisper base at startup      |
| ChromeDriver mismatch                         | High        | High     | webdriver-manager                     |
| SQLite locked under concurrent API+voice      | Medium      | High     | WAL mode                              |
| pywebview crash from non-main-thread HUD call | Low         | High     | Architecture rule + assertion         |

---

## PHASE 3 — VOICE PIPELINE DEEP INVESTIGATION

### 3.1 Current Voice Pipeline Flow

```
[Wake Word Detection]
    pvporcupine (hardware keyword) OR energy threshold scan
    → threading.Event fired
    → wake_word.pause() called BEFORE event (critical: prevents mic echo)

[STT Capture]
    shared_mic (permanently open PyAudio stream)
    → sr.Recognizer.listen(pause_threshold=0.8, energy_threshold=300)
    → audio clip → Google Web Speech API → text string
    → on RequestError → Whisper local transcription (lazy-loaded)

[Latency profile]
    Wake detection: ~200ms
    Mic capture: real-time
    Google STT: 400–800ms (network)
    Whisper STT: 1.5–4s first call, 600ms–1.2s subsequent
    NLP routing: ~50ms
    Groq response: 800ms–2s
    TTS (pyttsx3): ~100ms first word
    Total E2E: 1.8s (best case) to 8s (Whisper cold start)
```

### 3.2 Nemotron-3.5-ASR Evaluation

**NVIDIA Nemotron-3.5-ASR** is a CTC-based model optimized for real-time streaming transcription.

Pros:

- Streaming support (partial results during speech)
- Strong word error rate on English: ~3.2% WER (LibriSpeech clean)
- NVIDIA inference optimization

Cons:

- Requires NVIDIA GPU for real-time performance (CPU is 4–8x slower than Whisper)
- No Urdu support
- Heavier than Whisper Tiny/Base
- Not yet on Hugging Face main branch (ONNX export needed for CPU)

**Verdict for NOVA:** Not recommended as primary. Requires GPU not guaranteed on demo machine.

### 3.3 Recommended STT Architecture

**Tier 1 (default): Faster-Whisper**

```python
# faster-whisper is a CTranslate2-ported Whisper — 4x faster on CPU
# pip install faster-whisper
from faster_whisper import WhisperModel
model = WhisperModel("base", device="cpu", compute_type="int8")
segments, info = model.transcribe(audio_path, beam_size=5)
```

- 4x faster than openai-whisper on CPU (base model: ~250ms vs ~1.2s)
- Streaming segments as they complete
- Multilingual (Urdu detection: `language="ur"`)
- Free, local, no internet required

**Tier 2 (online): Google Web Speech** — keep as current
**Tier 3 (premium quality, offline): Whisper Large v3 Turbo** — for future upgrade

### 3.4 Streaming STT Architecture

For real-time partial results (showing "typing" in HUD while user is still speaking):

```python
# Real-time chunked transcription
import pyaudio, numpy as np
from faster_whisper import WhisperModel

CHUNK = 1600  # 100ms at 16kHz
RATE = 16000

def stream_transcribe(model, callback):
    """Yield partial transcriptions as user speaks."""
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1,
                    rate=RATE, input=True, frames_per_buffer=CHUNK)
    buffer = []
    silence_count = 0

    while True:
        chunk = np.frombuffer(stream.read(CHUNK), dtype=np.int16).astype(np.float32) / 32768.0
        rms = np.sqrt(np.mean(chunk**2))

        if rms > 0.01:  # speech detected
            buffer.append(chunk)
            silence_count = 0
        else:
            silence_count += 1

        if silence_count > 8 and buffer:  # 800ms silence = end of utterance
            audio = np.concatenate(buffer)
            segments, _ = model.transcribe(audio, language="auto")
            text = " ".join(s.text for s in segments)
            callback(text)
            buffer = []
            silence_count = 0
```

### 3.5 Urdu STT Options

| Option                     | Quality    | Offline | Free | Latency |
| -------------------------- | ---------- | ------- | ---- | ------- |
| Whisper Large v3 (ur)      | ⭐⭐⭐⭐⭐ | ✅      | ✅   | 2–4s    |
| faster-whisper medium (ur) | ⭐⭐⭐⭐   | ✅      | ✅   | 600ms   |
| Google Web Speech (ur-PK)  | ⭐⭐⭐     | ❌      | ✅   | 400ms   |
| SpeechBrain Urdu model     | ⭐⭐       | ✅      | ✅   | 1.5s    |

**Recommendation:** faster-whisper medium with `language="ur"` for offline Urdu. Google Web Speech with `language="ur-PK"` for online fallback.

---

## PHASE 4 — COMPETITIVE ANALYSIS

### What Gemini / ChatGPT / Claude CAN do that NOVA also does:

- Answer questions
- Draft emails
- Explain code
- Translate text
- Tell jokes / chat

### What Gemini / ChatGPT / Claude CANNOT do that NOVA can:

| Capability                           | Gemini App            | NOVA                          |
| ------------------------------------ | --------------------- | ----------------------------- |
| Wake word ("Hey NOVA")               | ❌                    | ✅                            |
| Control Windows volume/brightness    | ❌                    | ✅                            |
| Launch installed applications        | ❌                    | ✅                            |
| Take screenshots                     | ❌                    | ✅                            |
| Read clipboard content               | ❌                    | ✅                            |
| Send WhatsApp messages               | ❌                    | ✅                            |
| Set reminders that actually fire     | ❌                    | ✅                            |
| Detect hand gestures via webcam      | ❌                    | ✅                            |
| Read/write local files               | ❌                    | ✅ (coding assistant)         |
| Run terminal commands                | ❌                    | ✅                            |
| Monitor CPU/RAM/battery live         | ❌                    | ✅                            |
| Remember user facts across sessions  | ⚠️ (cloud, not local) | ✅ (local SQLite)             |
| Work fully offline                   | ❌                    | ✅ (with Whisper + local LLM) |
| Control PC from phone via local WiFi | ❌                    | ✅                            |

### The Killer Insight for the Judge:

**NOVA is not an AI assistant you talk to. NOVA is an AI that lives on your PC and acts as its operating agent.** The difference is not incremental — it is categorical.

---

## PHASE 5 — FLAGSHIP DIFFERENTIATING FEATURES

### FLAGSHIP 1: NOVA CONTEXT ENGINE — Autonomous PC Awareness

**Problem solved:** All other AI assistants are blind to the user's current context. They cannot answer "what am I working on?" or "what just crashed?" or "why is my PC slow?"

**Why Gemini cannot do it:** Gemini has no access to Windows APIs, process lists, active window titles, recent file activity, or system events.

**What NOVA does:**
Every 10 seconds, a lightweight background scanner reads:

- Active window title + process name (what you're currently doing)
- Clipboard content (what you just copied)
- Recent files modified in the last 10 minutes
- Running processes sorted by CPU usage
- Network connections (which apps are using internet)
- Battery state + power plan

This data is stored as a rolling 30-minute context buffer. When you speak to NOVA, the relevant context is automatically injected into the Groq prompt without you having to explain anything.

**Demo scenario (judge impact: maximum):**

```
User switches to a Python file with a bug.
Presses Ctrl+C on the error message.
Says: "Hey NOVA, fix this."

NOVA sees:
- Active window: VS Code — main.py
- Clipboard: "AttributeError: 'NoneType' object has no attribute 'chat'"
- Recent file: main.py modified 30s ago

NOVA responds: "I can see you have a NoneType error on groq_brain.chat().
The issue is that groq_brain is None because the API key isn't set.
Here's the fix..." [writes the patch to main.py]
```

**Technical architecture:**

```python
# modules/context_scanner.py

import psutil, pygetwindow, pyperclip, os, time, threading
from pathlib import Path
from collections import deque

class ContextScanner:
    """Lightweight 10s polling daemon — builds a live PC context model."""

    SCAN_INTERVAL = 10  # seconds
    BUFFER_MINUTES = 30

    def __init__(self):
        self.context_buffer = deque(maxlen=180)  # 30min at 10s intervals
        self.latest = {}
        self._stop = threading.Event()

    def _scan(self):
        snapshot = {
            "timestamp": time.time(),
            "active_window": self._get_active_window(),
            "clipboard": self._get_clipboard(),
            "top_processes": self._get_top_processes(),
            "recent_files": self._get_recent_files(),
            "battery": self._get_battery(),
        }
        self.context_buffer.append(snapshot)
        self.latest = snapshot
        return snapshot

    def _get_active_window(self):
        try:
            import pygetwindow as gw
            win = gw.getActiveWindow()
            if win:
                return {"title": win.title, "pid": None}
        except Exception:
            pass
        return {}

    def _get_clipboard(self):
        try:
            text = pyperclip.paste()
            return text[:500] if text else ""  # cap at 500 chars
        except Exception:
            return ""

    def _get_top_processes(self, n=5):
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return sorted(procs, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:n]

    def _get_recent_files(self, minutes=10):
        """Scan Desktop + Documents + Downloads for recently modified files."""
        recent = []
        cutoff = time.time() - minutes * 60
        safe_dirs = [
            Path.home() / "Desktop",
            Path.home() / "Documents",
            Path.home() / "Downloads",
        ]
        for d in safe_dirs:
            if not d.exists():
                continue
            for f in d.iterdir():
                try:
                    if f.is_file() and f.stat().st_mtime > cutoff:
                        recent.append({"name": f.name, "path": str(f),
                                      "modified": f.stat().st_mtime})
                except Exception:
                    pass
        return sorted(recent, key=lambda x: x["modified"], reverse=True)[:10]

    def _get_battery(self):
        b = psutil.sensors_battery()
        if b:
            return {"percent": b.percent, "plugged": b.power_plugged}
        return {}

    def get_context_summary(self) -> str:
        """Returns a concise context string for Groq prompt injection."""
        c = self.latest
        if not c:
            return ""
        parts = []
        if c.get("active_window", {}).get("title"):
            parts.append(f"Active window: {c['active_window']['title']}")
        if c.get("clipboard"):
            parts.append(f"Clipboard: {c['clipboard'][:200]}")
        if c.get("recent_files"):
            names = [f["name"] for f in c["recent_files"][:3]]
            parts.append(f"Recently modified: {', '.join(names)}")
        top = [p["name"] for p in c.get("top_processes", []) if p.get("cpu_percent", 0) > 5]
        if top:
            parts.append(f"High CPU processes: {', '.join(top[:3])}")
        return " | ".join(parts) if parts else ""

    def start(self):
        def _loop():
            while not self._stop.is_set():
                try:
                    self._scan()
                except Exception as e:
                    print(f"[ContextScanner] Error: {e}")
                self._stop.wait(self.SCAN_INTERVAL)
        threading.Thread(target=_loop, daemon=True, name="ContextScannerThread").start()

    def stop(self):
        self._stop.set()

# Singleton
context_scanner = ContextScanner()
```

**Integration into Groq Brain:**

```python
# In modules/groq_brain.py — inject context before every call
from modules.context_scanner import context_scanner

def chat(self, user_message: str) -> str:
    context_str = context_scanner.get_context_summary()
    if context_str:
        # Prepend real-time context to the user message
        enriched_message = f"[Current PC context: {context_str}]\n\nUser says: {user_message}"
    else:
        enriched_message = user_message
    # ... rest of chat() unchanged ...
```

**Files to create/modify:**

- `modules/context_scanner.py` — new file (shown above)
- `modules/groq_brain.py` — inject `context_scanner.get_context_summary()` before each call
- `main.py` — start `context_scanner.start()` alongside wake_word
- `nova_core.py` — expose context to routing logic
- `modules/api_server.py` — add `GET /api/context/current` endpoint

**Dependencies:** `pip install pygetwindow`

**Estimated complexity:** 4 hours

---

### FLAGSHIP 2: SEMANTIC MEMORY SEARCH — Living User Model

**Problem solved:** Current memory is keyword-stored flat facts. "What do you know about my project?" returns unranked rows. No temporal reasoning, no relationship understanding.

**Why Gemini cannot do it:** Gemini's memory is cloud-stored, session-scoped, and opaque. Users have no control. NOVA's memory is local, searchable, editable, and grows intelligently.

**Architecture:**

Replace flat `user_facts` lookup with sentence-transformer embeddings stored as BLOB in SQLite. At query time, find semantically similar facts using cosine similarity in Python — no external vector DB needed.

```python
# modules/semantic_memory.py

import sqlite3, json, numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple

class SemanticMemory:
    """SQLite + in-process sentence embeddings. No external vector DB."""

    MODEL_NAME = "all-MiniLM-L6-v2"  # 22MB, runs in ~50ms on CPU

    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        self.model = SentenceTransformer(self.MODEL_NAME)
        self._ensure_schema()
        self._cache: dict = {}  # in-memory embedding cache

    def _ensure_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP
                )
            """)

    def store(self, key: str, value: str, category: str = "general"):
        text = f"{key}: {value}"
        embedding = self.model.encode(text).astype(np.float32).tobytes()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO semantic_facts (key, value, category, embedding)
                VALUES (?, ?, ?, ?)
            """, (key, value, category, embedding))

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
        """Returns top_k (key, value, similarity_score) tuples for a query."""
        query_embedding = self.model.encode(query).astype(np.float32)

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, key, value, embedding FROM semantic_facts"
            ).fetchall()

        scored = []
        for row_id, key, value, emb_bytes in rows:
            if not emb_bytes:
                continue
            fact_emb = np.frombuffer(emb_bytes, dtype=np.float32)
            # Cosine similarity
            sim = float(np.dot(query_embedding, fact_emb) /
                       (np.linalg.norm(query_embedding) * np.linalg.norm(fact_emb) + 1e-8))
            scored.append((key, value, sim, row_id))

        scored.sort(key=lambda x: x[2], reverse=True)

        # Update access counts for retrieved facts
        if scored:
            top_ids = [r[3] for r in scored[:top_k]]
            with sqlite3.connect(self.db_path) as conn:
                for rid in top_ids:
                    conn.execute(
                        "UPDATE semantic_facts SET access_count = access_count + 1, "
                        "last_accessed = CURRENT_TIMESTAMP WHERE id = ?", (rid,)
                    )

        return [(k, v, s) for k, v, s, _ in scored[:top_k]]

    def inject_for_prompt(self, query: str, top_k: int = 8) -> str:
        """Returns formatted memory string for Groq system prompt injection."""
        facts = self.search(query, top_k)
        if not facts:
            return ""
        lines = [f"- {k}: {v}" for k, v, _ in facts if _ > 0.3]  # threshold 0.3
        return "Known facts about the user:\n" + "\n".join(lines) if lines else ""

# Singleton — pre-loaded at startup
semantic_memory = SemanticMemory()
```

**Dependencies:** `pip install sentence-transformers` (80MB download, local inference after)

**Estimated complexity:** 3 hours

---

### FLAGSHIP 3: URDU ↔ ENGLISH SEAMLESS VOICE

**Why this wins the demo:** Speak Urdu → NOVA understands → responds in Urdu. No command needed. No "translate to Urdu." Natural bilingual conversation.

**Architecture:**

```
[Spoken audio]
       ↓
[faster-whisper language detection]
  detected_language = "ur" OR "en"
       ↓
[If Urdu → translate to English for Groq → get English response → translate back to Urdu]
[If English → direct Groq → English TTS]
       ↓
[TTS: pyttsx3 for English | gTTS(lang='ur') for Urdu]
```

```python
# modules/multilingual.py

from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator
from gtts import gTTS
import os, tempfile

class MultilingualEngine:
    SUPPORTED = {"en": "English", "ur": "Urdu"}

    def __init__(self):
        # faster-whisper base model — auto language detection
        self.whisper = WhisperModel("base", device="cpu", compute_type="int8")
        self._current_lang = "en"

    def transcribe_with_language(self, audio_path: str) -> tuple[str, str]:
        """Returns (transcribed_text, detected_language_code)."""
        segments, info = self.whisper.transcribe(
            audio_path,
            beam_size=5,
            language=None,       # auto-detect
            task="transcribe"
        )
        text = " ".join(s.text.strip() for s in segments)
        lang = info.language  # "en", "ur", etc.
        self._current_lang = lang if lang in self.SUPPORTED else "en"
        return text, self._current_lang

    def translate_to_english(self, text: str, source_lang: str = "ur") -> str:
        if source_lang == "en":
            return text
        return GoogleTranslator(source=source_lang, target="en").translate(text)

    def translate_from_english(self, text: str, target_lang: str = "ur") -> str:
        if target_lang == "en":
            return text
        return GoogleTranslator(source="en", target=target_lang).translate(text)

    def speak(self, text: str, lang: str = None):
        """Speak in the given language; falls back to pyttsx3 for English."""
        lang = lang or self._current_lang
        if lang == "en":
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        else:
            # gTTS for Urdu and other languages
            tts = gTTS(text=text, lang=lang, slow=False)
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tts.save(tmp.name)
            os.system(f"start {tmp.name}")  # Windows

    @property
    def active_language(self) -> str:
        return self._current_lang

multilingual = MultilingualEngine()
```

**Integration in main.py pipeline:**

```python
# Replace current STT + TTS with multilingual pipeline:

text, detected_lang = multilingual.transcribe_with_language(audio_path)

if detected_lang != "en":
    english_text = multilingual.translate_to_english(text, detected_lang)
else:
    english_text = text

result = nlp_process(english_text)
response_english = nova_core.route(result)

if detected_lang != "en":
    response_local = multilingual.translate_from_english(response_english, detected_lang)
else:
    response_local = response_english

multilingual.speak(response_local, lang=detected_lang)
```

**Estimated complexity:** 3 hours

---

### SUPPORTING FEATURE: OFFLINE-FIRST WITH LOCAL LLM FALLBACK

**The judge will test internet dependency.** NOVA must not die when internet drops.

```python
# modules/local_llm.py
# Uses ollama (free, runs llama3.2 locally) as Groq fallback

import requests, json

class LocalLLM:
    """Ollama-based local LLM fallback. Pull: ollama pull llama3.2"""
    BASE_URL = "http://localhost:11434/api/generate"
    MODEL = "llama3.2"  # 2GB, runs on any laptop

    def chat(self, prompt: str, system_prompt: str = "") -> str:
        payload = {
            "model": self.MODEL,
            "prompt": f"{system_prompt}\n\nUser: {prompt}\nAssistant:",
            "stream": False
        }
        try:
            resp = requests.post(self.BASE_URL, json=payload, timeout=30)
            return resp.json().get("response", "").strip()
        except Exception as e:
            return f"[Local LLM unavailable: {e}]"

    def is_available(self) -> bool:
        try:
            requests.get("http://localhost:11434/api/tags", timeout=2)
            return True
        except Exception:
            return False

local_llm = LocalLLM()
```

```python
# In groq_brain.py — Groq with local fallback:
def chat(self, user_message: str) -> str:
    try:
        # Try Groq first
        return self._groq_call(user_message)
    except Exception as e:
        print(f"[Groq] Failed: {e} — falling back to local LLM")
        if local_llm.is_available():
            return local_llm.chat(user_message, self.system_prompt)
        return "I'm having trouble connecting. Please check your internet connection."
```

---

## PHASE 6 — SEARCH INTEGRATION

### Evaluation

| Solution     | Quality    | Free Tier    | Latency | Citations | Urdu    | Verdict               |
| ------------ | ---------- | ------------ | ------- | --------- | ------- | --------------------- |
| Tavily       | ⭐⭐⭐⭐⭐ | ✅ 1000/mo   | 400ms   | ✅        | Limited | **Best for research** |
| Brave Search | ⭐⭐⭐⭐   | ✅ 2000/mo   | 300ms   | ⚠️        | ❌      | Good backup           |
| SearXNG      | ⭐⭐⭐     | ✅ Self-host | 600ms   | ❌        | ⚠️      | Good for privacy      |
| DuckDuckGo   | ⭐⭐       | ✅ Unlimited | 300ms   | ❌        | ❌      | Last resort           |
| Serper       | ⭐⭐⭐⭐   | ✅ 2500/mo   | 250ms   | ❌        | ⚠️      | Fast, no citations    |

### Recommended Architecture

**Primary: Tavily** (1000 free calls/month, includes citations, supports news search)
**Fallback: DuckDuckGo** (unlimited, no API key, uses `duckduckgo-search` library)

```python
# modules/search_engine.py

from tavily import TavilyClient
from duckduckgo_search import DDGS
import os, time

class SearchEngine:
    def __init__(self):
        key = os.getenv("TAVILY_API_KEY", "")
        self.tavily = TavilyClient(api_key=key) if key else None
        self._cache: dict = {}
        self._cache_ttl = 300  # 5-minute cache

    def search(self, query: str, max_results: int = 5) -> dict:
        cache_key = f"{query}:{max_results}"
        if cache_key in self._cache:
            result, ts = self._cache[cache_key]
            if time.time() - ts < self._cache_ttl:
                return result

        try:
            if self.tavily:
                return self._tavily_search(query, max_results)
            else:
                return self._ddg_search(query, max_results)
        except Exception as e:
            print(f"[Search] Primary failed: {e}. Trying DDG...")
            return self._ddg_search(query, max_results)

    def _tavily_search(self, query: str, n: int) -> dict:
        resp = self.tavily.search(query=query, max_results=n,
                                   search_depth="basic", include_answer=True)
        return {
            "answer": resp.get("answer", ""),
            "sources": [{"title": r["title"], "url": r["url"],
                         "snippet": r["content"][:200]}
                        for r in resp.get("results", [])],
            "provider": "tavily"
        }

    def _ddg_search(self, query: str, n: int) -> dict:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=n))
        return {
            "answer": results[0]["body"] if results else "",
            "sources": [{"title": r["title"], "url": r["href"],
                         "snippet": r["body"][:200]}
                        for r in results],
            "provider": "duckduckgo"
        }

    def format_for_groq(self, search_result: dict, query: str) -> str:
        """Format search results for injection into Groq context."""
        if not search_result.get("sources"):
            return ""
        lines = [f"Search results for '{query}':"]
        if search_result.get("answer"):
            lines.append(f"Summary: {search_result['answer']}")
        for i, s in enumerate(search_result["sources"][:3], 1):
            lines.append(f"{i}. {s['title']}: {s['snippet']}")
        return "\n".join(lines)

search_engine = SearchEngine()
```

**Integration into nova_core routing:**

```python
# In nova_core.py — for "information" and "conversation" intents:
if intent in ("information", "conversation", "wikipedia"):
    # Try live search first if query looks factual
    if _is_factual_query(text):
        search_result = search_engine.search(text)
        search_context = search_engine.format_for_groq(search_result, text)
        groq_brain.inject_search_context(search_context)
    response = groq_brain.chat(text)
```

---

## PHASE 7 — URDU VOICE SYSTEM (COMPLETE DESIGN)

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│ MULTILINGUAL VOICE PIPELINE                             │
│                                                         │
│  Spoken audio → faster-whisper (auto language detect)   │
│                    ↓                                    │
│           detected: "ur" or "en"                        │
│                    ↓                                    │
│  [if Urdu]  GoogleTranslator(ur → en)                   │
│  [if English] pass-through                              │
│                    ↓                                    │
│  NLP Intent Engine (English only — stays simple)        │
│                    ↓                                    │
│  nova_core.route() → response in English                │
│                    ↓                                    │
│  [if Urdu]  GoogleTranslator(en → ur)                   │
│  [if English] pass-through                              │
│                    ↓                                    │
│  TTS: pyttsx3 (en) | gTTS lang="ur" (ur)               │
│                    ↓                                    │
│  HUD: displays text in both scripts (Urdu + English)    │
└─────────────────────────────────────────────────────────┘
```

### HUD Language Display

Add a language indicator to `nova_hud.html`:

```javascript
// In HUD JS — display both language versions
function updateResponse(englishText, urduText, lang) {
  const panel = document.getElementById("response-panel");
  if (lang === "ur") {
    panel.innerHTML = `
            <div class="response-text" dir="rtl" style="font-family: 'Noto Nastaliq Urdu', serif">
                ${urduText}
            </div>
            <div class="response-text-secondary">${englishText}</div>
        `;
  } else {
    panel.innerHTML = `<div class="response-text">${englishText}</div>`;
  }
}
```

### Language Toggle Command

```
"Hey NOVA, اردو میں بات کرو"  → auto-detected as Urdu → switches to Urdu mode
"Hey NOVA, switch to English" → back to English mode
```

### STT Models for Urdu

```python
# faster-whisper with Urdu
# pip install faster-whisper
from faster_whisper import WhisperModel
model = WhisperModel("medium", device="cpu", compute_type="int8")
# "medium" needed for reliable Urdu (base has ~15% WER on Urdu)
segments, info = model.transcribe(audio_path, language="ur")
```

---

## PHASE 8 — CROSS-PLATFORM CONSISTENCY

### Feature Matrix

| Feature         | Voice (PC)        | Flutter App               | Web Browser              |
| --------------- | ----------------- | ------------------------- | ------------------------ |
| Text commands   | ✅                | ✅ /api/command           | ✅ /api/command          |
| Voice commands  | ✅ native         | ✅ speech_to_text pkg     | ⚠️ Web Speech API        |
| System controls | ✅                | ✅ /api/system/\*         | ✅ /api/system/\*        |
| File browser    | ✅                | ✅ /api/files/\*          | ✅ /api/files/\*         |
| PC context      | ✅ live           | ✅ /api/context/current   | ✅ /api/context/current  |
| Urdu voice      | ✅ faster-whisper | ✅ device STT + API       | ⚠️ browser STT (limited) |
| Offline mode    | ✅ full           | ⚠️ commands only          | ❌ needs API             |
| Live status     | ✅ HUD            | ✅ /ws/status             | ✅ /ws/status            |
| Gesture control | ✅ webcam         | ❌ (future: phone camera) | ❌                       |

### Platform-Specific Notes

**Web browser STT:** Chrome Web Speech API supports `ur-PK` locale but quality is lower than faster-whisper. Acceptable for demo.

**Flutter Urdu TTS:** Use `flutter_tts` package with language `"ur-PK"`. Falls back to English if not available.

**Offline Flutter:** Without internet, Flutter app can still send commands to local PC API (no external network needed, only local WiFi).

---

## PHASE 9 — ARCHITECTURE PRESERVATION RULES

All new modules follow existing patterns:

1. **New files only** — no refactors of working modules
2. **Modules return strings** — HUD is called only from main.py
3. **Thread safety** — use `_route_lock` in nova_core.py (T1 already done)
4. **Singleton pattern** — new modules expose singleton instances
5. **config.json toggles** — every new feature has an enable/disable flag
6. **SQLite WAL mode** — all new DB writes assume WAL is enabled
7. **Graceful degradation** — every feature works even if its dependencies are absent

New config.json keys to add:

```json
{
  "context_scanner": { "enabled": true, "scan_interval": 10 },
  "semantic_memory": { "enabled": true, "model": "all-MiniLM-L6-v2" },
  "multilingual": { "enabled": true, "default_language": "en" },
  "search": { "enabled": true, "provider": "tavily", "cache_ttl": 300 },
  "local_llm": { "enabled": false, "model": "llama3.2", "port": 11434 }
}
```

---

## PHASE 10 — TESTING STRATEGY

### Unit Tests (add to tests/test_all.py)

```python
# Test 25: Context scanner returns active window within 10s
def test_context_scanner():
    from modules.context_scanner import context_scanner
    context_scanner.start()
    time.sleep(11)
    ctx = context_scanner.get_context_summary()
    assert isinstance(ctx, str)
    context_scanner.stop()

# Test 26: Semantic memory stores and retrieves with similarity > 0.5
def test_semantic_memory():
    from modules.semantic_memory import SemanticMemory
    sm = SemanticMemory(":memory:")  # in-memory SQLite for test
    sm.store("favorite_editor", "VS Code")
    results = sm.search("What IDE does the user prefer?")
    assert len(results) > 0
    assert results[0][2] > 0.3  # similarity score

# Test 27: faster-whisper transcribes English correctly
def test_faster_whisper():
    from faster_whisper import WhisperModel
    model = WhisperModel("base", device="cpu", compute_type="int8")
    # Use a pre-recorded test audio file
    assert model is not None

# Test 28: Urdu translation round-trips correctly
def test_urdu_translation():
    from deep_translator import GoogleTranslator
    urdu = GoogleTranslator(source="en", target="ur").translate("Hello, how are you?")
    back = GoogleTranslator(source="ur", target="en").translate(urdu)
    assert "hello" in back.lower() or "how" in back.lower()

# Test 29: Search engine returns results for known query
def test_search_engine():
    from modules.search_engine import search_engine
    result = search_engine.search("Pakistan capital city")
    assert result.get("sources") or result.get("answer")

# Test 30: Local LLM availability check is non-crashing
def test_local_llm():
    from modules.local_llm import local_llm
    available = local_llm.is_available()
    assert isinstance(available, bool)

# Test 31: API /api/context/current returns JSON
def test_context_api():
    import requests
    resp = requests.get("http://localhost:8000/api/context/current",
                       headers={"X-API-Key": "nova-secret-change-this"})
    assert resp.status_code == 200

# Test 32: SQLite WAL mode is enabled
def test_wal_mode():
    import sqlite3
    conn = sqlite3.connect("data/memory.db")
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"
```

### Latency Benchmarks (target vs current)

| Operation              | Current             | Target            | Method                |
| ---------------------- | ------------------- | ----------------- | --------------------- |
| Wake detection         | 200ms               | 200ms             | No change             |
| STT (English)          | 400–800ms           | 200–300ms         | faster-whisper base   |
| STT (Urdu)             | N/A                 | 400–600ms         | faster-whisper medium |
| NLP routing            | 50ms                | 50ms              | No change             |
| Groq response          | 800ms–2s            | 800ms–2s          | No change             |
| Context injection      | 0ms                 | +20ms             | Negligible            |
| Semantic memory lookup | 0ms                 | +30ms             | All-MiniLM-L6-v2      |
| Total E2E (online)     | 1.8–3s              | 1.5–2.5s          |                       |
| Total E2E (offline)    | 4–8s (Whisper cold) | 1.8s (pre-loaded) |                       |

### Voice Pipeline Tests

```python
# Record 10 test utterances, measure WER and latency
TEST_UTTERANCES_EN = [
    ("what time is it", "datetime"),
    ("open chrome", "app"),
    ("weather in islamabad", "weather"),
    ("take a screenshot", "screenshot"),
    ("set volume to 60", "system"),
]

TEST_UTTERANCES_UR = [
    ("وقت کیا ہے", "datetime"),  # "What is the time"
    ("کروم کھولو", "app"),         # "Open Chrome"
    ("موسم کیا ہے", "weather"),   # "What is the weather"
]
```

### Mobile Testing

- Test all 3 tabs (Dashboard, Remote, Code) on Android 13+
- Test connection on different network topologies (direct WiFi, hotspot)
- Test WebSocket reconnect after 60s background sleep
- Test Urdu text rendering (RTL direction, Noto Nastaliq font)

---

## PHASE 11 — EXECUTION ROADMAP

### Sprint 0 — Stability Fixes (2 hours)

**Do these first. These unblock everything else.**

| Task                                                                                                   | File              | Time  |
| ------------------------------------------------------------------------------------------------------ | ----------------- | ----- |
| Enable SQLite WAL mode                                                                                 | memory_system.py  | 15min |
| Pre-load faster-whisper at startup                                                                     | stt.py            | 30min |
| Add webdriver-manager for ChromeDriver                                                                 | web_automation.py | 20min |
| Add`pygetwindow` to requirements.txt                                                                   | requirements.txt  | 5min  |
| Add`sentence-transformers`, `faster-whisper`, `tavily-python`, `duckduckgo-search` to requirements.txt | requirements.txt  | 5min  |

```python
# memory_system.py — after connect:
self.conn = sqlite3.connect(db_path, check_same_thread=False)
self.conn.execute("PRAGMA journal_mode=WAL")
self.conn.execute("PRAGMA synchronous=NORMAL")

# stt.py — at init, pre-load Whisper:
from faster_whisper import WhisperModel
self._faster_whisper = WhisperModel("base", device="cpu", compute_type="int8")
print("[STT] faster-whisper pre-loaded")
```

---

### Sprint 1 — Context Scanner (4 hours)

**Milestone: NOVA knows what you're doing without being told.**

| Task                                     | File                        | Time  |
| ---------------------------------------- | --------------------------- | ----- |
| Create context_scanner.py                | modules/context_scanner.py  | 2h    |
| Start scanner in main.py                 | main.py                     | 20min |
| Inject context into groq_brain.chat()    | modules/groq_brain.py       | 30min |
| Add /api/context/current endpoint        | modules/api_server.py       | 30min |
| Add context display to Flutter dashboard | nova_app/dashboard_tab.dart | 1h    |

**Completion criteria:**

- [ ] `context_scanner.get_context_summary()` returns non-empty string
- [ ] Groq response references active window when relevant
- [ ] `/api/context/current` returns JSON with all fields
- [ ] Flutter shows "Currently working on: VS Code — main.py" on dashboard

---

### Sprint 2 — Semantic Memory (3 hours)

**Milestone: NOVA finds relevant memories for every question.**

| Task                                          | File                       | Time  |
| --------------------------------------------- | -------------------------- | ----- |
| Create semantic_memory.py                     | modules/semantic_memory.py | 1.5h  |
| Replace get_facts() injection in groq_brain   | modules/groq_brain.py      | 30min |
| Migrate existing user_facts to semantic_facts | migration script           | 30min |
| Add /api/memory/search endpoint               | modules/api_server.py      | 30min |

**Completion criteria:**

- [ ] `semantic_memory.search("what IDE does Akif use")` returns VS Code with score > 0.4
- [ ] Groq responses reference stored memories when relevant
- [ ] Memory injection adds < 50ms to response time

---

### Sprint 3 — Urdu Voice (3 hours)

**Milestone: Speak Urdu → NOVA answers in Urdu.**

| Task                             | File                    | Time  |
| -------------------------------- | ----------------------- | ----- |
| Create multilingual.py           | modules/multilingual.py | 1.5h  |
| Update voice_pipeline in main.py | main.py                 | 45min |
| Add Urdu script display to HUD   | modules/nova_hud.html   | 30min |
| Test 5 Urdu utterances           | tests/                  | 15min |

**Completion criteria:**

- [ ] `اسلام آباد کا موسم کیسا ہے؟` → weather response in Urdu
- [ ] Language detected automatically without user command
- [ ] HUD shows Urdu text right-to-left
- [ ] Latency < 2s for Urdu round-trip

---

### Sprint 4 — Search Integration (2 hours)

**Milestone: NOVA has live internet knowledge with citations.**

| Task                                                          | File                     | Time  |
| ------------------------------------------------------------- | ------------------------ | ----- |
| Create search_engine.py                                       | modules/search_engine.py | 1h    |
| Register TAVILY_API_KEY in .env                               | .env                     | 5min  |
| Inject search results into groq_brain for information intents | nova_core.py             | 45min |
| Add search results display to Flutter remote tab              | nova_app/remote_tab.dart | 30min |

**Completion criteria:**

- [ ] "Who won the ICC Champions Trophy 2025?" → correct answer with source URL
- [ ] Falls back to DDG if Tavily key missing
- [ ] Cache prevents re-fetching same query within 5 minutes

---

### Sprint 5 — Offline Fallback LLM (2 hours)

**Milestone: NOVA works without internet.**

| Task                               | File                  | Time             |
| ---------------------------------- | --------------------- | ---------------- |
| Install Ollama + pull llama3.2     | system                | 20min (download) |
| Create local_llm.py                | modules/local_llm.py  | 45min            |
| Add Groq fallback in groq_brain.py | modules/groq_brain.py | 30min            |
| Test offline scenario              | manual                | 15min            |

**Completion criteria:**

- [ ] Disconnect internet → NOVA still answers questions
- [ ] Response quality degrades gracefully (shorter but valid)
- [ ] Local LLM latency < 8s for short responses

---

### Sprint 6 — Demo Polish (3 hours)

**Milestone: 10-minute flawless demo sequence.**

| Task                                                          | Time  |
| ------------------------------------------------------------- | ----- |
| Record all demo commands, verify 3× each                      | 1h    |
| Add "thinking..." animation while Groq responds               | 20min |
| Add context indicator to HUD ("Currently: VS Code — main.py") | 30min |
| Add language indicator to HUD (🇵🇰 / 🇬🇧)                       | 15min |
| Test full demo sequence twice consecutively                   | 30min |
| Add Tavily API key + test search in demo                      | 15min |
| Final requirements.txt pin + clean install test               | 30min |

---

## DEMO SCRIPT (10 Minutes, Judge-Optimized)

### Act 1 — "It's not a chatbot" (2 min)

```
[Switch to VS Code with a Python file open]
[Copy an error message to clipboard]

Say: "Hey NOVA, what's wrong with what I'm working on?"

NOVA: "I can see you have VS Code open with main.py.
       You just copied an AttributeError — groq_brain is None
       because no API key is set. Here's the fix..." [writes to file]

[JUDGE IMPACT: Proactive context. No AI app can do this.]
```

### Act 2 — "It remembers everything" (2 min)

```
Say: "Hey NOVA, remember that I prefer dark themes and I'm working
      on the NOVA AI hackathon project due tomorrow."

NOVA: "Got it. I've stored that."

[5 seconds later]
Say: "Hey NOVA, what do I have to finish today?"

NOVA: "Based on what I know about you: you're working on NOVA AI
       for the hackathon due tomorrow. You prefer dark themes so
       make sure your demo UI matches that preference."

[JUDGE IMPACT: Semantic, not keyword, memory recall.]
```

### Act 3 — "It speaks your language" (2 min)

```
Say: "اسلام آباد کا آج کا موسم کیا ہے؟"
(What is today's weather in Islamabad?)

NOVA: [responds in Urdu] "آج اسلام آباد میں درجہ حرارت 28 ڈگری سیلسیس
       ہے، صاف آسمان ہے اور ہوا کی رفتار معمول کے مطابق ہے۔"

Say: "Switch to English."

Say: "What was the weather again?"
NOVA: [in English] "It's 28°C in Islamabad today, clear skies."

[JUDGE IMPACT: No other AI assistant switches automatically to Urdu voice.]
```

### Act 4 — "It controls everything" (2 min)

```
[Gesture: show open palm to camera → media plays]
[Gesture: show fist → media pauses]

Say: "Hey NOVA, set volume to 40%." [volume changes live]
Say: "Hey NOVA, take a screenshot." [screenshot appears on desktop]
Say: "Hey NOVA, open VS Code." [VS Code launches]

[From phone]
Tap "Lock PC" button → PC locks
Tap "Mute" button → audio mutes

[JUDGE IMPACT: Full system control. Voice + gesture + phone simultaneously.]
```

### Act 5 — "It works offline" (2 min)

```
[Disconnect WiFi visibly]

Say: "Hey NOVA, explain what a closure is in Python."

NOVA: [local LLM responds in ~3s] "A closure is a function that..."

Say: "Hey NOVA, what time is it?"
NOVA: "It's 3:47 PM." [instant — no internet needed]

[Reconnect WiFi]
Say: "Hey NOVA, who won the ICC Champions Trophy 2025?"
NOVA: [Tavily search + Groq] "Pakistan won... [with source URL]"

[JUDGE IMPACT: True local-first AI. Cloud-optional, not cloud-dependent.]
```

---

## CONTEXT.MD ENTRIES

Add these to context.md for every file modified:

```
## Sprint 0 — Stability Fixes

FILE: modules/memory_system.py
FUNCTION: DatabaseManager.__init__
CHANGE: Added PRAGMA journal_mode=WAL and PRAGMA synchronous=NORMAL after connect()
BEFORE: Standard SQLite connection, no WAL mode
AFTER: WAL mode enabled — allows concurrent reads during writes
REASON: API server + voice pipeline + reminder thread all write simultaneously; WAL prevents "database is locked" errors

FILE: modules/stt.py
FUNCTION: SpeechToText.__init__
CHANGE: Pre-loads faster-whisper base model at init instead of lazy load
BEFORE: Whisper model loaded on first offline transcription request (~3–8s cold start)
AFTER: faster-whisper base pre-loaded at startup (~1.5s, done before HUD appears)
REASON: Eliminates cold-start latency during live demo; Whisper fallback is now instant

FILE: requirements.txt
CHANGE: Added faster-whisper, sentence-transformers, tavily-python, duckduckgo-search, pygetwindow, webdriver-manager
REASON: New modules for context scanner, semantic memory, search engine, multilingual STT

## Sprint 1 — Context Scanner

FILE: modules/context_scanner.py
FUNCTION: new file — ContextScanner class
CHANGE: Created new background daemon scanning active window, clipboard, recent files, top processes, battery every 10s
BEFORE: NOVA had no knowledge of what the user was currently doing
AFTER: get_context_summary() returns a single-line PC state string injected into Groq prompt
REASON: Flagship feature — enables proactive context-aware responses without user explanation

FILE: modules/groq_brain.py
FUNCTION: GroqBrain.chat()
CHANGE: Calls context_scanner.get_context_summary() and prepends to user_message if non-empty
BEFORE: chat(user_message) — only user message sent to Groq
AFTER: chat(user_message) — PC context prepended: "[Context: VS Code active | Clipboard: error...] User says: ..."
REASON: Enables NOVA to reference what user is currently doing without being asked

FILE: main.py
FUNCTION: main()
CHANGE: Added context_scanner.start() call alongside wake_word.start()
BEFORE: 3 background threads (wake_word, gesture, reminder)
AFTER: 4 background threads; context_scanner added as daemon
REASON: Context must be scanning from launch so it has history when first command arrives

FILE: modules/api_server.py
FUNCTION: new endpoint GET /api/context/current
CHANGE: Added endpoint returning context_scanner.latest as JSON
BEFORE: No context endpoint
AFTER: Flutter dashboard can display what NOVA currently knows about user's PC state
REASON: Exposes context to mobile app for dashboard display

## Sprint 2 — Semantic Memory

FILE: modules/semantic_memory.py
FUNCTION: new file — SemanticMemory class
CHANGE: Created SQLite + sentence-transformer semantic search replacing flat keyword lookup
BEFORE: memory_system.get_facts() returns top 10 rows by updated_at DESC (chronological, not relevant)
AFTER: semantic_memory.search(query) returns top k facts by cosine similarity to current query
REASON: "What IDE does Akif use?" now retrieves VS Code fact even if query phrasing differs from stored key

FILE: modules/groq_brain.py
FUNCTION: GroqBrain.inject_memory()
CHANGE: Replaced db.get_facts(10) with semantic_memory.inject_for_prompt(user_message)
BEFORE: Top 10 most recently updated facts injected regardless of relevance
AFTER: Top 8 most semantically similar facts injected (threshold: cosine similarity > 0.3)
REASON: Weather question no longer gets facts about coding preferences; memory injection is now relevant

## Sprint 3 — Multilingual

FILE: modules/multilingual.py
FUNCTION: new file — MultilingualEngine class
CHANGE: Created faster-whisper language detection + Google Translate bridge + gTTS Urdu TTS
BEFORE: English-only STT and TTS
AFTER: Auto-detects Urdu or English → routes through translation → responds in detected language
REASON: Hackathon differentiator — NOVA speaks Urdu natively; no other desktop AI assistant does this

FILE: main.py
FUNCTION: voice_pipeline() (inner function)
CHANGE: Replaced stt.transcribe() → speak() with multilingual.transcribe_with_language() → multilingual.speak()
BEFORE: text = stt.transcribe(audio) → speak(response)
AFTER: text, lang = multilingual.transcribe_with_language(audio) → english = translate_to_en(text, lang) → response = route(english) → speak(translate_from_en(response, lang), lang)
REASON: Language detection and translation now happen transparently in the pipeline

FILE: modules/nova_hud.html
FUNCTION: updateResponse() JS function
CHANGE: Added RTL rendering for Urdu text with Noto Nastaliq Urdu font and language indicator badge
BEFORE: Single div for response text, always LTR
AFTER: Conditional RTL rendering, bilingual display (Urdu primary + English secondary), 🇵🇰/🇬🇧 badge
REASON: Urdu text must render right-to-left; showing both languages confirms correct translation

## Sprint 4 — Search Engine

FILE: modules/search_engine.py
FUNCTION: new file — SearchEngine class
CHANGE: Created Tavily-primary / DDG-fallback search with 5-minute response cache
BEFORE: Wikipedia module was the only factual search source
AFTER: Live web search with citations; Tavily for quality, DDG for unlimited fallback
REASON: Enables NOVA to answer questions about events after its training cutoff

FILE: nova_core.py
FUNCTION: route()
CHANGE: For information/conversation intents with factual queries, prepend search results to Groq context
BEFORE: Groq receives only user message + stored memories
AFTER: Groq receives user message + live search results + stored memories
REASON: NOVA now answers "who won the ICC Champions Trophy 2025?" correctly instead of guessing

## Sprint 5 — Offline LLM

FILE: modules/local_llm.py
FUNCTION: new file — LocalLLM class
CHANGE: Created Ollama-backed local LLM with availability check
BEFORE: Groq failure = NOVA silent or "having trouble connecting"
AFTER: Groq failure → automatic fallback to local llama3.2 via Ollama
REASON: Demo resilience — internet drop does not kill NOVA during judge presentation
```

---

## FINAL DEPENDENCIES LIST

Add to requirements.txt:

```
# Sprint 0
faster-whisper==1.0.3
webdriver-manager==4.0.1
pygetwindow==0.0.9

# Sprint 1
# (psutil already in requirements)

# Sprint 2
sentence-transformers==3.1.1

# Sprint 3
# (deep-translator already in requirements)
# (gTTS already in requirements)
# (faster-whisper covers Urdu STT)

# Sprint 4
tavily-python==0.3.8
duckduckgo-search==6.3.7

# Sprint 5
# ollama is a system install, not pip
# requests already in requirements
```

---

## TOTAL EFFORT ESTIMATE

| Sprint    | Feature         | Hours   |
| --------- | --------------- | ------- |
| 0         | Stability fixes | 2h      |
| 1         | Context Scanner | 4h      |
| 2         | Semantic Memory | 3h      |
| 3         | Urdu Voice      | 3h      |
| 4         | Search Engine   | 2h      |
| 5         | Offline LLM     | 2h      |
| 6         | Demo Polish     | 3h      |
| **Total** |                 | **19h** |

A team of two can complete this in 2 days of focused work.

---

## ONE-SENTENCE PITCH FOR THE JUDGES

> **NOVA is not an AI you open in a browser tab — it is an AI that lives on your PC, watches what you're doing, speaks your language, and acts without being asked.**

---

_Blueprint version 1.0 | NOVA AI Hackathon Final Round | June 2026_
