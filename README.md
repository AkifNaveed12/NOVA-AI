# NOVA AI 🤖

### Neural Orchestrated Voice Assistant with Autonomous Intelligence

> A production-style Python 3.11 AI voice assistant featuring wake-word activation, NLP intent routing, Groq LLM intelligence, real-time automation, persistent SQLite memory, gesture control, pywebview cinematic HUD, and multi-threaded modular architecture.

---

# ✨ Features

NOVA AI is a modular desktop AI assistant designed to combine:

- 🎤 Voice interaction
- 🧠 NLP + LLM intelligence
- 🖥️ Windows automation
- 🌐 Web automation
- 📚 Knowledge retrieval
- 🗃️ Persistent memory
- ✋ Hand gesture control
- 📅 Productivity management
- 🎛️ System controls
- 🎨 Cinematic HUD interface

All integrated into a single local-first Python system.

---

# 🚀 Current Development Status

## ✅ Week 1 — Foundation & Core Voice Pipeline

- Wake Word Detection
- Speech-to-Text
- NLP Intent Engine
- Groq LLM Brain
- SQLite Memory System
- Cinematic HUD
- End-to-End Voice Pipeline

## ✅ Week 2 — Information & Automation

- Weather Module
- NASA News
- Wikipedia Search
- Translation System
- Web Automation
- App Launcher
- Clipboard Manager
- Email System
- WhatsApp Automation
- Music & Media Controls

## ✅ Week 3 — Productivity, Gestures & System

- Notes & Reminders
- Calendar & Task Manager
- System Controls
- Screenshot Tools
- Gesture Engine (OpenCV + MediaPipe)
- Activity Logging
- Config Manager
- Personality System
- Threading & Integration Pipeline

## 🔄 Week 4 — Final Polish & Stability

(Current Phase):

- Edge-case testing
- Stability improvements
- Performance tuning
- Demo preparation
- Documentation finalization
- Production hardening

---

# 🧠 Core Capabilities

| Category      | Features                                 |
| ------------- | ---------------------------------------- |
| Voice AI      | Wake word, STT, TTS, conversational AI   |
| Intelligence  | NLP routing, Groq LLM, memory injection  |
| Productivity  | Notes, reminders, tasks, calendar        |
| Automation    | App launch, Selenium web automation      |
| Communication | Email drafting, WhatsApp messaging       |
| Media         | YouTube playback, local music control    |
| Knowledge     | Wikipedia, NASA news, translation        |
| System        | Volume, brightness, screenshots, battery |
| Vision        | OpenCV + MediaPipe gesture control       |
| UI            | pywebview cinematic HUD                  |
| Persistence   | SQLite memory & activity logs            |

---

# 🏗️ System Architecture

```text
🎤 Wake Word
   ↓
🗣️ STT Engine
   ↓
🧠 NLP Intent Router
   ├── Local Module Execution
   └── Groq LLM Fallback
   ↓
🔊 TTS Response
   ↓
🎨 HUD Updates
   ↓
🗃️ SQLite Logging + Memory
```

---

# 🧵 Threaded Runtime Architecture

NOVA AI runs as a multi-threaded modular system:

| Thread                | Responsibility          |
| --------------------- | ----------------------- |
| Main Thread           | pywebview HUD           |
| Wake Word Thread      | Passive listening       |
| Voice Pipeline Thread | STT → NLP → Routing     |
| Reminder Thread       | Scheduled alerts        |
| Gesture Thread        | OpenCV + MediaPipe      |
| Background Logging    | SQLite activity storage |

---

# 🛠️ Tech Stack

## AI & NLP

- Groq LLaMA 3
- spaCy
- NLTK
- Whisper

## Voice

- SpeechRecognition
- pyttsx3
- gTTS
- PyAudio

## Automation

- Selenium
- PyAutoGUI
- PyWhatKit

## Vision

- OpenCV
- MediaPipe

## Database

- SQLite3

## HUD

- pywebview
- HTML/CSS/JavaScript

---

# 📂 Project Structure

```text
NOVA-AI/
├── main.py
├── nova_core.py
├── requirements.txt
├── config.json
├── modules/
├── config/
├── data/
├── docs/
├── tests/
└── assets/
```

