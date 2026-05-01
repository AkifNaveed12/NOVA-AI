# NOVA AI — Master Development Plan
> **Neural Orchestrated Voice Assistant with Autonomous Intelligence**
> 4-Week | 28-Day Implementation Roadmap | Task-Level Breakdown

---

## Legend
| Symbol | Meaning |
|--------|---------|
| `T0` | Pre-requisites — installs, API keys, file creation, repo pull |
| `T1–Tn` | Implementation tasks in order |
| `TEST` | Test cases to verify before git push |
| `PUSH` | Daily git commit + push protocol |

**Daily Workflow:** Plan → T0 → T1…Tn → TEST → PUSH

---

---

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WEEK 1 — Foundation & Core Voice Pipeline
# Days 1–7
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

---

## DAY 1 — Dev Environment + Repository Setup

**Goal:** Full project scaffold live on GitHub. Every teammate can clone and run.

### T0 — Prerequisites
- [ ] Install Python 3.11 from python.org (verify `python --version`)
- [ ] Install Git for Windows; configure `git config --global user.name` and `user.email`
- [ ] Create GitHub repo `nova-ai` (public, add README, .gitignore Python)
- [ ] Clone repo locally: `git clone https://github.com/<username>/nova-ai.git`
- [ ] Install VS Code + Python extension

### T1 — Create Project Folder Structure
Create the following directory tree exactly as finalized:
```
nova-ai/
├── main.py
├── .env
├── .env.example
├── config.json
├── requirements.txt
├── README.md
├── planning.md
├── architecture.md
├── context.md
├── data/
│   └── memory.db          # created at runtime
├── config/
│   ├── apps.json
│   ├── sites.json
│   └── contacts.json
├── modules/
│   ├── __init__.py
│   ├── wake_word.py
│   ├── stt.py
│   ├── nlp_engine.py
│   ├── groq_brain.py
│   ├── weather.py
│   ├── news.py
│   ├── wikipedia_module.py
│   ├── web_automation.py
│   ├── app_launcher.py
│   ├── email_module.py
│   ├── whatsapp_module.py
│   ├── music_module.py
│   ├── notes_reminders.py
│   ├── calendar_tasks.py
│   ├── datetime_calc.py
│   ├── system_controls.py
│   ├── screenshot_tools.py
│   ├── clipboard_manager.py
│   ├── translation.py
│   ├── memory_system.py
│   ├── personality.py
│   ├── gesture_engine.py
│   ├── hud_interface.py
│   ├── activity_log.py
│   └── config_manager.py
├── assets/
│   └── nova_logo.png
└── tests/
    └── test_all.py
```

### T2 — Create `.env.example` and `.env`
```
GROQ_API_KEY=your_groq_api_key_here
OPENWEATHER_API_KEY=your_openweather_key_here
NASA_API_KEY=DEMO_KEY
GMAIL_ADDRESS=your_gmail@gmail.com
GMAIL_APP_PASSWORD=your_app_password_here
DEFAULT_CITY=Wah Cantt
USER_NAME=Akif
```
- Copy `.env.example` → `.env`, fill real values
- Add `.env` to `.gitignore` (never commit secrets)

### T3 — Create `config.json` Scaffold
```json
{
  "user": { "name": "Akif", "default_city": "Wah Cantt" },
  "modules": {
    "wake_word": true, "stt": true, "nlp": true,
    "groq": true, "weather": true, "news": true,
    "wikipedia": true, "web_automation": true,
    "app_launcher": true, "email": true, "whatsapp": true,
    "music": true, "notes": true, "calendar": true,
    "datetime": true, "system_controls": true,
    "screenshot": true, "clipboard": true,
    "translation": true, "memory": true,
    "personality": true, "gesture": true,
    "hud": true, "activity_log": true
  },
  "tts": { "engine": "pyttsx3", "rate": 175, "volume": 1.0 },
  "stt": { "pause_threshold": 0.8, "energy_threshold": 300 }
}
```

### T4 — Create `apps.json` and `sites.json`
**apps.json:** Map friendly names to Windows executable paths for VS Code, Chrome, Firefox, Notepad, Calculator, Spotify, VLC, File Explorer, Task Manager, Control Panel, WhatsApp, Discord, Telegram, PowerPoint, Word, Excel, GitHub Desktop, Postman.

**sites.json:** Map friendly names to URLs for GitHub, LinkedIn, YouTube, Google, StackOverflow, ChatGPT, Gmail, Google Drive, WhatsApp Web, university portal.

**contacts.json:** Empty array `[]` — will be populated by voice commands.

### T5 — Create `requirements.txt` with Pinned Versions
```
SpeechRecognition==3.10.4
pyaudio==0.2.14
pvporcupine==3.0.2
openai-whisper==20231117
spacy==3.7.4
nltk==3.8.1
groq==0.8.0
requests==2.31.0
python-dotenv==1.0.1
pyttsx3==2.90
gTTS==2.5.1
opencv-python==4.9.0.80
mediapipe==0.10.11
selenium==4.18.1
pywhatkit==5.4
pycaw==20230625
psutil==5.9.8
screen-brightness-control==0.23.0
pyautogui==0.9.54
Pillow==10.2.0
pyperclip==1.8.2
deep-translator==1.11.4
fuzzywuzzy==0.18.0
rapidfuzz==3.6.2
dateparser==1.2.0
pyjokes==0.6.0
matplotlib==3.8.3
wikipedia==1.4.0
```

### T6 — Create Stub `main.py`
```python
# main.py — NOVA AI Entry Point
from dotenv import load_dotenv
load_dotenv()

def main():
    print("NOVA AI — Initializing...")
    # Module imports will be added each day

if __name__ == "__main__":
    main()
```

### T7 — Create `context.md` file
Add first entry:
```
## Day 1 — Project Scaffold
- Created full folder structure (25 modules + config + data)
- Added .env, config.json, apps.json, sites.json, contacts.json
- Pinned requirements.txt with all 25+ dependencies
- main.py stub created
```

### TEST — Day 1
- [ ] `python main.py` runs without error
- [ ] All folders and files exist as per structure
- [ ] `.env` is in `.gitignore` and not tracked by git
- [ ] `git status` shows clean working tree after commit

### PUSH
```bash
git add .
git commit -m "Day 1: Project scaffold — folder structure, config, requirements"
git push origin main
```

---

## DAY 2 — Module 1 (Wake Word) + Module 2 (STT)

**Goal:** NOVA listens passively. On "Hey NOVA", it wakes and converts the next spoken sentence to text.

**Modules:** `wake_word.py`, `stt.py`
**Stack:** `SpeechRecognition`, `pvporcupine` (or energy-threshold fallback), `threading`, `Whisper` (offline fallback)

### T0 — Prerequisites
- [ ] `pip install SpeechRecognition pyaudio pvporcupine openai-whisper`
- [ ] Test mic works: `python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"`
- [ ] Get Porcupine access key from picovoice.ai (free tier)
- [ ] Add `PORCUPINE_ACCESS_KEY=` to `.env`
- [ ] Open `modules/wake_word.py` and `modules/stt.py`

### T1 — Implement `wake_word.py`
- Import `pvporcupine`, `pyaudio`, `threading`, `threading.Event`
- Create `WakeWordDetector` class
- `__init__`: load Porcupine with `hey nova` keyword, init PyAudio stream
- `_listen_loop()`: continuous audio frame read → porcupine.process() → on detection, set `threading.Event`
- `start()`: launch `_listen_loop` as daemon thread
- `stop()`: cleanup porcupine + pyaudio
- Energy-threshold fallback: if pvporcupine import fails, use `SpeechRecognition` with keyword spotting loop

### T2 — Implement `stt.py`
- Import `speech_recognition as sr`, `whisper`
- Create `SpeechToText` class
- `__init__`: init `sr.Recognizer()`, load Whisper model `"base"` as fallback
- `listen()`: open mic → `recognizer.listen()` with `pause_threshold` and `energy_threshold` from config → return audio clip
- `transcribe(audio)`: try Google Web Speech → on `RequestError` fallback to Whisper local transcription
- Return clean text string or `None` on failure
- Log failed transcriptions

### T3 — Wire into `main.py`
- Import `WakeWordDetector`, `SpeechToText`
- In `main()`: start wake word thread → `wake_event.wait()` → call `stt.listen()` → `stt.transcribe()` → print result
- Loop: after transcription, reset event and resume listening

### T4 — Update `context.md`
```
## Day 2 — wake_word.py + stt.py
- wake_word.py: WakeWordDetector class — pvporcupine background thread,
  threading.Event for activation signal, energy-threshold fallback
- stt.py: SpeechToText class — Google Web Speech primary,
  Whisper base model offline fallback, configurable thresholds
- main.py: wake → listen → transcribe loop wired
```

### TEST — Day 2
- [ ] Say "Hey NOVA" — wake event triggers within 1 second
- [ ] After waking, speak a sentence — text is printed correctly
- [ ] Silence for 5 seconds — NOVA returns to listening without crashing
- [ ] Disconnect internet — Whisper fallback transcribes correctly
- [ ] Loud ambient noise — energy threshold filters background

### PUSH
```bash
git add .
git commit -m "Day 2: Module 1 (wake word) + Module 2 (STT) implemented"
git push origin main
```

---

## DAY 3 — Module 3 (NLP Intent Engine) + TTS

**Goal:** Classify every transcribed command into an intent category and extract entities. Add voice output (TTS) so NOVA can speak responses.

