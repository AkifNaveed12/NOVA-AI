# NOVA AI — Complete Project Idea & System Reference
> Neural Orchestrated Voice Assistant with Autonomous Intelligence  
> COMSATS University Islamabad, Wah Campus  
> Muhammad Akif Naveed — FA24-BSE-129  
> Supervised by: Ms. Maira Afzal  
> Course: Artificial Intelligence  

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Core Design Philosophy](#2-core-design-philosophy)
3. [System Architecture](#3-system-architecture)
4. [Dual-Pipeline Execution Model](#4-dual-pipeline-execution-model)
5. [Module-by-Module Breakdown](#5-module-by-module-breakdown)
6. [How Everything Communicates](#6-how-everything-communicates)
7. [Complete Tech Stack](#7-complete-tech-stack)
8. [JSON Config Contracts](#8-json-config-contracts)
9. [Database Schema](#9-database-schema)
10. [Routing Logic — NLP vs Groq](#10-routing-logic--nlp-vs-groq)
11. [Thread Architecture](#11-thread-architecture)
12. [End-to-End Command Flow](#12-end-to-end-command-flow)
13. [Project Folder Structure](#13-project-folder-structure)
14. [Scope & Boundaries](#14-scope--boundaries)
15. [End Goal](#15-end-goal)

---

## 1. Project Overview

NOVA AI is a **fully local, voice-controlled intelligent personal assistant** for Windows, built entirely in Python 3.11 using free and open-source tools. It is not a wrapper around a cloud service — it is a real, self-contained AI system with 25 independent modules that collectively handle voice interaction, natural language understanding, LLM-powered reasoning, OS automation, real-time web APIs, persistent memory, computer vision gesture control, and a live HUD interface.

**Full name:** NOVA — Neural Orchestrated Voice Assistant with Autonomous Intelligence  
**Activation phrase:** "Hey NOVA"  
**Platform:** Windows 10/11 only  
**Language runtime:** Python 3.11  
**Cost to run:** Zero — all APIs and libraries are free tier or open-source  
**Execution:** Fully local — no cloud hosting, no server, no mobile companion  

The system is designed as a **semester AI project** that demonstrates real integration of NLP pipelines, LLM APIs, computer vision, OS automation, and software architecture — targeting an impressive, demo-ready result for presentation to the course representative.

---

## 2. Core Design Philosophy

Three principles govern every architectural decision in NOVA:

### 2.1 Voice-First, Always-On
NOVA never fully sleeps. A background layer keeps the wake-word listener and gesture engine running as daemon threads at all times. When "Hey NOVA" is detected, the full voice pipeline activates instantly — no app to open, no button to click. This mirrors how real production voice assistants like Alexa and Google Assistant work at the OS level.

### 2.2 Backend-Heavy, UI-Minimal
Processing intelligence is in the pipeline modules, not the UI. The HUD overlay surfaces only essential status information — last command, last response, status indicator, clock, reminders ticker — and stays out of the way. No bloated GUI, no unnecessary visual noise. This is intentional: it reflects mature software philosophy.

### 2.3 Modular and Extensible
Every one of the 25 modules is independently registered in `config.json`. Features can be toggled on/off. New app shortcuts, websites, and contacts can be added without touching a single line of Python. Hot-reload lets config changes apply while NOVA is running. This architecture demonstrates software engineering maturity.

### 2.4 NLP-First, Groq-Second (Dual-Brain Routing)
Simple, deterministic commands (open Chrome, what time is it, set volume to 60%) are handled by the NLP layer locally in milliseconds with zero API cost. Only complex, conversational, ambiguous, or creative queries escalate to the Groq LLM. This is the core routing philosophy — speed, cost efficiency, and offline capability for common operations.

---

## 3. System Architecture

```
╔══════════════════════════════════════════════════════════════════╗
║                    BACKGROUND LAYER (Always Running)             ║
║                                                                  ║
║   ┌─────────────────────┐    ┌─────────────────────────────┐    ║
║   │  Wake Word Engine   │    │   Hand Gesture Engine       │    ║
║   │  (Module 1)         │    │   (Module 22)               │    ║
║   │  pvporcupine /      │    │   OpenCV + MediaPipe        │    ║
║   │  energy threshold   │    │   21-landmark tracking      │    ║
║   │  daemon thread      │    │   daemon thread             │    ║
║   └────────┬────────────┘    └──────────────┬──────────────┘    ║
║            │ threading.Event                 │ thread-safe queue ║
╚════════════╪═════════════════════════════════╪══════════════════╝
             │ ACTIVATION                      │ OS ACTIONS
             ▼                                 ▼
╔══════════════════════════════════════════════════════════════════╗
║                    PRIMARY PIPELINE                              ║
║                                                                  ║
║   [MIC] → STT (M2) → NLP Engine (M3) ──→ LOCAL MODULES         ║
║                              │             (M5–M19, M21)        ║
║                              │                                   ║
║                              └──→ GROQ LLM (M4)                 ║
║                                    ↓                             ║
║                              EXECUTION + RESPONSE                ║
║                                    ↓                             ║
║                         TTS (pyttsx3 / gTTS)                    ║
║                                    ↓                             ║
╚══════════════════════════════════════════════════════════════════╝
             │
             ▼
╔══════════════════════════════════════════════════════════════════╗
║                    SUPPORT LAYER                                 ║
║                                                                  ║
║   Memory System (M20) │ Activity Log (M24) │ HUD (M23)         ║
║   SQLite memory.db    │ SQLite log.db      │ Tkinter + mpl      ║
║   Config Manager (M25) — config.json hot-reload                 ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 4. Dual-Pipeline Execution Model

NOVA runs two independent execution pipelines simultaneously from the moment it starts.

### 4.1 Background Layer
Always active. Consumes minimal CPU. Houses two daemon threads:

**Wake Word Listener (Module 1):**
- Runs `pvporcupine` offline wake word detection or an energy-threshold keyword scan loop
- Continuously monitors microphone audio at low sample rate
- On "Hey NOVA" detection → fires `threading.Event` to signal the primary pipeline
- Never blocks, never sleeps, never stops unless NOVA is shut down

**Gesture Engine (Module 22):**
- Opens camera via OpenCV, processes frames at ~15–20 FPS
- MediaPipe Hands extracts 21 hand landmarks per frame
- Computes distances, fingertip positions, wrist deltas
- Dispatches OS actions (volume, scroll, media control, tab switch) via thread-safe queue
- Completely independent of voice pipeline — gesture and voice work simultaneously

### 4.2 Primary Pipeline
Activates on wake word detection. Sequence:

```
Wake Event Fired
      ↓
Microphone Capture (SpeechRecognition)
      ↓
Silence Detection → Audio Clip Trimmed
      ↓
Google Web Speech API → Text String
(Whisper local fallback if offline)
      ↓
NLP Intent Engine (spaCy + NLTK)
  → Entity Extraction (city, time, app name, contact)
  → Intent Classification (System / Web / Info / Automation / Memory / Creative / Conversation)
      ↓
ROUTING DECISION:
  ├── Confidence HIGH + Simple Intent → Local Module Handler
  └── Confidence LOW / Complex / Conversational → Groq LLM
      ↓
Module Execution
      ↓
Response Text Generated
      ↓
TTS Engine (pyttsx3 primary, gTTS fallback)
      ↓
HUD Updated (status, last command, last response)
      ↓
Activity Log Written (SQLite)
      ↓
NOVA Returns to Sleeping State
```

---

## 5. Module-by-Module Breakdown

### MODULE 1 — Wake Word Detection
**Purpose:** Keep NOVA always listening with minimal CPU overhead.  
**Tech:** `pvporcupine` (offline, free tier) or `SpeechRecognition` energy threshold scan  
**How it works:** Runs as a background daemon thread. Continuously scans ambient audio energy. On detecting "Hey NOVA", fires a `threading.Event` object that the main pipeline is waiting on. Does not process the actual command — just the trigger word.  
**Thread:** Dedicated daemon thread. Never touches the main thread.  
**Output:** `threading.Event` signal  
**Storage:** None  

---

### MODULE 2 — Speech-to-Text (STT)
**Purpose:** Convert spoken voice command to text string after wake word fires.  
**Tech:** `SpeechRecognition` library with Google Web Speech API backend (free, no key required for basic usage). Offline fallback: `openai-whisper` running locally.  
**How it works:** Captures microphone audio after wake event. `Recognizer.listen()` with configurable `pause_threshold` and `energy_threshold` for Wah Cantt ambient noise conditions. Sends trimmed audio clip to Google Web Speech → returns text. If no internet, Whisper runs locally.  
**Config params:** `energy_threshold`, `pause_threshold` in `config.json`  
**Output:** Plain text string passed to Module 3  
**Storage:** None  

---

### MODULE 3 — NLP Intent Engine
**Purpose:** First brain layer. Classify intent and extract entities from the text command before deciding whether to handle locally or escalate to Groq.  
**Tech:** `spaCy` (fast NER — extracts cities, times, app names, person names, numbers) + `NLTK` (tokenization, stopword removal) + `dateparser` (natural language date/time parsing)  
**Intent categories:**

| Category | Example Commands |
|----------|-----------------|
| System | "shutdown", "restart", "mute", "battery status" |
| Web | "open YouTube", "search Google for X", "open my GitHub" |
| Information | "weather in Islamabad", "tell me about black holes", "NASA news" |
| Automation | "take a screenshot", "type hello", "copy to clipboard" |
| Memory | "remember that my editor is VS Code", "what do you know about me" |
| Creative | "write a poem", "roast me", "tell me a joke" |
| Conversation | "how are you", "what's your name", "explain quantum computing" |

**How it works:** Rule-based pattern matching first (if "weather" in tokens → WeatherModule). spaCy NER extracts payload entities. If intent is clear and simple → routes to local handler. If ambiguous, multi-step, or conversational → routes to Groq.  
**Output:** `(intent_category, entities_dict, confidence_score)` tuple  
**Storage:** None  

---

### MODULE 4 — Groq LLM Brain
**Purpose:** Second brain layer. Handles anything the NLP layer can't — complex queries, email drafting, code explanation, open-ended conversation, creative writing.  
**Tech:** Groq API, LLaMA 3 70B model (free tier, ultra-fast inference — typically <1s response)  
**How it works:**
- Maintains a `conversation_history` list (rolling message array)
- Before each API call: top 10 most relevant memories are pulled from SQLite and injected into the system prompt
- System prompt defines: NOVA's name, personality (professional but friendly), Akif's profile (SE student, Wah Cantt, COMSATS), current date/time
- Response is read back via TTS
- After conversation: Groq auto-extracts key facts and stores them in the memory system

**System prompt structure:**
```
You are NOVA, a voice-controlled AI assistant. You are professional, 
friendly, and concise. The user's name is Akif. Today is {date}. 
Current time: {time}. 
Known facts about Akif: {memory_injection}
```

**Use cases:** Email drafting, Q&A, code explanation, general chat, creative writing, roast mode  
**Storage:** `conversation_log` table in `memory.db`  

---

### MODULE 5 — Weather Information
**Purpose:** Real-time weather for any city by voice.  
**Tech:** OpenWeatherMap API (free tier, 60 calls/min), `requests` library  
**How it works:** NLP extracts city entity from command. If no city mentioned, defaults to Wah Cantt (stored in `config.json`). HTTP GET to OpenWeatherMap → parses temperature, feels-like, humidity, conditions → TTS reads response.  
**Example:** "Weather in Islamabad" → "It's 28°C in Islamabad, feels like 31, humidity 65%, clear skies."  
**Config:** `default_city` in `config.json`, API key in `.env`  
**Storage:** None  

---

### MODULE 6 — Space & Science News
**Purpose:** Daily NASA astronomy picture and science update.  
**Tech:** NASA Open API (APOD endpoint, completely free), `requests`  
**How it works:** Hits `https://api.nasa.gov/planetary/apod` with date param → gets title + explanation → TTS reads it. Optional: RSS parsing for general science news (no API key needed).  
**Example:** "Hey NOVA, NASA news" → reads today's APOD title and explanation  
**Config:** NASA API key in `.env`  
**Storage:** None  

---

### MODULE 7 — Wikipedia Knowledge Base
**Purpose:** Quick factual summaries for "tell me about X" queries.  
**Tech:** `wikipedia` Python library (free, no API key)  
**How it works:** NLP extracts the subject entity. `wikipedia.summary(subject, sentences=3)` returns first 3 sentences. Disambiguation handling: if multiple matches exist, NOVA asks "Did you mean X or Y?"  
**Example:** "Tell me about neural networks" → 3-sentence Wikipedia summary via TTS  
**Storage:** None  

---

### MODULE 8 — Web Automation & Browser Control
**Purpose:** Open websites and perform real browser interactions by voice.  
**Tech:** `webbrowser` (simple URL opens), `selenium` (interactive — click, scroll, comment, search)  
**Sites NOVA can open by voice:**
- GitHub profile, LinkedIn profile
- YouTube, Google, StackOverflow, ChatGPT
- Gmail, Google Drive, WhatsApp Web
- University portal (COMSATS)

**Selenium actions:**
- Like a post on LinkedIn/YouTube
- Comment text on a post
- Scroll up/down on current page
- Search on YouTube and autoplay result

**Config:** `sites.json` stores `name → URL` mappings. Fully extensible without code changes.  
**Storage:** `sites.json`  

---

### MODULE 9 — Application Launcher
**Purpose:** Open any installed Windows application by voice.  
**Tech:** `os`, `subprocess`, `fuzzywuzzy`/`rapidfuzz`  
**Apps registered (default):**
- VS Code, Chrome, Firefox, Notepad, Calculator
- Spotify, VLC Media Player
- File Explorer, Task Manager, Control Panel
- WhatsApp Desktop, Discord, Telegram
- PowerPoint, Word, Excel
- GitHub Desktop, Postman

**How it works:** NLP extracts app name. `fuzzywuzzy.process.extractOne()` finds best match from `apps.json` registry. `subprocess.Popen(executable_path)` launches it.  
**Example:** "Open visual studio" → fuzzy matches "VS Code" → launches `code.exe`  
**Config:** `apps.json` stores `name → executable_path`. User can add any app.  
**Storage:** `apps.json`  

---

### MODULE 10 — Email Compose & Send
**Purpose:** Full voice-driven email workflow — describe → draft → review → send.  
**Tech:** `smtplib` + `email` (Python built-in) for Gmail SMTP sending. Groq API for drafting.  
**Full flow:**
1. "Hey NOVA, write an email to Ali about the project meeting"
2. NOVA asks: "What should the email say?"
3. User describes intent in natural language
4. Groq drafts professional email from description
5. NOVA reads full email back via TTS
6. User says "Send it" or "Edit"
7. If send → `smtplib` sends via Gmail SMTP
8. If edit → re-prompts

**Security:** Gmail App Password stored in `.env` — never hardcoded.  
**Config:** Sender email in `.env`  
**Storage:** `.env` (credentials only)  

---

### MODULE 11 — WhatsApp Messaging
**Purpose:** Send WhatsApp messages by voice.  
**Tech:** `PyWhatKit`  
**How it works:** NLP extracts contact name and message. Looks up phone number from `contacts.json`. `PyWhatKit.sendwhatmsg()` opens WhatsApp Web in Chrome, navigates to contact, types message, sends.  
**Limitation:** Requires active Chrome session with WhatsApp Web logged in.  
**Example:** "Send a WhatsApp to Mama saying I'll be home by 8"  
**Config:** `contacts.json` stores `name → phone_number`  
**Storage:** `contacts.json`  

---

### MODULE 12 — Music & Media Control
**Purpose:** Play YouTube content or local music, control playback by voice.  
**Tech:** `PyWhatKit` (YouTube), `subprocess` + VLC (local files), `pyautogui` (playback shortcuts)  
**Commands:**
- "Play lo-fi hip hop on YouTube" → `PyWhatKit.playonyt()`
- "Play my playlist" → opens local music folder in VLC
- "Pause / resume / next / previous" → `pyautogui` keyboard shortcuts
- "Play [song name]" → YouTube search + autoplay

**Storage:** None  

---

### MODULE 13 — Notes & Reminders
**Purpose:** Save voice notes and set timed reminder alerts.  
**Tech:** `sqlite3`, `dateparser`  
**How it works:**
- Notes: NLP detects "take a note" → extracts note body → stores in `notes` table in `memory.db`
- Reminders: NLP detects "remind me at 5 PM" → `dateparser` converts natural language to datetime → stores in `reminders` table
- Reminder engine: background thread checks `reminders` table every 60 seconds → triggers TTS alert when time matches

**Example:** "Set a reminder for 10 PM to submit the assignment" → stored with datetime → fires at 10 PM  
**Storage:** `memory.db` — `notes` and `reminders` tables  

---

### MODULE 14 — Calendar & Task Scheduling
**Purpose:** Voice-driven calendar events and to-do list management.  
**Tech:** `sqlite3`, `dateparser`  
**Commands:**
- "Add event: AI class on Monday at 9 AM" → stores in `events` table
- "What do I have tomorrow?" → queries events by date → TTS reads list
- "Add to my task list: finish the NOVA project" → stores in `tasks` table
- "Mark task X as done" → updates `status` column

**HUD:** Upcoming events shown in reminders ticker on startup.  
**Storage:** `memory.db` — `events` and `tasks` tables  

---

### MODULE 15 — Date, Time & Math
**Purpose:** Instant answers for time, date, and arithmetic queries.  
**Tech:** `datetime` (built-in), `eval()` with sandboxed execution for math  
**Commands:**
- "What time is it?" → `datetime.now().strftime()`
- "What's today's date?" → formatted date string
- "How many days until 25th December?" → `timedelta` calculation
- "What is 847 divided by 13?" → sandboxed `eval()`

**Routing:** Always NLP — never Groq. Zero API calls for these.  
**Storage:** None  

---

### MODULE 16 — System Controls
**Purpose:** Full OS-level control by voice.  
**Tech:** `pycaw` (Windows audio API), `screen_brightness_control`, `psutil`, `os`  
**Commands:**
- "Set volume to 60%" → `pycaw` sets Windows master volume
- "Mute / unmute" → toggle mute state
- "Increase / decrease brightness" → `screen_brightness_control`
- "Shutdown / restart / sleep" → `os.system()` calls
- "Lock screen" → `os.system("rundll32.exe user32.dll,LockWorkStation")`
- "Battery status" → `psutil.sensors_battery()`
- "CPU usage / RAM usage" → `psutil.cpu_percent()`, `psutil.virtual_memory()`

**Storage:** None  

---

### MODULE 17 — Screenshot & Screen Automation
**Purpose:** Screenshot capture and cursor-based screen interaction.  
**Tech:** `pyautogui`, `Pillow`  
**Commands:**
- "Take a screenshot" → `pyautogui.screenshot()` → saves as `screenshot_YYYYMMDD_HHMMSS.png` to Desktop
- "Click the top right of the screen" → `pyautogui.click(x, y)` with NLP coordinate inference
- "Type hello world" → `pyautogui.typewrite()` at current cursor position

**Storage:** Desktop folder (screenshots)  

---

### MODULE 18 — Clipboard Manager
**Purpose:** Voice control over Windows clipboard.  
**Tech:** `pyperclip`  
**Commands:**
- "What's in my clipboard?" → `pyperclip.paste()` → TTS reads content
- "Copy [text] to clipboard" → `pyperclip.copy(text)`
- "Read what I copied" → same as first command

**Storage:** None (clipboard is OS-managed)  

---

### MODULE 19 — Language Translation
**Purpose:** Translate any text to any language by voice.  
**Tech:** `deep-translator` (free, no API key for GoogleTranslator backend)  
**Commands:**
- "Translate 'how are you' to Arabic"
- "What does 'hola' mean in English?"
- "Translate this to French: [text]"

**How it works:** NLP extracts source text and target language. `GoogleTranslator(source='auto', target='arabic').translate(text)` → TTS reads result.  
**Storage:** None  

---

### MODULE 20 — Memory System
**Purpose:** NOVA remembers facts about Akif, preferences, contacts, and conversation history across sessions.  
**Tech:** `sqlite3`, Groq API (for auto-extraction)  
**SQLite Schema (memory.db) — 8 tables:**

| Table | Columns | Purpose |
|-------|---------|---------|
| `user_facts` | id, key, value, timestamp | Persistent facts about Akif |
| `conversation_log` | id, role, content, timestamp | Full Groq conversation history |
| `notes` | id, content, timestamp | Voice notes |
| `reminders` | id, content, datetime, fired | Timed reminders |
| `events` | id, title, event_datetime, location | Calendar events |
| `tasks` | id, title, status, created_at | To-do tasks |
| `activity_log` | id, command, response, timestamp | All NOVA command history |
| `contacts` | id, name, phone, email | Contact book |

**How memory injection works:**
1. At each Groq call, query `user_facts` for top 10 most relevant rows
2. Inject as context into Groq system prompt
3. After Groq conversation ends, call Groq again with: "Extract any new facts about the user from this conversation and return as JSON key-value pairs"
4. Store extracted facts in `user_facts` table

**Startup greeting uses memory:** "Good evening Akif! It's 9 PM, you have 3 notes and a reminder at 10 PM."  
**Storage:** `memory.db`  

---

### MODULE 21 — Personality, Jokes & Small Talk
**Purpose:** Give NOVA a real character — not a cold command processor.  
**Tech:** `pyjokes` (offline joke library), Groq API (for banter, motivation, roast mode)  
**Features:**
- "Tell me a joke" → `pyjokes.get_joke()` (offline, instant)
- "How are you?" → Groq generates friendly in-character response
- "Motivate me" → Groq generates motivational content
- "Roast me" → Groq generates friendly roast (optional fun feature)
- Startup greeting: time-aware + memory-aware personalized greeting

**Routing:** Simple jokes → pyjokes (NLP). Open-ended banter → Groq.  
**Storage:** None  

---

### MODULE 22 — Hand Gesture Control ⭐
**Purpose:** Always-on, vision-based OS control — completely parallel to voice.  
**Tech:** `OpenCV` (camera capture + frame processing), `MediaPipe Hands` (21-landmark skeletal tracking), `pycaw` (volume control), `pyautogui` (scroll, zoom, tab)  

**How it works:**
- Dedicated daemon thread captures frames from webcam via OpenCV
- MediaPipe processes each frame → returns 21 hand landmark (x, y, z) coordinates
- Custom logic computes: fingertip positions relative to knuckles (finger up/down), Euclidean distance between landmarks 4 (thumb tip) and 8 (index tip), wrist x-delta between frames (swipe detection)
- Results dispatched via thread-safe `queue.Queue` to avoid race conditions with voice pipeline

**Volume control (continuous):**
- Distance between landmark 4 (thumb tip) and landmark 8 (index tip) mapped linearly to 0–100% volume
- Small distance = low volume, large distance = high volume
- Real-time, smooth — not discrete steps

**Discrete gesture map:**

| Gesture | Detection Logic | OS Action |
|---------|----------------|-----------|
| Open palm | All 5 fingertips above knuckles | Play / resume media |
| Closed fist | All fingers curled | Pause media |
| Index finger up | Only index extended | Volume up +5% |
| Index + middle up | Two fingers extended | Scroll up |
| Three fingers up | Three fingers extended | Scroll down |
| Pinch | Landmark 4–8 distance < 30px | Zoom in |
| OK sign | Thumb + index touching, others up | Next browser tab |
| Swipe left | Wrist x-delta > threshold (left) | Previous track |
| Swipe right | Wrist x-delta > threshold (right) | Next track |

**Debounce:** Gesture must hold for 0.4 seconds before action fires. Prevents accidental triggers from transitional hand positions.  
**Performance:** ~15–20 FPS. Minimal CPU impact on voice pipeline.  
**HUD display:** Optional small corner feed showing live camera with MediaPipe skeleton overlay + detected gesture label.  
**Storage:** None  

---

### MODULE 23 — HUD Interface
**Purpose:** NOVA's visual face — minimal, always-on-top dark overlay docked to the right side of the screen.  
**Tech:** `Tkinter` (frameless window management), `matplotlib` (animated waveform via `FuncAnimation`)  

**Window properties:**
- Frameless (no title bar, no borders)
- Always-on-top: `root.wm_attributes('-topmost', True)`
- Semi-transparent: `root.wm_attributes('-alpha', 0.92)`
- Right-docked, full screen height, 320px wide
- Background: `#0D0D0D`

**HUD panels (top to bottom):**
1. **Logo + Waveform Zone:** Animated NOVA SVG mark with matplotlib circular waveform overlaid. Waveform bars pulse based on NOVA state. Clicking activates NOVA manually.
2. **Status Indicator:** `● SLEEPING` / `● LISTENING` / `● PROCESSING` / `● SPEAKING` with state-colored dots
3. **Live Clock:** HH:MM:SS in cyan `#00D4FF`, updates every second
4. **Command/Response Panel:** Last 5 command-response pairs (user command in lavender, NOVA response in cyan)
5. **Reminders Ticker:** Scrolling horizontal ticker of upcoming reminders in teal `#5DCAA5`
6. **Gesture Cam Feed:** Optional 280×160 live camera feed with landmark overlay (toggle in config)

**Waveform states:**

| State | Behavior | Color |
|-------|----------|-------|
| Sleeping | Near-flat, very slow pulse | `#7B6CF6` at 30% |
| Listening | Medium amplitude, rapid random bars | `#00D4FF` at 85% |
| Processing | Slow rotating sweep | `#5DCAA5` at 70% |
| Speaking | High amplitude, driven by TTS | `#00D4FF` at 100% |

**Color scheme:** `#0D0D0D` background, `#00D4FF` cyan accent, `#7B6CF6` violet, `#A89AF8` lavender, `#5DCAA5` teal. Monospace font throughout.  

---

### MODULE 24 — Activity Log & History
**Purpose:** Every command NOVA processes is logged with timestamp and result.  
**Tech:** `sqlite3`  
**How it works:** After every command execution, regardless of which module handled it, a row is written to `activity_log` table in `activity_log.db` with: timestamp, raw command text, NOVA's response text, and which module handled it.  
**Auto-cleanup:** Rows older than 30 days are automatically deleted on startup to keep DB lean.  
**Voice query:** "What did I ask you earlier?" → reads last 5 entries. "Show me today's log" → reads all commands from today.  
**Storage:** `activity_log.db`  

---

### MODULE 25 — Plugin / Config Manager
**Purpose:** Central control panel for NOVA's behavior. Enable/disable modules, add shortcuts, hot-reload without restart.  
**Tech:** `json` (built-in), file watcher or manual reload via voice command  
**How it works:** At startup, NOVA loads `config.json`. All module-level settings, toggles, and defaults come from this file. When Akif says "Hey NOVA, reload config" — the file is re-read and all settings update live.  
**Why this matters architecturally:** Demonstrates mature software design. New apps, websites, and contacts can be added by editing JSON files — no Python knowledge required. Shows understanding of configuration-driven architecture.  
**Storage:** `config.json`, `apps.json`, `sites.json`, `contacts.json`  

---

## 6. How Everything Communicates

### 6.1 Thread Communication
All background threads communicate with the main pipeline via Python's built-in thread-safe primitives:

| From | To | Mechanism |
|------|----|-----------|
| Wake Word thread | Main pipeline | `threading.Event.set()` |
| Gesture engine thread | OS action dispatcher | `queue.Queue.put()` |
| Reminder checker thread | TTS engine | `queue.Queue.put()` |
| HUD update | Main pipeline | Shared state variable + `tkinter.after()` |

No shared mutable state without locks. No direct cross-thread function calls.

### 6.2 Module Communication
Modules do not call each other directly. They communicate through the central `nova_core.py` orchestrator:

```
voice_text → nova_core.route(text)
                  ↓
          NLP Engine → (intent, entities, confidence)
                  ↓
          Router selects module
                  ↓
          module.handle(entities) → response_text
                  ↓
          TTS.speak(response_text)
          HUD.update(command, response)
          ActivityLog.write(command, response)
```

### 6.3 Memory Flow
```
Groq conversation ends
         ↓
MemorySystem.extract_facts(conversation_history)
  → calls Groq: "Extract key facts as JSON"
  → parses JSON response
  → writes to user_facts table
         ↓
Next Groq call:
  MemorySystem.get_relevant_facts(query, top_k=10)
  → injected into system prompt
```

### 6.4 Config Flow
```
startup → ConfigManager.load('config.json')
        → all modules receive their settings dict

runtime → "Hey NOVA, reload config"
        → ConfigManager.reload()
        → all modules re-read their settings
        → no restart required
```

---

## 7. Complete Tech Stack

| Category | Tool / Library | Version / Tier | Why |
|----------|---------------|----------------|-----|
| Language | Python | 3.11 (Windows) | Required |
| Wake Word | pvporcupine | Free tier | Offline wake word |
| Wake Word Fallback | SpeechRecognition energy threshold | Free | No key needed |
| STT | SpeechRecognition + Google Web Speech | Free | No key for basic use |
| STT Fallback | openai-whisper | Local, free | Offline privacy mode |
| NLP | spaCy | Free | Fast NER |
| NLP | NLTK | Free | Tokenization, stopwords |
| Date Parsing | dateparser | Free | Natural language dates |
| LLM | Groq API (LLaMA 3 70B) | Free tier | Fast, smart, free |
| TTS Primary | pyttsx3 | Free, offline | No internet needed |
| TTS Fallback | gTTS | Free, online | Better voice quality |
| Gesture Vision | OpenCV | Free | Camera capture |
| Gesture Vision | MediaPipe Hands | Free | 21-point hand tracking |
| Weather | OpenWeatherMap API | Free tier | Real-time weather |
| News | NASA Open API | Free | APOD endpoint |
| Knowledge | wikipedia (Python) | Free | No key needed |
| Web Automation | selenium | Free | Browser interaction |
| Web Automation | webbrowser | Built-in | Simple URL opens |
| Messaging | PyWhatKit | Free | WhatsApp + YouTube |
| System Audio | pycaw | Free, Windows | Windows audio API |
| System Info | psutil | Free | CPU, RAM, battery |
| Brightness | screen-brightness-control | Free, Windows | Monitor brightness |
| Screen Auto | pyautogui | Free | Click, type, screenshot |
| Clipboard | pyperclip | Free | Read/write clipboard |
| Translation | deep-translator | Free | No key for Google backend |
| Email | smtplib + email | Built-in | Gmail SMTP |
| Fuzzy Match | fuzzywuzzy / rapidfuzz | Free | App name matching |
| Jokes | pyjokes | Free, offline | Instant humor |
| Database | sqlite3 | Built-in | Persistent storage |
| HUD UI | Tkinter | Built-in | Frameless window |
| Waveform | matplotlib | Free | FuncAnimation |
| Config | json | Built-in | Config files |
| Secrets | python-dotenv | Free | .env API key management |
| Threading | threading | Built-in | Daemon threads |

**Total paid tools: 0. Total cloud dependencies: 0 (all can run offline with fallbacks).**

---

## 8. JSON Config Contracts

### 8.1 `config.json` — Master Control

```json
{
  "nova": {
    "name": "NOVA",
    "wake_phrase": "Hey NOVA",
    "user_name": "Akif",
    "language": "en"
  },
  "stt": {
    "engine": "google",
    "fallback": "whisper",
    "energy_threshold": 300,
    "pause_threshold": 0.8,
    "phrase_threshold": 0.3
  },
  "tts": {
    "engine": "pyttsx3",
    "fallback": "gtts",
    "rate": 175,
    "volume": 0.9,
    "voice_index": 0
  },
  "modules": {
    "wake_word": true,
    "stt": true,
    "nlp": true,
    "groq": true,
    "weather": true,
    "news": true,
    "wikipedia": true,
    "web_automation": true,
    "app_launcher": true,
    "email": true,
    "whatsapp": true,
    "music": true,
    "notes": true,
    "calendar": true,
    "datetime_math": true,
    "system_controls": true,
    "screenshot": true,
    "clipboard": true,
    "translation": true,
    "memory": true,
    "personality": true,
    "gesture_control": true,
    "hud": true,
    "activity_log": true,
    "config_manager": true
  },
  "weather": {
    "default_city": "Wah Cantt",
    "units": "metric"
  },
  "hud": {
    "width": 320,
    "alpha": 0.92,
    "dock": "right",
    "gesture_cam_feed": true,
    "waveform_bars": 64,
    "waveform_fps": 20
  },
  "gesture": {
    "camera_index": 0,
    "fps_target": 20,
    "debounce_seconds": 0.4,
    "pinch_threshold_px": 30
  },
  "memory": {
    "db_path": "data/memory.db",
    "top_k_injection": 10,
    "log_retention_days": 30
  },
  "groq": {
    "model": "llama3-70b-8192",
    "max_tokens": 1024,
    "temperature": 0.7,
    "conversation_window": 20
  }
}
```

---

### 8.2 `apps.json` — Application Registry

```json
{
  "apps": [
    { "name": "VS Code", "aliases": ["visual studio code", "vscode", "code"], "path": "C:\\Users\\Akif\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe" },
    { "name": "Chrome", "aliases": ["google chrome", "browser", "chrome"], "path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" },
    { "name": "Firefox", "aliases": ["firefox", "mozilla"], "path": "C:\\Program Files\\Mozilla Firefox\\firefox.exe" },
    { "name": "Notepad", "aliases": ["notepad", "text editor"], "path": "notepad.exe" },
    { "name": "Calculator", "aliases": ["calculator", "calc"], "path": "calc.exe" },
    { "name": "Spotify", "aliases": ["spotify", "music app"], "path": "C:\\Users\\Akif\\AppData\\Roaming\\Spotify\\Spotify.exe" },
    { "name": "VLC", "aliases": ["vlc", "media player", "vlc player"], "path": "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe" },
    { "name": "File Explorer", "aliases": ["explorer", "file manager", "files"], "path": "explorer.exe" },
    { "name": "Task Manager", "aliases": ["task manager", "processes"], "path": "taskmgr.exe" },
    { "name": "Discord", "aliases": ["discord"], "path": "C:\\Users\\Akif\\AppData\\Local\\Discord\\Update.exe" },
    { "name": "PowerPoint", "aliases": ["powerpoint", "presentation", "slides"], "path": "C:\\Program Files\\Microsoft Office\\root\\Office16\\POWERPNT.EXE" },
    { "name": "Word", "aliases": ["word", "microsoft word", "document"], "path": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE" },
    { "name": "Excel", "aliases": ["excel", "spreadsheet"], "path": "C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE" },
    { "name": "Postman", "aliases": ["postman", "api client"], "path": "C:\\Users\\Akif\\AppData\\Local\\Postman\\Postman.exe" }
  ]
}
```

---

### 8.3 `sites.json` — Website Registry

```json
{
  "sites": [
    { "name": "GitHub", "aliases": ["github", "my github", "github profile"], "url": "https://github.com/akifnaveed" },
    { "name": "LinkedIn", "aliases": ["linkedin", "my linkedin"], "url": "https://linkedin.com/in/akifnaveed" },
    { "name": "YouTube", "aliases": ["youtube", "yt"], "url": "https://youtube.com" },
    { "name": "Google", "aliases": ["google", "search"], "url": "https://google.com" },
    { "name": "StackOverflow", "aliases": ["stackoverflow", "stack overflow"], "url": "https://stackoverflow.com" },
    { "name": "ChatGPT", "aliases": ["chatgpt", "gpt", "openai"], "url": "https://chat.openai.com" },
    { "name": "Gmail", "aliases": ["gmail", "email", "mail"], "url": "https://mail.google.com" },
    { "name": "Google Drive", "aliases": ["drive", "google drive"], "url": "https://drive.google.com" },
    { "name": "WhatsApp Web", "aliases": ["whatsapp web", "whatsapp"], "url": "https://web.whatsapp.com" },
    { "name": "University Portal", "aliases": ["university", "comsats portal", "student portal"], "url": "https://cuonline.edu.pk" }
  ]
}
```

---

### 8.4 `contacts.json` — Contact Book

```json
{
  "contacts": [
    { "name": "Mama", "aliases": ["mama", "mom", "mother"], "phone": "+92300XXXXXXX" },
    { "name": "Baba", "aliases": ["baba", "dad", "father"], "phone": "+92300XXXXXXX" },
    { "name": "Ali", "aliases": ["ali"], "phone": "+92300XXXXXXX", "email": "ali@example.com" }
  ]
}
```

---

### 8.5 `.env` — Secrets (Never Committed to Git)

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
OPENWEATHER_API_KEY=xxxxxxxxxxxxxxxxxxxx
NASA_API_KEY=xxxxxxxxxxxxxxxxxxxx
GMAIL_SENDER=akif@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

---

## 9. Database Schema

### `memory.db` — 7 Tables

```sql
CREATE TABLE user_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,          -- 'user' or 'assistant'
    content TEXT NOT NULL,
    session_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    remind_at TIMESTAMP NOT NULL,
    fired INTEGER DEFAULT 0,     -- 0 = pending, 1 = fired
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    event_datetime TIMESTAMP NOT NULL,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending' | 'done'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `activity_log.db` — 1 Table

```sql
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command TEXT NOT NULL,
    response TEXT,
    module_handled TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Auto-purge: DELETE FROM activity_log WHERE timestamp < datetime('now', '-30 days');
```

---

## 10. Routing Logic — NLP vs Groq

The routing decision is made by the NLP engine after intent classification:

```
Input text arrives from STT
         ↓
spaCy NER extracts entities (city, name, time, app)
NLTK tokenizes and removes stopwords
Rule-based patterns check intent keywords
         ↓
confidence_score = match_strength(intent_rules, tokens)

if confidence_score >= 0.75 AND intent in LOCAL_INTENTS:
    → route to local module handler (milliseconds, free)

elif confidence_score < 0.75 OR intent in GROQ_INTENTS:
    → route to Groq LLM (1–2 seconds, API call)
```

**LOCAL_INTENTS (NLP handles):** weather, news, wikipedia, app_launch, web_open, system_control, screenshot, clipboard, music, notes, reminders, calendar, datetime, math, translation, whatsapp, email_send

**GROQ_INTENTS (always Groq):** email_draft, general_conversation, creative_writing, code_explanation, complex_qa, personality, memory_extraction

**Always Groq escalation:** If NLP confidence < 0.75 on any intent, regardless of category.

---

## 11. Thread Architecture

NOVA runs 4 concurrent threads:

| Thread | Type | Purpose | Communication |
|--------|------|---------|---------------|
| `main` | Main thread | Primary pipeline + HUD | Owns Tkinter mainloop |
| `wake_word_thread` | Daemon | "Hey NOVA" detection | `threading.Event` |
| `gesture_thread` | Daemon | Camera + MediaPipe | `queue.Queue` |
| `reminder_thread` | Daemon | Reminder checker (60s poll) | `queue.Queue` |

All daemon threads terminate automatically when main thread exits. No manual cleanup needed.

---

## 12. End-to-End Command Flow

**Example: "Hey NOVA, send a WhatsApp to Ali saying I'll be home by 8"**

```
1. [gesture_thread]    Running in background — not relevant here
2. [wake_word_thread]  Detects "Hey NOVA" → fires threading.Event
3. [main]              Event received → HUD status: LISTENING
4. [main/STT M2]       Captures "send a WhatsApp to Ali saying I'll be home by 8"
                       Google Web Speech → text string returned
5. [main/NLP M3]       spaCy NER:
                         contact = "Ali"
                         message = "I'll be home by 8"
                       Intent = "whatsapp_message", confidence = 0.92
6. [main/Router]       0.92 > 0.75 AND intent in LOCAL_INTENTS
                       → route to Module 11 (WhatsApp)
7. [main/M11]          HUD status: PROCESSING
                       contacts.json lookup: Ali → +923XXXXXXXXX
                       PyWhatKit.sendwhatmsg("+923XXXXXXXXX", "I'll be home by 8", ...)
8. [main/TTS]          "Message sent to Ali."
                       HUD status: SPEAKING → waveform high amplitude
9. [main/M24]          ActivityLog.write("send whatsapp to ali...", "Message sent to Ali.", "whatsapp")
10. [main]             HUD status: SLEEPING → waveform near-flat
```

---

## 13. Project Folder Structure

```
nova-ai/
│
├── main.py                          # Entry point — starts all threads, launches HUD
├── nova_core.py                     # Central orchestrator — routing logic
├── .env                             # API keys and secrets (git-ignored)
├── config.json                      # Master config (hot-reload capable)
├── apps.json                        # App registry
├── sites.json                       # Website registry
├── contacts.json                    # Contact book
├── requirements.txt                 # All pip dependencies
├── design.md                        # UI/UX design specification
├── idea.md                          # This file — full project reference
├── context.md                       # Development changelog
│
├── modules/
│   ├── __init__.py
│   ├── wake_word.py                 # Module 1
│   ├── stt.py                       # Module 2
│   ├── nlp_engine.py                # Module 3
│   ├── groq_brain.py                # Module 4
│   ├── weather.py                   # Module 5
│   ├── news.py                      # Module 6
│   ├── wikipedia_module.py          # Module 7
│   ├── web_automation.py            # Module 8
│   ├── app_launcher.py              # Module 9
│   ├── email_module.py              # Module 10
│   ├── whatsapp_module.py           # Module 11
│   ├── music_module.py              # Module 12
│   ├── notes_reminders.py           # Module 13
│   ├── calendar_tasks.py            # Module 14
│   ├── datetime_math.py             # Module 15
│   ├── system_controls.py           # Module 16
│   ├── screenshot_screen.py         # Module 17
│   ├── clipboard_module.py          # Module 18
│   ├── translation_module.py        # Module 19
│   ├── memory_system.py             # Module 20
│   ├── personality.py               # Module 21
│   ├── gesture_engine.py            # Module 22
│   ├── hud.py                       # Module 23
│   ├── activity_log.py              # Module 24
│   └── config_manager.py            # Module 25
│
├── ui/
│   ├── waveform.py                  # Matplotlib circular waveform component
│   ├── ticker.py                    # Scrolling reminders ticker
│   └── logo_renderer.py            # SVG logo render helper
│
├── data/
│   ├── memory.db                    # SQLite — notes, reminders, events, tasks, facts
│   └── activity_log.db             # SQLite — command history
│
└── assets/
    └── logo/
        ├── nova_logo_animated.svg
        ├── nova_icon_circle.svg
        ├── nova_icon_rounded.svg
        ├── nova_lockup_dark.svg
        └── nova_lockup_light.svg
```

---

## 14. Scope & Boundaries

### In Scope (We Build This)
- All 25 modules described above
- Windows 10/11 only
- Python 3.11, all free tools
- English voice input, any language translation output
- Fully local execution — no cloud hosting, no server, no mobile

### Out of Scope (Explicitly Deferred)
- Face recognition or user identification by voice tone
- Custom wake-word training/enrollment
- Linux and macOS support
- Real-time video call integration
- Mobile companion app
- Paid APIs or subscriptions of any kind

---

## 15. End Goal

NOVA AI's objective at the end of the semester is a **fully integrated, demo-ready AI voice assistant** that:

1. Wakes on "Hey NOVA" with zero manual intervention
2. Understands natural English commands and routes them intelligently
3. Controls the OS, applications, browser, and system settings entirely by voice
4. Handles email drafting, WhatsApp messaging, and media playback
5. Answers questions using Wikipedia, NASA API, and Groq LLM
6. Remembers facts across sessions via SQLite
7. Responds to hand gestures independently of voice (parallel thread)
8. Displays a professional, animated HUD with real-time waveform
9. Can be configured and extended without touching code

The presentation to the course representative will demonstrate all 25 modules live, highlight the dual-brain routing architecture (NLP-first, Groq-second), the gesture engine's independence from voice, and the modular design philosophy — collectively making the case that NOVA is not just a project, but a production-worthy AI system design.

---

## Context.md Entry — idea.md

```
FILE: idea.md
ACTION: Created (new file)
LOCATION: Project root
CHANGE: Full project idea and system reference document created. Covers project
        overview, design philosophy, dual-pipeline architecture, all 25 modules
        in detail, inter-module communication, complete tech stack, all JSON
        config contracts with schemas, SQLite database schema (8 tables),
        NLP vs Groq routing logic, thread architecture (4 threads), end-to-end
        command flow walkthrough, full folder structure, scope boundaries, end goal.
BEFORE: File did not exist
AFTER: Single authoritative reference for the entire NOVA AI project
REASON: Needed one document that captures every finalized decision — modules,
        tech, schemas, configs, flows — to guide consistent implementation
        across all 25 modules and serve as project memory for the team
```