---

# ⚡ Quick Start

## 1. Clone Repository

```bash
git clone https://github.com/AkifNaveed12/NOVA-AI.git
cd NOVA-AI
```

---

## 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

## 4. Configure Environment Variables

Copy:

```bash
copy .env.example .env
```

Fill:

```env
GROQ_API_KEY=
OPENWEATHER_API_KEY=
NASA_API_KEY=DEMO_KEY
GMAIL_ADDRESS=
GMAIL_APP_PASSWORD=
PORCUPINE_ACCESS_KEY=
```

---

## 5. Run NOVA AI

```bash
python main.py
```

---

## 6. Run the Companion App (Web / Android)

NOVA comes with a cross-platform companion app that acts as a remote control and coding assistant. 

1. Ensure your phone or browser is on the **same Wi-Fi network** as the PC.
2. In a new terminal, navigate to the app folder and start it (we use Chrome for quick testing):
   ```bash
   cd nova_app
   flutter run -d chrome
   ```
3. When the app opens, it will ask for your PC's IP and an API Key.
   - **PC IP Address:** Enter your IPv4 address (e.g., `192.168.1.42` or `127.0.0.1`). *Do not append `:8000`, the app does this automatically!*
   - **API Key:** Enter your `NOVA_API_SECRET` from your `.env` file (Default: `nova-secret-change-this`). *Do NOT enter your Groq key here!*
4. Hit Connect. You can now control your PC remotely!

### 📶 Companion App Connection Troubleshooting

If the app fails to connect and displays a `"Could not connect to NOVA"` error, follow these troubleshooting steps:

#### A. Change Network Profile to "Private"
By default, Windows blocks local network incoming connections if your Wi-Fi profile is set to **Public**. Change it to **Private**:
* **PowerShell (Run as Administrator):**
  ```powershell
  Set-NetConnectionProfile -Name "YOUR_WIFI_NAME" -NetworkCategory Private
  ```
  *(Replace `YOUR_WIFI_NAME` with your actual Wi-Fi SSID name, e.g., `"Virusonly 2"`)*
* **GUI Way:** Open Windows **Settings** → **Network & internet** → **Wi-Fi** → click on your active network → toggle **Network profile type** to **Private**.

#### B. Allow Port 8000 in Windows Firewall
You must explicitly allow incoming connections on port `8000` (FastAPI):
1. Open **PowerShell (Run as Administrator)**.
2. Run the following command:
   ```powershell
   New-NetFirewallRule -DisplayName "NOVA AI API Port 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
   ```
3. *To remove this rule later:*
   ```powershell
   Remove-NetFirewallRule -DisplayName "NOVA AI API Port 8000"
   ```

#### C. Router AP Isolation
Ensure both your PC and phone are on the same Wi-Fi subnet and your router does not have **AP Isolation** (Client Isolation) enabled, which prevents local wireless devices from communicating with each other.

---

# 🧪 Testing

Run all tests:

```bash
pytest tests/test_all.py -v
```

Current project includes:

- module validation
- integration tests
- database tests
- routing tests
- threading stability checks

---

# 🎨 HUD System

NOVA AI uses a cinematic pywebview-based floating HUD featuring:

- animated waveform
- live status indicators
- scrolling activity log
- reminder ticker
- real-time updates
- non-blocking desktop overlay

---

# ✋ Gesture Controls

Hand gestures powered by OpenCV + MediaPipe:

| Gesture               | Action         |
| --------------------- | -------------- |
| Open Palm             | Play           |
| Fist                  | Pause          |
| Index Finger          | Volume Control |
| Multi-finger gestures | System actions |

---

# 🗃️ Persistent Memory System

SQLite-backed memory architecture stores:

- user facts
- reminders
- notes
- calendar events
- tasks
- activity logs
- conversations

Memory persists across sessions.

---

# 🔒 Safety & Architecture Principles

NOVA AI follows:

- modular architecture
- thread-safe design
- local-first execution
- minimal external dependencies
- fault-tolerant module routing
- graceful fallback handling
- safe error recovery

---

# 📅 Development Methodology

The project follows a structured:

**4 Week / 28 Day Development Plan**

with:

- task-level milestones
- modular implementation
- daily integration testing
- progressive stabilization
- Week 4 production hardening

Documentation includes:

- planning.md
- context.md
- architecture.md
- idea.md
- design.md
- userflows.md

---

# 🤝 Contributors & Contributions

## 👨‍💻 Muhammad Akif Naveed (Lead Developer)
BS Software Engineering, COMSATS University Islamabad — Wah Campus

*Designed and implemented the core foundations of NOVA AI, including the multi-threaded wake-word engine, NLP intent routing, pywebview cinematic HUD, and modular local execution pipelines.*

---

## 👨‍🚀 Muhammad Alyan ([@Alyan-khattak](https://github.com/Alyan-khattak))
GitHub: [Alyan-khattak](https://github.com/Alyan-khattak)

*Pioneered the transition of NOVA AI from a standalone desktop software into a distributed, local-first cross-platform ecosystem by executing the specifications in `EXPANSION_PLAN.md` and `FEATURES_PLAN.md`.*

### Key Features Developed (Desktop-to-App & API Bridge):
- **FastAPI Bridge Server:** Designed the backend API framework (`modules/api_server.py`) executing safe multithreaded command routing utilizing a `threading.Lock` around `nova_core.route()`.
- **Real-Time WebSocket Status Bridge:** Created `/ws/status` and `/ws/interactive` WebSocket protocols enabling real-time status syncing and fluid multi-turn voice/text flows.
- **Cross-Platform Flutter Companion App:** Engineered the mobile/web Flutter application (`nova_app`) featuring setup wizards, real-time status dashboards, remote voice/text command shell, and terminal interface.
- **PC File Browser API & Interface:** Created the endpoints and Flutter interface allowing users to securely browse, list, read, and open PC files remotely.
- **UDP Auto-Discovery Broadcaster:** Developed a local network UDP broadcaster permitting companion devices to discover the PC server automatically.
- **Onboarding Setup Wizard:** Designed a secure on-device configuration flow validating Groq/API credentials on the first run.
- **Agentic Coding Assistant:** Upgraded the Dev module (`modules/coding_assistant.py`) into an autonomous terminal agent with local filesystem tools (list, read, write, delete) and console command execution.
- **Self-Healing API Fallback Parser:** Engineered an XML-to-JSON fallback extraction algorithm to intercept and recover from Groq API `tool_use_failed` errors during code writing tasks.
- **System Diagnostics & Clipboard Sync:** Built real-time PC diagnostic metrics (CPU, RAM, Disk, Network) and two-way clipboard synchronization.
- **Google & YouTube Search Shortcuts:** Added dashboard search integration shortcuts to execute immediate web automations and searches on the PC browser from the mobile client.
- **Remote Mouse Trackpad Control:** Developed a low-latency `/ws/mouse` WebSocket pipeline and custom gesture/scroll tracking panel inside the Flutter app.
- **Instant Windows Index Search:** Leveraged the native Windows Collator Search database to provide instant desktop file searches (<0.05s) across secure user directories.
- **Pulsing Sci-Fi Launcher Icon:** Designed a custom orbital breathing geometry icon matching the system HUD and packaged it into Android mipmap assets.

---

# 📌 Project Status

Current Version:

## Week 4 Local-First Distributed System Complete ✅

new features someone soon mobile version under development.

---

# ⭐ Future Scope

- Local offline LLM support
- Voice cloning
- Smart home integration
- Vision-based object detection
- Cloud sync

---

# 🌐 Connect With Me

## 👨‍💻 Muhammad Akif Naveed

BS Software Engineering
COMSATS University Islamabad — Wah Campus

### 🔗 Portfolio

[Personal Portfolio](https://portfolio-muhammad-akif-naveed.vercel.app/?utm_source=chatgpt.com)

### 💼 LinkedIn

[Akif Naveed Malik — LinkedIn](https://www.linkedin.com/in/akif-naveed-malik30?utm_source=chatgpt.com)

### 🛠️ GitHub

[AkifNaveed12 — GitHub](https://github.com/AkifNaveed12?utm_source=chatgpt.com)

---

# 📜 License

Educational / Semester Project
Built using free and open-source technologies.