**Modules:** `nlp_engine.py` (+ TTS integrated in `main.py`)
**Stack:** `spaCy`, `NLTK`, `pyttsx3`, `gTTS`

### T0 — Prerequisites
- [ ] `pip install spacy nltk pyttsx3 gTTS`
- [ ] `python -m spacy download en_core_web_sm`
- [ ] `python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"`
- [ ] Open `modules/nlp_engine.py`

### T1 — Implement `nlp_engine.py` — Core Structure
- Import `spacy`, `nltk`, `re`
- Load `en_core_web_sm` model at module level
- Define `INTENT_PATTERNS` dict mapping intent names to keyword lists:
  - `"weather"`: `["weather", "temperature", "forecast", "rain", "sunny"]`
  - `"news"`: `["news", "headlines", "space", "NASA", "science"]`
  - `"wikipedia"`: `["tell me about", "what is", "who is", "explain"]`
  - `"web"`: `["open", "go to", "visit", "browse"]`
  - `"app"`: `["launch", "start", "run", "open"]`
  - `"email"`: `["email", "mail", "send email", "write email"]`
  - `"whatsapp"`: `["whatsapp", "message", "send message"]`
  - `"music"`: `["play", "music", "song", "pause", "resume", "next"]`
  - `"notes"`: `["note", "take a note", "write down", "remember"]`
  - `"reminder"`: `["remind", "reminder", "alert me", "set alarm"]`
  - `"calendar"`: `["calendar", "event", "schedule", "meeting"]`
  - `"task"`: `["task", "to-do", "todo", "add task", "mark done"]`
  - `"datetime"`: `["time", "date", "today", "what day", "how many days"]`
  - `"math"`: `["calculate", "what is", "+", "-", "*", "/", "percent"]`
  - `"system"`: `["shutdown", "restart", "sleep", "lock", "volume", "brightness", "battery", "cpu", "ram"]`
  - `"screenshot"`: `["screenshot", "capture screen", "take screenshot"]`
  - `"clipboard"`: `["clipboard", "copy", "paste", "what did i copy"]`
  - `"translate"`: `["translate", "in french", "in arabic", "in urdu"]`
  - `"memory"`: `["remember that", "forget that", "what do you know"]`
  - `"joke"`: `["joke", "make me laugh", "funny"]`
  - `"roast"`: `["roast me"]`
  - `"conversation"`: fallback — passed to Groq

### T2 — Implement `classify_intent(text)` Function
- Lowercase and tokenize with NLTK
- Remove stopwords
- Match against `INTENT_PATTERNS` (keyword in text)
- Return first matched intent or `"conversation"` as fallback
- Priority ordering: system > datetime > math > weather > ... > conversation

### T3 — Implement `extract_entities(text)` Function
- Run spaCy NER on text
- Extract: `GPE`/`LOC` → city, `PERSON` → name, `TIME`/`DATE` → time entities, `ORG` → organization
- Regex fallback: extract quoted strings, numbers, app names
- Return dict: `{"city": ..., "name": ..., "time": ..., "query": ...}`

### T4 — Implement `process(text)` Main Entry Point
- Call `classify_intent(text)` → get intent
- Call `extract_entities(text)` → get entities
- Return `{"intent": intent, "entities": entities, "original": text}`

### T5 — Create TTS Utility in `main.py`
- `speak(text)`: pyttsx3 engine, `engine.say(text)`, `engine.runAndWait()`
- gTTS fallback function `speak_online(text)` for when pyttsx3 unavailable
- Load TTS rate and volume from config.json

### T6 — Wire NLP + TTS into `main.py`
- After STT transcription: call `nlp_engine.process(text)` → print intent + entities
- Call `speak(f"I understood: {intent}")` to confirm

### T7 — Update `context.md`

### TEST — Day 3
- [ ] "Open Chrome" → intent: `app`, entity: `Chrome`
- [ ] "Weather in Islamabad" → intent: `weather`, entity city: `Islamabad`
- [ ] "What is machine learning" → intent: `wikipedia`, query: `machine learning`
- [ ] "Set a reminder at 5 PM" → intent: `reminder`, time: `5 PM`
- [ ] "Tell me a joke" → intent: `joke`
- [ ] Gibberish input → intent: `conversation`
- [ ] TTS speaks response clearly without crashing

### PUSH
```bash
git add .
git commit -m "Day 3: Module 3 (NLP intent engine) + TTS output integrated"
git push origin main
```

---

## DAY 4 — Module 4 (Groq LLM Brain)

**Goal:** Connect Groq API (LLaMA 3) as NOVA's second brain for complex, conversational, and ambiguous queries.

**Module:** `groq_brain.py`
**Stack:** `groq` Python SDK, `.env` for API key, rolling conversation history

### T0 — Prerequisites
- [ ] `pip install groq python-dotenv`
- [ ] Create Groq account at console.groq.com → get API key
- [ ] Add `GROQ_API_KEY=` to `.env`
- [ ] Open `modules/groq_brain.py`

### T1 — Implement `GroqBrain` Class — Init
- Import `groq`, `os`, `datetime`
- `__init__`: init `groq.Groq(api_key=os.getenv("GROQ_API_KEY"))`
- `self.conversation_history = []`
- `self.model = "llama3-70b-8192"`
- Build `self.system_prompt` string: include NOVA name, personality description (professional + friendly), user name (Akif), SE student at [university], Wah Cantt, current date/time

### T2 — Implement `inject_memory(memories_list)` Method
- Accept list of `(key, value)` tuples from SQLite memory
- Prepend to system prompt: `"Known facts about Akif: [facts]"`
- Called before every Groq API call

### T3 — Implement `chat(user_message)` Method
- Append `{"role": "user", "content": user_message}` to `self.conversation_history`
- Keep rolling window: last 10 messages only (slice `[-10:]`)
- Build messages list: `[{"role": "system", "content": system_prompt}] + conversation_history`
- Call `client.chat.completions.create(model=self.model, messages=messages, max_tokens=1024, temperature=0.7)`
- Extract response text from `completion.choices[0].message.content`
- Append assistant response to `conversation_history`
- Return response string

### T4 — Implement `reset_conversation()` Method
- Clear `self.conversation_history = []`
- Used when user says "start over" or new session begins

### T5 — Implement `extract_facts(conversation_text)` Method
- Send conversation to Groq with a special system prompt asking it to extract key user facts as JSON
- Returns list of `{"key": ..., "value": ..., "category": ...}` dicts
- Used by memory system after each session

### T6 — Wire into `main.py`
- Import `GroqBrain`, instantiate once at startup
- In NLP router: if `intent == "conversation"` or confidence low → call `groq_brain.chat(text)`
- Speak the response via TTS

### T7 — Update `context.md`

### TEST — Day 4
- [ ] "What is quantum entanglement?" → Groq responds with accurate explanation
- [ ] Multi-turn: ask follow-up question referencing previous answer → context maintained
- [ ] "Draft an email to professor asking for extension" → Groq produces full email text
- [ ] Invalid API key → graceful error message spoken, no crash
- [ ] 10+ turn conversation → only last 10 kept in history, no memory overflow
- [ ] `reset_conversation()` clears history correctly

### PUSH
```bash
git add .
git commit -m "Day 4: Module 4 (Groq LLM brain) — stateful conversation, memory injection"
git push origin main
```

---

## DAY 5 — Module 20 (SQLite Memory System) + DB Schema

**Goal:** Full SQLite database live with all 8 tables. NOVA can store and retrieve facts, conversation logs, notes, reminders, events, tasks, contacts, and activity.

**Module:** `memory_system.py`
**Stack:** `sqlite3` (built-in), schema from ERD

### T0 — Prerequisites
- [ ] No pip installs needed (sqlite3 built-in)
- [ ] Ensure `data/` directory exists
- [ ] Open `modules/memory_system.py`

### T1 — Implement `DatabaseManager` Class — Init & Schema
- `__init__`: connect to `data/memory.db`, call `_create_tables()`
- `_create_tables()`: execute `CREATE TABLE IF NOT EXISTS` for all 8 tables:

**Users:** `id, email, created_at, updated_at`
**UserFacts:** `id, user_id, key, value, category, created_at, updated_at`
**Notes:** `id, user_id, activity_id (nullable), content, tags, created_at`
**Tasks:** `id, user_id, activity_id (nullable), title, is_done, priority, due_date, created_at`
**Events:** `id, user_id, activity_id (nullable), title, event_dt, location, notes, created_at`
**Reminders:** `id, user_id, activity_id (nullable), title, message, trigger_at, is_done, created_at`
**Contacts:** `id, user_id, name, phone, email, platform, created_at`
**ActivityLog:** `id, user_id, command_text, module_triggered, response_summary, success, timestamp`
**ConversationLog:** `id, user_id, activity_id, role, content, session_id, timestamp`

- Insert default user row (Akif, user_id=1) on first run

### T2 — Implement UserFacts Methods
- `store_fact(key, value, category)`: INSERT or REPLACE into UserFacts
- `get_facts(limit=10)`: SELECT top facts ordered by updated_at DESC
- `get_fact(key)`: SELECT single fact by key
- `delete_fact(key)`: DELETE from UserFacts where key matches
- `search_facts(query)`: SELECT where key or value LIKE %query%

### T3 — Implement ActivityLog Methods
- `log_activity(command_text, module_triggered, response_summary, success)`: INSERT into ActivityLog
- `get_today_log()`: SELECT where date(timestamp) = date('now')
- `get_recent_log(n=10)`: SELECT last n entries
- `cleanup_old_logs(days=30)`: DELETE where timestamp < now - 30 days

