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

# 👨‍💻 Developer

## Muhammad Akif Naveed

BS Software Engineering
COMSATS University Islamabad — Wah Campus

---

# 📌 Project Status

Current Version:

## Week 3 Complete ✅

Week 4 Stabilization & Demo Preparation In Progress 🔄

new features someone soon mobile version under development.

---

# ⭐ Future Scope

- Local offline LLM support
- Cross-platform support
- Mobile companion app
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
