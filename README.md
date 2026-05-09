# NOVA AI 🤖
### Neural Orchestrated Voice Assistant with Autonomous Intelligence

> A Python 3.11 voice-activated personal assistant with NLP-powered intent recognition,
> Groq LLM conversation, real-time web integrations, OS automation, persistent SQLite memory,
> and an animated full-screen HUD — all running locally on Windows, free and open-source.

---

## ✅ Week 1 Status — All Modules Verified

| Day | Module | Status |
|-----|--------|--------|
| Day 1 | Project Scaffold | ✅ Done |
| Day 2 | Wake Word + STT | ✅ Done |
| Day 3 | NLP Engine + TTS | ✅ Done |
| Day 4 | Groq LLM Brain | ✅ Done |
| Day 5 | SQLite Memory System | ✅ Done |
| Day 6 | HUD Interface | ✅ Done |
| Day 7 | Week 1 Integration Test | ✅ Done |

---

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/AkifNaveed12/NOVA-AI.git
cd NOVA-AI

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install all dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 4. Configure API keys
copy .env.example .env
# Open .env and fill in your keys (see Environment Variables below)

# 5. Run NOVA
python main.py
```

> 💡 **To close NOVA:** Press the `Escape` key on the HUD, or double-click the dark background.

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and fill in these values:

| Variable | Where to get it |
|----------|----------------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) — Free tier |
| `OPENWEATHER_API_KEY` | [openweathermap.org/api](https://openweathermap.org/api) — Free |
| `NASA_API_KEY` | Use `DEMO_KEY` for development |
| `GMAIL_ADDRESS` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail → Settings → App Passwords |

---

## 🧠 How It Works

```
🎤 "Hey NOVA"
    ↓
WakeWord Detector (background thread, Google Speech API)
    ↓
STT — Captures your command (shared mic, 0.0s latency)
    ↓
NLP Engine — Classifies intent + extracts entities (spaCy + NLTK)
    ↓
Router (nova_core.py)
  ├── HIGH confidence + known intent → Local Module (weather, apps, etc.)
  └── LOW confidence / conversational → Groq LLM (LLaMA 3.3-70B)
    ↓
TTS Response (pyttsx3 offline, gTTS online fallback)
    ↓
HUD Updated (status, waveform animation, activity log)
    ↓
SQLite Log (ActivityLog + ConversationLog)
    ↓
🔴 Back to Sleeping
```

---

## 🎛️ Feature Modules

| Module | Capability | Status |
|--------|-----------|--------|
| Wake Word | Activates on "Hey NOVA" | ✅ |
| Voice I/O | SpeechRecognition + pyttsx3 | ✅ |
| NLP Engine | spaCy + NLTK intent classification | ✅ |
| Groq LLM | LLaMA 3.3-70B conversation with memory | ✅ |
| SQLite Memory | Persistent user facts + activity log | ✅ |
| HUD Interface | Full-screen animated dark-mode overlay | ✅ |
| Weather | OpenWeatherMap real-time data | 🔄 Week 2 |
| Space News | NASA Open API | 🔄 Week 2 |
| Wikipedia | Quick knowledge summaries | 🔄 Week 2 |
| Web Automation | Selenium — open, search, scroll | 🔄 Week 2 |
| App Launcher | Open any Windows app by voice | 🔄 Week 3 |
| Email | AI-composed + Gmail send | 🔄 Week 3 |
| WhatsApp | Automated messaging via PyWhatKit | 🔄 Week 3 |
| Music | YouTube + local media control | 🔄 Week 3 |
| Notes & Reminders | Voice-dictated notes | 🔄 Week 3 |
| System Control | Volume, brightness, shutdown, battery | 🔄 Week 4 |
| Screenshot | Capture + save by voice | 🔄 Week 4 |
| Translation | 100+ languages via deep-translator | 🔄 Week 4 |
| Gestures | OpenCV + MediaPipe hand control | 🔄 Week 4 |

---

## 🗂️ Project Structure

```
NOVA-AI/
├── main.py                  # Entry point — threads + HUD launch
├── nova_core.py             # Central router (NLP → local OR Groq)
├── config.json              # Master config (TTS, STT, HUD, modules)
├── requirements.txt         # All dependencies (pinned)
├── .env.example             # Template for API keys
├── modules/
│   ├── wake_word.py         # "Hey NOVA" detection daemon thread
│   ├── stt.py               # Speech-to-Text (Google + Whisper fallback)
│   ├── nlp_engine.py        # Intent classification + entity extraction
│   ├── groq_brain.py        # Groq LLM with history + exponential backoff
│   ├── memory_system.py     # SQLite DatabaseManager (9 tables)
│   ├── hud_interface.py     # Tkinter full-screen animated HUD
│   └── ...                  # 19 more modules (Week 2–4)
├── config/
│   ├── apps.json            # 18 registered Windows apps
│   ├── sites.json           # 11 registered websites
│   └── contacts.json        # User contacts
├── data/
│   └── memory.db            # SQLite database (auto-created at runtime)
├── docs/
│   ├── planning.md          # 28-day development plan
│   ├── idea.md              # Full system design document
│   ├── context.md           # Daily development changelog
│   └── architecture.md      # Mermaid system diagram + ERD
└── tests/
    └── test_all.py          # 22 tests (pytest) — all passing ✅
```

---

## 🧪 Running Tests

```bash
# Activate venv first
venv\Scripts\activate

# Run all tests (non-interactive, skips mic/HUD tests safely)
pytest tests/test_all.py -v
```

All 22 tests should pass. Tests requiring a live GROQ_API_KEY are skipped gracefully on CI.

---

## 👨‍💻 Developer

**Muhammad Akif Naveed**  
BS Software Engineering — COMSATS University Islamabad, Wah Campus

---

*Built as a semester project. All tools and APIs used are free and open-source.*