### T4 — Implement ConversationLog Methods
- `log_message(role, content, session_id, activity_id=None)`: INSERT into ConversationLog
- `get_session(session_id)`: SELECT all messages for a session
- `get_recent_conversation(n=20)`: SELECT last n messages

### T5 — Wire Memory into `groq_brain.py`
- In `GroqBrain.__init__`: import `DatabaseManager`, instantiate
- Before each `chat()` call: `db.get_facts(10)` → `inject_memory(facts)`
- After each `chat()` session: call `extract_facts()` → `db.store_fact()` for each extracted fact

### T6 — Update `context.md`

### TEST — Day 5
- [ ] `data/memory.db` created with all 8 tables on first run
- [ ] `store_fact("favorite_editor", "VS Code", "preferences")` → row inserted
- [ ] `get_facts(10)` returns list with the stored fact
- [ ] `delete_fact("favorite_editor")` → row removed
- [ ] `log_activity("open chrome", "app_launcher", "Opened Chrome", True)` → logged
- [ ] `get_today_log()` returns today's entries only
- [ ] `cleanup_old_logs(30)` removes entries older than 30 days
- [ ] Voice: "Remember that my favourite editor is VS Code" → fact stored

### PUSH
```bash
git add .
git commit -m "Day 5: Module 20 (SQLite memory system) — 8-table schema, CRUD methods"
git push origin main
```

---

## DAY 6 — Module 23 (HUD Tkinter Interface)

**Goal:** NOVA's visual face — dark HUD overlay always-on-top with animated waveform, status indicator, and command history.

**Module:** `hud_interface.py`
**Stack:** `tkinter`, `matplotlib`, `threading`

### T0 — Prerequisites
- [ ] `pip install matplotlib`
- [ ] Tkinter is built-in with Python 3.11 on Windows
- [ ] Open `modules/hud_interface.py`

### T1 — Implement `NOVAHud` Class — Window Setup
- `__init__`: create `tk.Tk()` root window
- Window config: `overrideredirect(True)` (frameless), `wm_attributes("-topmost", True)`, `wm_attributes("-alpha", 0.92)`, background `#0D0D0D`
- Geometry: dock to right side — `geometry(f"320x{screen_height}+{screen_width-320}+0")`
- Font: `("Courier New", 10)` — monospace HUD aesthetic

### T2 — Implement Waveform Canvas (matplotlib FuncAnimation)
- Embed matplotlib `Figure` in Tkinter via `FigureCanvasTkAgg`
- Figure background `#0D0D0D`, axes background `#0D0D0D`
- Animate circular waveform with `FuncAnimation`: sine wave that pulses amplitude based on NOVA state
- Color: `#00D4FF` (cyan/teal)
- Bind click on canvas → trigger wake/listen callback

### T3 — Implement Status Indicator
- `tk.Label` at top: shows `🔴 Sleeping` / `🟡 Listening` / `🟢 Processing` / `🔵 Speaking`
- `update_status(state)` method: updates label text and color
- Clock label: `datetime.now().strftime("%H:%M:%S")` updated every second via `after(1000, ...)`

### T4 — Implement Conversation Display
- `tk.Text` widget (read-only, scrollable) showing last 5 command/response pairs
- Colors: user text `#AAAAAA`, NOVA response `#00D4FF`
- `update_display(command, response)` method: insert new pair, trim to 5 entries

### T5 — Implement Reminders Ticker
- `tk.Label` at bottom scrolling upcoming reminders/events text
- `update_ticker(text)` method: updates ticker content
- Called at startup with today's reminders from DB

### T6 — Thread-Safe Update Methods
- All Tkinter updates from non-main threads must use `root.after(0, func)` — implement `safe_update(func, *args)`

### T7 — Wire HUD into `main.py`
- Start HUD in main thread (Tkinter must run in main thread)
- All other modules (wake word, gesture engine) run as daemon threads
- HUD `update_status()` called from pipeline at each stage transition

### T8 — Update `context.md`

### TEST — Day 6
- [ ] HUD window appears docked right, always on top, semi-transparent
- [ ] Status cycles through 🔴→🟡→🟢→🔵 on command
- [ ] Waveform animates continuously — pulses faster in speaking state
- [ ] Click on waveform triggers listen callback
- [ ] Last 5 exchanges shown in conversation panel
- [ ] Clock updates every second
- [ ] No Tkinter threading errors when updated from background thread

### PUSH
```bash
git add .
git commit -m "Day 6: Module 23 (HUD interface) — dark overlay, waveform, status, conversation panel"
git push origin main
```

---

## DAY 7 — Week 1 Integration Test + Git Push

**Goal:** Full voice pipeline works end-to-end. Wake → Listen → NLP → Groq OR local → TTS → HUD. All Week 1 modules verified together.

### T0 — Pull latest, review all 6 modules
- [ ] `git pull origin main`
- [ ] Review `main.py` for complete pipeline wiring

### T1 — Full Pipeline Integration Test
Wire the complete flow in `main.py`:
1. HUD starts (main thread)
2. Wake word detector starts (daemon thread)
3. `wake_event.wait()` — blocks until "Hey NOVA"
4. HUD → `🟡 Listening`
5. `stt.listen()` → `stt.transcribe()` → text
6. HUD → `🟢 Processing`
7. `nlp_engine.process(text)` → intent + entities
8. If intent == `"conversation"` → `groq_brain.chat(text)` → response
9. Else → log intent (stub for future modules)
10. HUD → `🔵 Speaking`
11. `speak(response)`
12. `db.log_activity(...)` — log the interaction
13. HUD → `🔴 Sleeping`, reset wake event, loop

### T2 — Fix Integration Bugs
- Threading race conditions
- Tkinter `after()` not used correctly
- STT energy threshold too sensitive/not sensitive enough
- Groq API rate limit handling (add exponential backoff)

### T3 — Write `tests/test_all.py` — Week 1 Test Cases
```python
# Test 1: Wake word detection triggers event within 2s
# Test 2: STT transcribes "open chrome" correctly
# Test 3: NLP classifies "open chrome" as intent="app"
# Test 4: NLP extracts "Islamabad" from "weather in Islamabad"
# Test 5: Groq responds to "what is AI" with non-empty string
# Test 6: DB stores and retrieves a fact correctly
# Test 7: HUD status updates without Tkinter error
```

### T4 — Update README.md
- Project description, setup instructions, how to run, module list

### T5 — Update `context.md`
```
## Day 7 — Week 1 Integration
- Full pipeline wired: wake → STT → NLP → Groq/local → TTS → HUD
- Groq exponential backoff added in groq_brain.chat()
- Tkinter thread safety fixed with root.after() throughout hud_interface.py
- Week 1 test cases added to tests/test_all.py
- README updated with setup + run instructions
```

### TEST — Day 7 (Full Integration)
- [ ] Cold start: say "Hey NOVA, what time is it?" — full pipeline completes in < 3s
- [ ] Say "Hey NOVA, tell me something interesting" — Groq responds via TTS
- [ ] HUD status transitions correctly through all 4 states
- [ ] Memory DB has activity log entry after each command
- [ ] Restart NOVA — previous session facts still in DB
- [ ] All 7 unit tests in `test_all.py` pass

### PUSH
```bash
git add .
git commit -m "Day 7: Week 1 integration test — full pipeline E2E verified, README updated"
git push origin main
```

---
---

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WEEK 2 — Information & Web Modules
# Days 8–14
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

---

## DAY 8 — Module 5 (Weather) + Module 6 (NASA News)

**Goal:** NOVA fetches real-time weather for any city and reads today's NASA space news.

**Modules:** `weather.py`, `news.py`
**Stack:** `requests`, OpenWeatherMap API, NASA Open API

### T0 — Prerequisites
- [ ] `pip install requests`
- [ ] Register at openweathermap.org → get free API key → add `OPENWEATHER_API_KEY=` to `.env`
- [ ] NASA API key: `DEMO_KEY` works for development (add `NASA_API_KEY=DEMO_KEY` to `.env`)
- [ ] Open `modules/weather.py` and `modules/news.py`

### T1 — Implement `weather.py`
- `WeatherModule` class
- `get_weather(city=None)`: use default city from config if None
- Build URL: `https://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&units=metric`
- Parse response: temp, feels_like, humidity, description, wind_speed
- Return formatted string: `"It's currently {temp}°C in {city}, feels like {feels}°C, humidity {humidity}%, {description}."`
- Error handling: city not found → `"I couldn't find weather for {city}."`
- API timeout: 5 seconds, connection error handled

### T2 — Implement `news.py`
- `NewsModule` class
- `get_nasa_apod()`: GET `https://api.nasa.gov/planetary/apod?api_key={key}`
- Extract: `title`, `explanation` (first 3 sentences), `date`
- Return: `"Today's space news: {title}. {explanation}"`
- `get_science_fact()`: hardcoded list of 20 interesting science facts — return `random.choice(facts)`
- Error handling: API down → speak cached last result or fallback fact

### T3 — Wire into NLP Router in `main.py`
- intent `"weather"` → extract city entity → `weather.get_weather(city)`
- intent `"news"` → `news.get_nasa_apod()`

### T4 — Update `context.md`

### TEST — Day 8
- [ ] "What's the weather in Lahore?" → correct temperature and description
- [ ] "Weather" (no city) → uses default city Wah Cantt
- [ ] "What's the weather in XYZcity?" → graceful error message
- [ ] "What's in the news today?" → NASA APOD title and summary spoken
- [ ] Disconnect internet → error handled without crash

### PUSH
```bash
git add .
git commit -m "Day 8: Module 5 (weather) + Module 6 (NASA news) implemented"
git push origin main
```

---

## DAY 9 — Module 7 (Wikipedia) + Module 19 (Translation)

**Goal:** NOVA answers "tell me about X" with Wikipedia summaries and translates text between any languages.

**Modules:** `wikipedia_module.py`, `translation.py`
**Stack:** `wikipedia` Python library, `deep-translator`

### T0 — Prerequisites
- [ ] `pip install wikipedia deep-translator`
- [ ] Open `modules/wikipedia_module.py` and `modules/translation.py`

### T1 — Implement `wikipedia_module.py`
- `WikipediaModule` class
- `search(query)`:
  - `wikipedia.summary(query, sentences=3)`
  - Disambiguation: `except wikipedia.exceptions.DisambiguationError as e` → return `f"Did you mean: {e.options[:3]}?"`
  - Page not found: `except wikipedia.exceptions.PageError` → `"I couldn't find information about {query}."`
  - Strip references, clean whitespace
- Return 3-sentence summary string

### T2 — Implement `translation.py`
- `TranslationModule` class
- Language map dict: common language names → ISO 639-1 codes (`"french": "fr"`, `"arabic": "ar"`, `"urdu": "ur"`, etc.)
- `translate(text, target_language)`:
  - Map language name to code
  - `GoogleTranslator(source="auto", target=lang_code).translate(text)`
  - Return translated string
- `detect_language(text)`: use `deep_translator` detect method
- Error: unknown language → `"I don't know that language code."`

### T3 — Extract entities for Translation
- NLP: for translate intent, extract quoted text + target language from sentence
- Pattern: `"translate [text] to [language]"` or `"what does [word] mean in [language]"`

### T4 — Wire into NLP Router
- intent `"wikipedia"` → extract query → `wikipedia_module.search(query)`
- intent `"translate"` → extract text + language → `translation.translate(text, language)`

### T5 — Update `context.md`

### TEST — Day 9
- [ ] "Tell me about Python programming language" → 3-sentence summary spoken
- [ ] "What is the Eiffel Tower?" → correct Wikipedia result
- [ ] "Tell me about Mercury" → disambiguation: "Did you mean: Mercury planet, Mercury element, ...?"
- [ ] "Translate 'how are you' to Arabic" → Arabic text spoken and displayed
- [ ] "What does 'marhaba' mean in English?" → correct translation
- [ ] Unknown language → graceful error

### PUSH
```bash
git add .
git commit -m "Day 9: Module 7 (Wikipedia) + Module 19 (Translation) implemented"
git push origin main
```

---

## DAY 10 — Module 8 (Web Automation — Selenium)

**Goal:** NOVA opens websites by name and performs Selenium actions — liking posts, commenting, searching YouTube.

**Module:** `web_automation.py`
**Stack:** `selenium`, `webbrowser`, `sites.json`

### T0 — Prerequisites
- [ ] `pip install selenium`
- [ ] Download ChromeDriver matching installed Chrome version → add to PATH
- [ ] Verify `sites.json` has all URLs mapped
- [ ] Open `modules/web_automation.py`

### T1 — Implement `WebAutomation` Class — Init
- Load `config/sites.json`
- `self.driver = None` (lazy init — only open browser when needed)
- `_get_driver()`: init `webdriver.Chrome()` with options (no detach, implicit wait 5s)

### T2 — Implement `open_site(name)` Method
- Fuzzy match `name` against `sites.json` keys using `rapidfuzz.process.extractOne`
- If match score > 70: `webbrowser.open(url)` — simple opens use webbrowser (faster)
- Unknown site: `"I don't know that website."`

### T3 — Implement Selenium Action Methods
- `search_youtube(query)`: navigate to `youtube.com/results?search_query={query}`
- `like_current_post()`: find and click like button (LinkedIn `.react-button__trigger`, YouTube `#like-button`)
- `comment_on_post(text)`: find comment box, click, type text, submit
- `scroll_down(amount=3)`: `driver.execute_script("window.scrollBy(0, 500);")`  × amount
- `scroll_up(amount=3)`: scroll up equivalent

### T4 — Wire into NLP Router
- intent `"web"` + entity site name → `open_site(name)` OR selenium action
- Parse action verbs: "like" → `like_current_post()`, "comment" → `comment_on_post()`, "search on youtube" → `search_youtube()`

### T5 — Update `context.md`

### TEST — Day 10
- [ ] "Open YouTube" → YouTube opens in Chrome
- [ ] "Open GitHub" → github.com opens
- [ ] "Search for Python tutorials on YouTube" → YouTube search results page loads
- [ ] "Scroll down" → page scrolls down 3 steps
- [ ] "Open XYZ" → fuzzy match suggests closest or says unknown
- [ ] Selenium driver closes cleanly on NOVA shutdown

### PUSH
```bash
git add .
git commit -m "Day 10: Module 8 (web automation + Selenium) implemented"
git push origin main
```

---

## DAY 11 — Module 9 (App Launcher) + Module 18 (Clipboard)

**Goal:** Open any Windows app by voice with fuzzy matching. Read/write clipboard by voice.

**Modules:** `app_launcher.py`, `clipboard_manager.py`
**Stack:** `os`, `subprocess`, `rapidfuzz`, `pyperclip`, `apps.json`

### T0 — Prerequisites
- [ ] `pip install rapidfuzz pyperclip`
- [ ] Populate `config/apps.json` with all app paths (VS Code, Chrome, Firefox, Notepad, Calculator, Spotify, VLC, File Explorer, Task Manager, Control Panel, WhatsApp Desktop, Discord, Telegram, PowerPoint, Word, Excel, GitHub Desktop, Postman)
- [ ] Open `modules/app_launcher.py` and `modules/clipboard_manager.py`

### T1 — Implement `app_launcher.py`
- `AppLauncher` class — load `apps.json` on init
- `launch(app_name)`:
  - Fuzzy match app_name against `apps.json` keys using `rapidfuzz.process.extractOne`
  - Score threshold: 65 — below = `"I don't know that application."`
  - `subprocess.Popen([path])` — non-blocking launch
  - Return `f"Opening {matched_name}."`
- `get_app_list()`: return list of all launchable app names

### T2 — Implement `clipboard_manager.py`
- `ClipboardManager` class
- `read()`: `pyperclip.paste()` → return clipboard text (truncate to 200 chars for TTS)
- `write(text)`: `pyperclip.copy(text)` → return `f"Copied to clipboard: {text[:50]}..."`
- Handle empty clipboard gracefully

### T3 — Wire into NLP Router
- intent `"app"` → extract app name → `app_launcher.launch(name)`
- intent `"clipboard"` → parse sub-action: `"what's in my clipboard"` → `read()`, `"copy [text]"` → `write(text)`

### T4 — Update `context.md`

### TEST — Day 11
- [ ] "Open Chrome" → Chrome launches
- [ ] "Open Visual Studio" → fuzzy matches "VS Code", launches correctly
- [ ] "Launch calculator" → Calculator opens
- [ ] "Open XYZapp" → graceful unknown app message
- [ ] "Copy hello world to clipboard" → pyperclip stores it
- [ ] "What's in my clipboard?" → speaks the clipboard content
- [ ] Empty clipboard → handled without error

### PUSH
```bash
git add .
git commit -m "Day 11: Module 9 (app launcher) + Module 18 (clipboard manager) implemented"
git push origin main
```

---

## DAY 12 — Module 10 (Email Compose & Send)

**Goal:** Draft emails via Groq by voice and send via Gmail SMTP. Full confirmation flow before sending.

**Module:** `email_module.py`
**Stack:** `smtplib`, `email` (built-in), Groq API for drafting, `.env` for credentials

### T0 — Prerequisites
- [ ] Enable Gmail 2FA → generate App Password → add to `.env`
- [ ] No extra pip installs (smtplib + email built-in)
- [ ] Open `modules/email_module.py`

### T1 — Implement `EmailModule` Class — Init
- Load `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` from `.env`
- `self.smtp_server = "smtp.gmail.com"`, `self.smtp_port = 587`
- Import `groq_brain` for drafting

### T2 — Implement `draft_email(recipient_name, topic, details)` Method
- Build Groq prompt: `"Draft a professional email to {recipient} about {topic}. Details: {details}. Include Subject line."`
- Call `groq_brain.chat(prompt)` → get full draft
- Parse subject from draft (look for `Subject:` line)
- Return `{"subject": subject, "body": body, "recipient": recipient}`

### T3 — Implement `send_email(to_address, subject, body)` Method
- Build `email.mime.multipart.MIMEMultipart()` message
- Attach body as `MIMEText(body, "plain")`
- Connect via `smtplib.SMTP(server, port)` → `starttls()` → `login()` → `sendmail()`
- Return success/failure string
- Error handling: auth failure, connection timeout, invalid address

### T4 — Implement Full Voice Flow `handle_email_command(text)` Method
- Parse recipient name and topic from NLP entities
- If missing: ask follow-up via TTS `speak("Who should I send it to?")`
- Call `draft_email()` → speak draft aloud
- Ask `"Should I send it? Say yes or no."`
- Listen for confirmation → if yes: `send_email()`, if no: `"Email cancelled."`

### T5 — Wire into NLP Router
- intent `"email"` → `email_module.handle_email_command(text)`

### T6 — Update `context.md`

### TEST — Day 12
- [ ] "Write an email to Ali about the project meeting" → Groq drafts email, spoken aloud
- [ ] Confirm "yes" → email sent, confirmation spoken
- [ ] Say "no" → email cancelled gracefully
- [ ] Invalid Gmail credentials → error message without crash
- [ ] No internet → SMTP connection error handled

### PUSH
```bash
git add .
git commit -m "Day 12: Module 10 (email compose + send via Groq + Gmail SMTP) implemented"
git push origin main
```

---

## DAY 13 — Module 11 (WhatsApp) + Module 12 (Music/Media)

**Goal:** Send WhatsApp messages by voice. Play YouTube or local music by voice with playback controls.

**Modules:** `whatsapp_module.py`, `music_module.py`
**Stack:** `PyWhatKit`, `subprocess` (VLC), `pyautogui`, `contacts.json`

### T0 — Prerequisites
- [ ] `pip install pywhatkit pyautogui`
- [ ] Ensure Chrome is default browser and WhatsApp Web is logged in
- [ ] VLC Media Player installed at known path
- [ ] Verify `contacts.json` structure: `[{"name": "Mama", "phone": "+923001234567"}]`
- [ ] Open `modules/whatsapp_module.py` and `modules/music_module.py`

### T1 — Implement `whatsapp_module.py`
- `WhatsAppModule` class — load `contacts.json`
- `find_contact(name)`: fuzzy match against contacts list (rapidfuzz), score threshold 70
- `send_message(contact_name, message)`:
  - Find contact → get phone number
  - `pywhatkit.sendwhatmsg_instantly(phone, message, wait_time=10, tab_close=True)`
  - Return confirmation
- Error: contact not found → `"I don't have {name} in your contacts."`
- Error: WhatsApp Web not open → `"Please open WhatsApp Web in Chrome first."`

### T2 — Implement `music_module.py`
- `MusicModule` class
- `play_youtube(query)`: `pywhatkit.playonyt(query)` — opens YouTube and autoplays
- `play_local(path=None)`: open VLC with local music folder or specific file
  - Default path from config: e.g., `C:/Users/Akif/Music`
- `pause()`: `pyautogui.press("space")` — works in active browser/VLC
- `resume()`: `pyautogui.press("space")`
- `next_track()`: `pyautogui.hotkey("ctrl", "right")` (VLC) or `shift+n` (YouTube)
- `previous_track()`: `pyautogui.hotkey("ctrl", "left")`
- `set_volume(level)`: delegate to `system_controls.set_volume(level)`

### T3 — Wire into NLP Router
- intent `"whatsapp"` → extract contact + message → `whatsapp.send_message()`
- intent `"music"` → parse sub-action: play/pause/resume/next/previous/local
  - "Play lo-fi on YouTube" → `play_youtube("lo-fi")`
  - "Play my playlist" → `play_local()`
  - "Pause" → `pause()`

### T4 — Update `context.md`

### TEST — Day 13
- [ ] "Send a WhatsApp to Mama saying I'll be home by 8" → WhatsApp Web opens, message sent
- [ ] "Send WhatsApp to Ali" (not in contacts) → graceful error
- [ ] "Play lo-fi hip hop on YouTube" → YouTube plays
- [ ] "Play my playlist" → VLC opens local music folder
- [ ] "Pause" → media pauses
- [ ] "Next song" → next track plays

### PUSH
```bash
git add .
git commit -m "Day 13: Module 11 (WhatsApp) + Module 12 (music/media control) implemented"
git push origin main
```

---

## DAY 14 — Week 2 Integration Test + Git Push

**Goal:** All 8 Week 2 modules verified working together with the Week 1 pipeline.

### T0 — Pull latest, review all new modules

### T1 — Full Week 2 Integration Test
- Wire all new intent routes in `main.py`
- Verify complete intent routing table covers all 25 module intents

### T2 — Write Week 2 Test Cases in `tests/test_all.py`
```python
# Test 8:  Weather for "Islamabad" returns temp and description
# Test 9:  NASA APOD returns non-empty title
# Test 10: Wikipedia search "Python" returns 3 sentences
# Test 11: Translation "how are you" to French → "Comment allez-vous"
# Test 12: sites.json loads and "youtube" maps to correct URL
# Test 13: App launcher fuzzy matches "visual studio" → "VS Code"
# Test 14: Clipboard write → read returns same text
# Test 15: Email draft via Groq returns non-empty subject and body
```

### T3 — Fix Any Integration Issues
- NLP routing conflicts (e.g., "open YouTube" — app vs web intent)
- PyWhatKit timing issues
- Module import errors

### T4 — Update `context.md`

### TEST — Day 14 (Full Integration)
- [ ] All 8 new test cases pass
- [ ] Complete command set from Week 2 works in real pipeline
- [ ] No import errors on `python main.py`
- [ ] All 15 unit tests pass

### PUSH
```bash
git add .
git commit -m "Day 14: Week 2 integration test — all information/web modules verified"
git push origin main
```

---
---

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WEEK 3 — Automation, Gestures & System
# Days 15–21
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

---

## DAY 15 — Module 13 (Notes & Reminders)

**Goal:** NOVA takes notes to SQLite and fires timed reminder alerts via TTS at exact scheduled times.

**Module:** `notes_reminders.py`
**Stack:** `sqlite3`, `dateparser`, `threading`, `pyttsx3`

### T0 — Prerequisites
- [ ] `pip install dateparser`
- [ ] Notes + Reminders tables already exist from Day 5
- [ ] Open `modules/notes_reminders.py`

### T1 — Implement `NotesModule` Class
- `save_note(content, tags="")`:
  - INSERT into Notes table (user_id=1, content, tags, created_at=now)
  - Return `f"Note saved: {content[:50]}"`
- `read_notes(n=5)`: SELECT last n notes ORDER BY created_at DESC → format as list
- `delete_note(note_id)`: DELETE from Notes where id = note_id
- `search_notes(query)`: SELECT where content LIKE %query%

### T2 — Implement `RemindersModule` Class
- `set_reminder(message, trigger_time_str)`:
  - Parse `trigger_time_str` using `dateparser.parse()` → get `datetime` object
  - INSERT into Reminders table: message, trigger_at=parsed_datetime, is_done=False
  - Return `f"Reminder set for {trigger_at.strftime('%I:%M %p')} — {message}"`
- `get_pending_reminders()`: SELECT where is_done=False AND trigger_at > now
- `mark_done(reminder_id)`: UPDATE is_done=True

### T3 — Implement Reminder Background Engine
- `ReminderEngine` class with daemon thread
- `_check_loop()`: every 30 seconds, call `get_pending_reminders()`
  - For each reminder: if `trigger_at <= now` → fire alert
  - Fire alert: `speak(f"Reminder: {message}")`, `mark_done(id)`
  - Update HUD ticker
- `start()`: launch as `threading.Thread(daemon=True)`

### T4 — Wire into NLP Router
- intent `"notes"` → parse sub-action: take/read/delete/search
  - "Take a note: [content]" → `save_note(content)`
  - "Read my notes" → `read_notes()`
  - "Search notes for [query]" → `search_notes(query)`
- intent `"reminder"` → parse time + message → `set_reminder(message, time_str)`

### T5 — Start Reminder Engine in `main.py`
- Instantiate `ReminderEngine` → `engine.start()` before main loop

### T6 — Update `context.md`

### TEST — Day 15
- [ ] "Take a note: submit OOP assignment by Friday" → note saved to DB
- [ ] "Read my notes" → last 5 notes spoken
- [ ] "Set a reminder for 5 PM to call Ali" → `dateparser` parses correctly, row inserted
- [ ] Wait to trigger time → TTS fires reminder alert automatically
- [ ] "Set a reminder in 1 minute to test this" → fires after 60s
- [ ] Reminder marked done after firing — doesn't repeat

### PUSH
```bash
git add .
git commit -m "Day 15: Module 13 (notes + reminders) — SQLite storage, background reminder engine"
git push origin main
```

---

## DAY 16 — Module 14 (Calendar & Tasks)

**Goal:** NOVA manages calendar events and a to-do task list, all stored in SQLite with natural language date parsing.

**Module:** `calendar_tasks.py`
**Stack:** `sqlite3`, `dateparser`

### T0 — Prerequisites
- [ ] Events + Tasks tables already exist from Day 5
- [ ] `dateparser` already installed
- [ ] Open `modules/calendar_tasks.py`

### T1 — Implement `CalendarModule` Class
- `add_event(title, event_dt_str, location="", notes="")`:
  - Parse `event_dt_str` with `dateparser.parse()`
  - INSERT into Events table
  - Return `f"Event added: {title} on {event_dt.strftime('%A, %d %B at %I:%M %p')}"`
- `get_events_today()`: SELECT where date(event_dt) = date('now')
- `get_events_tomorrow()`: SELECT where date(event_dt) = date('now', '+1 day')
- `get_upcoming_events(days=7)`: SELECT next 7 days
- `delete_event(event_id)`: DELETE by id

### T2 — Implement `TasksModule` Class
- `add_task(title, priority="medium", due_date_str=None)`:
  - Parse due_date if provided
  - INSERT into Tasks with is_done=False
  - Return `f"Task added: {title}"`
- `get_pending_tasks()`: SELECT where is_done=False ORDER BY priority, due_date
- `mark_done(task_id_or_title)`: fuzzy match title → UPDATE is_done=True
- `delete_task(task_id)`: DELETE by id
- `get_all_tasks()`: SELECT all tasks

### T3 — Wire into NLP Router
- intent `"calendar"` → parse sub-action: add/what do I have/upcoming
  - "Add event: AI class Monday at 9 AM" → `add_event("AI class", "Monday at 9 AM")`
  - "What do I have today/tomorrow?" → `get_events_today()` / `get_events_tomorrow()`
- intent `"task"` → parse sub-action: add/list/done
  - "Add to task list: finish NOVA project" → `add_task("finish NOVA project")`
  - "What are my tasks?" → `get_pending_tasks()`
  - "Mark [task] as done" → `mark_done(task)`

### T4 — Load Today's Events into HUD Ticker on Startup
- In `main.py` startup: call `calendar_module.get_events_today()` → pass to `hud.update_ticker()`

### T5 — Update `context.md`

### TEST — Day 16
- [ ] "Add a calendar event: AI class on Monday at 9 AM" → parsed correctly, stored
- [ ] "What do I have today?" → today's events spoken
- [ ] "What do I have tomorrow?" → tomorrow's events spoken
- [ ] "Add to my task list: finish NOVA project" → task stored, is_done=False
- [ ] "What are my tasks?" → pending tasks listed
- [ ] "Mark finish NOVA project as done" → is_done=True in DB
- [ ] HUD ticker shows today's events on startup

### PUSH
```bash
git add .
git commit -m "Day 16: Module 14 (calendar + tasks) — events and to-do with natural language dates"
git push origin main
```

---

## DAY 17 — Module 16 (System Controls) + Module 17 (Screenshot Tools)

**Goal:** NOVA controls Windows system settings by voice — volume, brightness, shutdown, battery. Takes screenshots on command.

**Modules:** `system_controls.py`, `screenshot_tools.py`
**Stack:** `pycaw`, `psutil`, `screen_brightness_control`, `os`, `pyautogui`, `Pillow`

### T0 — Prerequisites
- [ ] `pip install pycaw psutil screen-brightness-control pyautogui Pillow`
- [ ] Run as admin may be required for brightness control on some systems
- [ ] Open `modules/system_controls.py` and `modules/screenshot_tools.py`

### T1 — Implement `system_controls.py`
- `SystemControls` class
- **Volume:**
  - `set_volume(percent)`: pycaw `ISimpleAudioVolume.SetMasterVolume(percent/100)`
  - `get_volume()`: return current volume as int 0-100
  - `mute()` / `unmute()`: toggle master mute
  - `volume_up(step=5)` / `volume_down(step=5)`: relative adjustment
- **Brightness:**
  - `set_brightness(percent)`: `screen_brightness_control.set_brightness(percent)`
  - `get_brightness()`: return current brightness
  - `brightness_up(step=10)` / `brightness_down(step=10)`
- **Power:**
  - `shutdown()`: `os.system("shutdown /s /t 5")` → speak countdown
  - `restart()`: `os.system("shutdown /r /t 5")`
  - `sleep()`: `os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")`
  - `lock_screen()`: `os.system("rundll32.exe user32.dll,LockWorkStation")`
- **System Info:**
  - `get_battery()`: `psutil.sensors_battery()` → percent + plugged status
  - `get_cpu_usage()`: `psutil.cpu_percent(interval=1)`
  - `get_ram_usage()`: `psutil.virtual_memory().percent`

### T2 — Implement `screenshot_tools.py`
- `ScreenshotTools` class
- `take_screenshot()`:
  - `pyautogui.screenshot()` → save as `screenshot_{timestamp}.png` to Desktop
  - Return `f"Screenshot saved to Desktop as {filename}"`
- `click_position(x, y)`: `pyautogui.click(x, y)` — used by gesture and voice
- `type_text(text)`: `pyautogui.typewrite(text, interval=0.05)`
- `get_desktop_path()`: `os.path.expanduser("~/Desktop")`

### T3 — Wire into NLP Router
- intent `"system"` → parse sub-action and value:
  - "Set volume to 60%" → `set_volume(60)`
  - "Mute" / "Unmute"
  - "Increase brightness" → `brightness_up()`
  - "What's my battery?" → `get_battery()`
  - "CPU usage?" → `get_cpu_usage()`
  - "Shutdown" → `shutdown()`
  - "Lock the screen" → `lock_screen()`
- intent `"screenshot"` → `screenshot_tools.take_screenshot()`

### T4 — Update `context.md`

### TEST — Day 17
- [ ] "Set volume to 50" → system volume changes to 50%
- [ ] "Mute" → audio muted; "Unmute" → audio restored
- [ ] "What's my battery?" → correct percentage and plugged status spoken
- [ ] "CPU usage?" → current % spoken
- [ ] "Increase brightness" → display brightens
- [ ] "Take a screenshot" → PNG file appears on Desktop with timestamp
- [ ] "Lock the screen" → Windows lock screen activates

### PUSH
```bash
git add .
git commit -m "Day 17: Module 16 (system controls) + Module 17 (screenshot tools) implemented"
git push origin main
```

---

## DAY 18–19 — Module 22 (Hand Gesture Engine) [2 Days]

**Goal:** Always-running background computer vision system detecting hand gestures and mapping them to OS actions — fully decoupled from voice pipeline.

**Module:** `gesture_engine.py`
**Stack:** `OpenCV`, `MediaPipe`, `pycaw`, `pyautogui`, `threading`, `queue`

### T0 — Prerequisites
- [ ] `pip install opencv-python mediapipe`
- [ ] Test webcam: `python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"`
- [ ] Open `modules/gesture_engine.py`

### T1 — Day 18: Core Gesture Detection Setup
- `GestureEngine` class
- `__init__`: init `mediapipe.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7)`, init `cv2.VideoCapture(0)`, init `queue.Queue()` for thread-safe action dispatch
- `_get_landmark_list(hand_landmarks)`: extract 21 (x, y) landmark positions as list
- `_fingers_up(landmarks)`: return list of 5 booleans (thumb, index, middle, ring, pinky) — compare tip vs knuckle y-coordinate

### T2 — Day 18: Gesture Classification Logic
Implement `_classify_gesture(landmarks, fingers)` method:
| Gesture | Detection Logic | Action |
|---------|----------------|--------|
| Open palm | All 5 fingers up | Play/resume media |
| Fist | 0 fingers up | Pause media |
| Index only | Only index extended | Volume up +5% |
| Index + middle | Two fingers extended | Scroll up |
| Three fingers | Three extended | Scroll down |
| Pinch | Thumb-index distance < 30px | Zoom in |
| OK sign | Thumb+index touching, others up | Next tab |
| Swipe left | Wrist x-delta > threshold | Previous track |
| Swipe right | Wrist x-delta > threshold | Next track |

- Thumb-index distance: `math.dist(landmarks[4], landmarks[8])`
- Volume gesture: continuous — map distance linearly to 0-100% via pycaw

### T3 — Day 18: Debouncing System
- `self.last_gesture = None`, `self.gesture_start_time = None`
- Gesture must be held for `0.4 seconds` before triggering
- `_should_trigger(gesture)`: compare with last_gesture + time elapsed
- Prevents accidental fires from brief hand movements

### T4 — Day 19: Action Dispatch System
- `_dispatch_action(gesture)`: maps gesture to action call:
  - `"play"` → `pyautogui.press("space")`
  - `"pause"` → `pyautogui.press("space")`
  - `"volume_up"` → `system_controls.volume_up()`
  - `"scroll_up"` → `pyautogui.scroll(3)`
  - `"scroll_down"` → `pyautogui.scroll(-3)`
  - `"next_tab"` → `pyautogui.hotkey("ctrl", "tab")`
  - `"prev_track"` → `pyautogui.hotkey("ctrl", "left")`
  - `"next_track"` → `pyautogui.hotkey("ctrl", "right")`
  - Continuous volume: `system_controls.set_volume(calculated_percent)`

### T5 — Day 19: Main Loop + Threading
- `_gesture_loop()`: at ~20 FPS:
  - `cap.read()` → flip frame → RGB convert
  - `hands.process(frame)` → get hand_landmarks
  - If landmarks: classify + debounce + dispatch
  - Optional: draw landmarks on frame for HUD cam feed
- `start()`: `threading.Thread(target=_gesture_loop, daemon=True).start()`
- `stop()`: set stop flag, release cap

### T6 — Day 19: HUD Cam Feed Integration
- Pass processed frame to HUD via queue for mini gesture cam display
- `hud.update_gesture_cam(frame)` — Tkinter `PhotoImage` update

### T7 — Wire into `main.py`
- Instantiate `GestureEngine` → `gesture_engine.start()` at startup alongside wake word
- No voice pipeline dependency — gesture engine operates independently

### T8 — Update `context.md`

### TEST — Days 18–19
- [ ] Camera opens and hand landmarks are detected without crashing
- [ ] Open palm detected → media plays
- [ ] Fist detected → media pauses
- [ ] Index only → volume increases by 5%
- [ ] Pinch gesture → zoom in action fires
- [ ] Debounce: quick flash of gesture does NOT trigger action
- [ ] Gesture engine runs at ~15-20 FPS in background while voice pipeline also runs
- [ ] Gesture engine stop/cleanup on NOVA exit

### PUSH
```bash
git add .
git commit -m "Days 18-19: Module 22 (gesture engine) — MediaPipe landmarks, gesture table, debounce, thread dispatch"
git push origin main
```

---

## DAY 20 — Module 24 (Activity Log) + Module 25 (Config Manager)

**Goal:** Every command is logged with full detail to SQLite. Config manager allows hot-reload of all settings without restarting.

**Modules:** `activity_log.py`, `config_manager.py`
**Stack:** `sqlite3`, `json`, `threading`

### T0 — Prerequisites
- [ ] ActivityLog table already exists from Day 5
- [ ] Open `modules/activity_log.py` and `modules/config_manager.py`

### T1 — Implement `activity_log.py`
- `ActivityLogger` class
- `log(command_text, module_triggered, response_summary, success=True)`:
  - INSERT into ActivityLog with all fields + timestamp
  - Auto-cleanup: if entry count > 1000, delete oldest 100
- `get_today()`: SELECT today's entries, format as readable list
- `get_recent(n=10)`: SELECT last n entries
- `cleanup_old(days=30)`: DELETE entries older than 30 days — run on startup

### T2 — Implement `config_manager.py`
- `ConfigManager` class
- `__init__`: load `config.json`, `apps.json`, `sites.json`, `contacts.json` into memory
- `get(key, default=None)`: dot-notation key access e.g. `get("tts.rate")`
- `set(key, value)`: update in-memory + write back to `config.json`
- `reload()`: re-read all JSON files from disk — hot-reload without restart
- `is_module_enabled(module_name)`: check `modules[name]` in config
- `add_app(name, path)`: append to `apps.json` and reload
- `add_site(name, url)`: append to `sites.json` and reload
- `add_contact(name, phone, platform="whatsapp")`: append to `contacts.json` and reload

### T3 — Replace Hardcoded Config Reads Across All Modules
- All modules that read config directly → refactor to use `config_manager.get()`
- Ensures single source of truth

### T4 — Wire Hot-Reload Command
- NLP: "Hey NOVA, reload config" → `config_manager.reload()` → speak "Configuration reloaded."

### T5 — Wire Activity Log into `main.py`
- After every command execution: call `activity_logger.log(command, module, response, success)`
- This replaces the inline `db.log_activity()` calls from Day 5

### T6 — Implement `"What did I ask you earlier?"` Query
- "Show today's log" → `activity_logger.get_today()` → speak last 5 entries

### T7 — Update `context.md`

### TEST — Day 20
- [ ] Every voice command creates an ActivityLog entry with correct module name
- [ ] "Show today's log" → last 5 commands spoken
- [ ] "What did I ask you earlier?" → last command recalled
- [ ] `config_manager.reload()` picks up changes to `apps.json` without restart
- [ ] Add new site via voice → "Add site Stack Overflow to my sites" → `sites.json` updated
- [ ] Old log entries (> 30 days) cleaned on startup
- [ ] `is_module_enabled("gesture")` returns True/False correctly

### PUSH
```bash
git add .
git commit -m "Day 20: Module 24 (activity log) + Module 25 (config manager) — hot-reload, full logging"
git push origin main
```

---

## DAY 21 — Week 3 Integration Test + Git Push

**Goal:** All Week 3 modules verified. Full NOVA pipeline with gestures, notes, reminders, calendar, system controls, and logging all working together.

### T0 — Pull latest, review all Week 3 modules

### T1 — Full Week 3 Integration Test
- Gesture engine + voice pipeline run simultaneously — verify no CPU spike or threading conflict
- Reminder engine fires correctly during voice interaction
- Activity log captures all commands from both gesture and voice pipeline

### T2 — Module Coverage Audit
Verify all 25 modules are implemented:
- [x] M1 Wake Word, [x] M2 STT, [x] M3 NLP, [x] M4 Groq, [x] M5 Weather
- [x] M6 News, [x] M7 Wikipedia, [x] M8 Web Auto, [x] M9 App Launcher, [x] M10 Email
- [x] M11 WhatsApp, [x] M12 Music, [x] M13 Notes/Reminders, [x] M14 Calendar/Tasks
- [x] M15 DateTime (within NLP), [x] M16 System Controls, [x] M17 Screenshot
- [x] M18 Clipboard, [x] M19 Translation, [x] M20 Memory, [x] M21 Personality (Day 21→Week 4)
- [x] M22 Gesture, [x] M23 HUD, [x] M24 Activity Log, [x] M25 Config Manager

> **Note:** Module 15 (DateTime/Math) and Module 21 (Personality/Jokes) are handled inline in NLP engine and Groq brain. If not explicitly separated, create thin wrapper modules on this day.

### T3 — Implement Module 15 as Explicit `datetime_calc.py`
- `get_time()`: `datetime.now().strftime("%I:%M %p")`
- `get_date()`: `datetime.now().strftime("%A, %d %B %Y")`
- `days_until(target_date_str)`: `dateparser.parse()` → delta days
- `calculate(expression)`: safe `eval()` with `ast.literal_eval` sandboxing
- Wire: intent `"datetime"` → route sub-actions

### T4 — Implement Module 21 as Explicit `personality.py`
- `get_joke()`: `pyjokes.get_joke()`
- `get_greeting()`: time-aware greeting with today's reminders summary
- `roast(name)`: Groq prompt for friendly roast
- Wire: intent `"joke"` → `get_joke()`, `"roast"` → `roast("Akif")`

### T5 — Write Week 3 Test Cases
```python
# Test 16: Note saved and retrieved from DB
# Test 17: Reminder fires within 5s of trigger time
# Test 18: Calendar event parsed for "Monday at 9 AM"
# Test 19: Task marked done updates DB correctly
# Test 20: System volume set to 40% successfully
# Test 21: Screenshot saved to Desktop as PNG
# Test 22: MediaPipe detects open palm gesture
# Test 23: Activity log entry created after command
# Test 24: Config manager hot-reload reads new apps.json
```

### T6 — Update `context.md`

### TEST — Day 21 (Full Integration)
- [ ] All 9 new test cases pass
- [ ] All 24 test cases pass total
- [ ] NOVA runs for 10+ minutes with no memory leak or crash
- [ ] Gesture engine + voice + reminders all active simultaneously

### PUSH
```bash
git add .
git commit -m "Day 21: Week 3 integration — all 25 modules implemented, M15+M21 formalized"
git push origin main
```

---
---

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WEEK 4 — Polish, Testing & Demo
# Days 22–28
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

---

## DAYS 22–23 — Bug Fixing + Edge Case Testing

**Goal:** Systematic bug hunt across all 25 modules. Fix crashes, improve error messages, handle all edge cases.

### T0 — Pull latest, run full test suite

### T1 — Day 22: Critical Bug Sweep
Go through each module and test these edge cases:

**Wake Word / STT:**
- [ ] Mic disconnected mid-session → graceful reconnection or error message
- [ ] Very noisy environment → STT falls back to Whisper
- [ ] Empty transcription (silence captured) → loop without crash

**NLP Engine:**
- [ ] Ambiguous intent (e.g., "open YouTube music") → conflict resolution
- [ ] Very long commands (100+ words) → truncated gracefully
- [ ] Non-English input → routed to translation module

**Groq Brain:**
- [ ] API rate limit hit → exponential backoff (0.5s, 1s, 2s, max 3 retries)
- [ ] API key invalid → graceful error, fallback to local NLP only
- [ ] Very long response → truncated at 300 words for TTS

**Memory System:**
- [ ] DB file corrupted → recreate schema, inform user
- [ ] Concurrent write from reminder engine + main thread → SQLite row lock handling

### T2 — Day 22: Module-Specific Edge Cases
**Weather:** API quota exceeded → cached last result
**Wikipedia:** Connection timeout → error message without crash
**Web Automation:** Browser not installed → informative error
**App Launcher:** App path doesn't exist → `"That app doesn't seem to be installed."`
**Email:** Gmail App Password wrong → `"Email authentication failed. Check your .env file."`
**WhatsApp:** WhatsApp Web session expired → `"Please log into WhatsApp Web first."`
**System Controls:** Brightness control unsupported on VM → skip with warning
**Gesture Engine:** Webcam not found → disable gracefully, HUD shows cam icon as unavailable

### T3 — Day 23: Response Quality Polish
- [ ] All TTS responses are natural, concise, < 20 words where possible
- [ ] Error messages are friendly, not technical
- [ ] Add "Did you mean X?" suggestions for fuzzy mismatches below threshold
- [ ] Startup greeting includes today's event count, pending reminders, time

### T4 — Day 23: Memory and Performance Fixes
- [ ] STT recognition takes > 4s → add `timeout=5` parameter
- [ ] Groq response takes > 5s → add "Thinking..." TTS feedback
- [ ] HUD animation choppy → reduce matplotlib FuncAnimation interval
- [ ] Gesture engine using > 15% CPU → reduce to 15 FPS cap

### T5 — Update `context.md` for all changes

### PUSH (Day 22)
```bash
git add .
git commit -m "Day 22: Bug fixes — STT fallback, Groq backoff, DB concurrency, edge case handling"
git push origin main
```

### PUSH (Day 23)
```bash
git add .
git commit -m "Day 23: Polish — TTS quality, error messages, startup greeting, response length limits"
git push origin main
```

---

## DAYS 24–25 — Performance Tuning + Threading Stability

**Goal:** NOVA runs smoothly for extended periods. No thread leaks, no memory growth, consistent response times.

### T1 — Day 24: Threading Audit
Verify thread safety across all concurrent components:

| Thread | Purpose | Priority |
|--------|---------|---------|
| Main thread | Tkinter HUD | Critical |
| Thread 2 | Wake word listener | High |
| Thread 3 | Gesture engine loop | Medium |
| Thread 4 | Reminder checker (30s) | Low |
| Thread 5 | Groq API call (async) | On-demand |

- All HUD updates via `root.after(0, fn)` — audit every module
- All DB writes use connection per thread or single shared connection with `check_same_thread=False`
- No daemon thread accesses Tkinter directly

### T2 — Day 24: Memory Profiling
- Run NOVA for 30 minutes → check RAM usage with `psutil.Process().memory_info()`
- Conversation history capped at 10 messages — verify it doesn't grow
- ActivityLog cleanup runs on startup — verify old entries deleted
- Gesture frame buffer not accumulating — verify OpenCV frames released

### T3 — Day 25: Response Time Benchmarking
Target response times:
| Command Type | Target |
|-------------|--------|
| Time/Date | < 0.5s |
| App Launch | < 1.5s |
| Weather | < 2s |
| Wikipedia | < 3s |
| Groq conversation | < 5s |

- Add `time.time()` measurements around each module call
- Log slow responses (> target) to activity log for review

### T4 — Day 25: Final Stability Test
- Run NOVA for 60 minutes continuous use — simulate real usage
- Issue 50 diverse commands across all modules
- Verify: no crashes, no zombie threads, memory stable, all modules respond

### T5 — Update `context.md`

### PUSH (Day 24)
```bash
git add .
git commit -m "Day 24: Threading audit — all HUD updates via root.after(), DB thread safety"
git push origin main
```

### PUSH (Day 25)
```bash
git add .
git commit -m "Day 25: Performance tuning — response time benchmarks, 60min stability test passed"
git push origin main
```

---

## DAYS 26–28 — Demo Preparation + Final Push

**Goal:** NOVA is demo-ready. Polished startup, clean demo script, full documentation, final GitHub release tag.

### T1 — Day 26: Demo Script Design
Prepare a structured demo sequence (10-minute presentation):

**Act 1 — Foundation (2 min)**
1. NOVA starts → HUD appears → greeting: "Good morning Akif! You have 2 events today and 1 reminder at 5 PM."
2. Wake word: "Hey NOVA, what time is it?" → spoken response
3. "Hey NOVA, tell me about artificial intelligence" → Wikipedia summary

**Act 2 — Intelligence (3 min)**
4. "Hey NOVA, what's the weather in Islamabad?" → real-time weather
5. "Hey NOVA, what's in the news today?" → NASA APOD
6. "Hey NOVA, explain recursion in simple terms" → Groq explanation
7. "Hey NOVA, translate how are you to Arabic"

**Act 3 — Automation (3 min)**
8. "Hey NOVA, open VS Code" → VS Code launches
9. "Hey NOVA, search for Python tutorials on YouTube" → YouTube search
10. "Hey NOVA, take a screenshot" → screenshot saved
11. "Hey NOVA, set volume to 60%" → volume changes
12. Gesture demo — show open palm → play, fist → pause, pinch → zoom

**Act 4 — Memory & Productivity (2 min)**
13. "Hey NOVA, remember that my favourite IDE is VS Code"
14. "Hey NOVA, what do you know about me?" → facts recalled
15. "Hey NOVA, take a note: finish demo prep by Friday"
16. "Hey NOVA, set a reminder for 6 PM to review slides"

### T2 — Day 26: Demo Mode Polish
- Ensure all demo commands work reliably (test 3× each)
- Add demo-friendly error messages ("Let me try that again...")
- Verify HUD looks clean and impressive on screen share
- Disable gesture cam feed if webcam is not available during demo

### T3 — Day 27: Final Documentation
- [ ] README.md: complete setup guide, all commands reference, architecture overview
- [ ] `planning.md`: this file — confirm all days reflect actual implementation
- [ ] `context.md`: ensure all changes documented
- [ ] `architecture.md`: Mermaid diagrams included
- [ ] Code comments: all public methods have docstrings
- [ ] `.env.example`: all variables documented with descriptions
- [ ] `tests/test_all.py`: all 24 test cases runnable with `pytest`

### T4 — Day 27: Full Test Suite Run
```bash
pip install pytest
pytest tests/test_all.py -v
```
- All 24 test cases must pass
- Fix any remaining failures
- Add 1–2 regression tests for bugs fixed in Week 4

### T5 — Day 28: Final GitHub Release
- [ ] Final code review — no hardcoded secrets, no debug `print()` statements
- [ ] `requirements.txt` — verify all pinned versions install cleanly on fresh Python 3.11
- [ ] Test fresh clone on clean machine (or VM): clone → `pip install -r requirements.txt` → `python main.py`
- [ ] Add GitHub topics: `python`, `ai`, `voice-assistant`, `nlp`, `computer-vision`, `tkinter`
- [ ] Create GitHub Release v1.0.0 with release notes

### T6 — Day 28: Final Commit + Tag
```bash
git add .
git commit -m "Day 28: NOVA AI v1.0.0 — final polish, docs complete, demo-ready"
git tag -a v1.0.0 -m "NOVA AI v1.0.0 — Semester Project Final Release"
git push origin main --tags
```

---

---

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APPENDIX
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Master Module Index

| Day | Module # | Module Name | File |
|-----|---------|-------------|------|
| 1 | — | Project Scaffold | `main.py`, configs |
| 2 | M1, M2 | Wake Word + STT | `wake_word.py`, `stt.py` |
| 3 | M3 | NLP Intent Engine + TTS | `nlp_engine.py` |
| 4 | M4 | Groq LLM Brain | `groq_brain.py` |
| 5 | M20 | SQLite Memory System | `memory_system.py` |
| 6 | M23 | HUD Interface | `hud_interface.py` |
| 7 | — | Week 1 Integration | `tests/test_all.py` |
| 8 | M5, M6 | Weather + NASA News | `weather.py`, `news.py` |
| 9 | M7, M19 | Wikipedia + Translation | `wikipedia_module.py`, `translation.py` |
| 10 | M8 | Web Automation (Selenium) | `web_automation.py` |
| 11 | M9, M18 | App Launcher + Clipboard | `app_launcher.py`, `clipboard_manager.py` |
| 12 | M10 | Email Compose + Send | `email_module.py` |
| 13 | M11, M12 | WhatsApp + Music | `whatsapp_module.py`, `music_module.py` |
| 14 | — | Week 2 Integration | `tests/test_all.py` |
| 15 | M13 | Notes + Reminders | `notes_reminders.py` |
| 16 | M14 | Calendar + Tasks | `calendar_tasks.py` |
| 17 | M16, M17 | System Controls + Screenshot | `system_controls.py`, `screenshot_tools.py` |
| 18–19 | M22 | Gesture Engine (2 days) | `gesture_engine.py` |
| 20 | M24, M25 | Activity Log + Config Manager | `activity_log.py`, `config_manager.py` |
| 21 | M15, M21 | Week 3 Integration + DateTime + Personality | `datetime_calc.py`, `personality.py` |
| 22–23 | — | Bug Fixing + Edge Cases | All modules |
| 24–25 | — | Performance + Threading | All modules |
| 26–28 | — | Demo Prep + Final Release | README, docs, v1.0.0 tag |

---

## Daily Git Commit Convention

```
Day N: Module X (short description) — what was done
```
Examples:
- `Day 2: Module 1+2 (wake word + STT) — pvporcupine thread, Google+Whisper STT`
- `Day 8: Module 5+6 (weather + NASA news) — OpenWeatherMap, APOD API`
- `Day 22: Bug fixes — STT fallback, Groq rate limit backoff`

---

## Test Case Summary

| # | Test | Module | Day |
|---|------|--------|-----|
| 1 | Wake event triggers on "Hey NOVA" | M1 | 7 |
| 2 | STT transcribes "open chrome" correctly | M2 | 7 |
| 3 | NLP classifies "open chrome" → app | M3 | 7 |
| 4 | NLP extracts "Islamabad" from weather query | M3 | 7 |
| 5 | Groq responds to "what is AI" | M4 | 7 |
| 6 | DB stores and retrieves a fact | M20 | 7 |
| 7 | HUD status update without Tkinter error | M23 | 7 |
| 8 | Weather returns temp+description for Islamabad | M5 | 14 |
| 9 | NASA APOD returns non-empty title | M6 | 14 |
| 10 | Wikipedia "Python" returns 3 sentences | M7 | 14 |
| 11 | Translation "how are you" → French | M19 | 14 |
| 12 | sites.json "youtube" maps to correct URL | M8 | 14 |
| 13 | App launcher fuzzy matches "visual studio" | M9 | 14 |
| 14 | Clipboard write → read returns same text | M18 | 14 |
| 15 | Email draft has non-empty subject + body | M10 | 14 |
| 16 | Note saved and retrieved from DB | M13 | 21 |
| 17 | Reminder fires within 5s of trigger time | M13 | 21 |
| 18 | Calendar event parsed for "Monday at 9 AM" | M14 | 21 |
| 19 | Task mark done updates DB correctly | M14 | 21 |
| 20 | System volume set to 40% | M16 | 21 |
| 21 | Screenshot saved to Desktop as PNG | M17 | 21 |
| 22 | MediaPipe detects open palm gesture | M22 | 21 |
| 23 | Activity log entry after command | M24 | 21 |
| 24 | Config manager hot-reload reads new apps.json | M25 | 21 |

---

*NOVA AI — Semester Project | Python 3.11 | Windows | All Free Tools*
*Planning Document v1.0 — 28-Day Implementation Roadmap*