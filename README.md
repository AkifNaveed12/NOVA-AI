# NOVA AI 🤖
### Neural Orchestrated Voice Assistant with Autonomous Intelligence

> A Python-based, voice-activated intelligent personal assistant with NLP-powered
> intent recognition, Groq LLM conversation, real-time web integrations,
> OS automation, and always-on hand gesture control.

---

## Features

| Module | Capability |
|--------|-----------|
| Wake Word | Activates on "Hey NOVA" |
| Voice I/O | SpeechRecognition + pyttsx3 |
| NLP Engine | spaCy intent classification |
| Groq LLM | LLaMA 3 powered conversation |
| Weather | OpenWeatherMap real-time data |
| Space News | NASA Open API |
| Wikipedia | Quick knowledge summaries |
| Web Automation | Selenium — open, like, comment, scroll |
| App Launcher | Open any Windows app by voice |
| Email | Compose with AI + send via Gmail |
| WhatsApp | Automated messaging via PyWhatKit |
| Music | YouTube + local media control |
| Notes | Voice-dictated notes + reminders |
| Calendar | Events and task scheduling |
| System | Volume, brightness, shutdown, battery |
| Screenshot | Capture + save by voice |
| Translation | 100+ languages via deep-translator |
| Memory | SQLite-backed user context |
| Gestures | OpenCV + MediaPipe hand control |
| HUD UI | Minimal dark always-on-top overlay |
| Activity Log | Full command history |

## Tech Stack

Python 3.11 · spaCy · NLTK · Groq API · OpenCV · MediaPipe · Tkinter ·
Selenium · SQLite · pyttsx3 · OpenWeatherMap · NASA API

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/nova-ai.git
cd nova-ai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
# Fill in your API keys in .env
python database/db_setup.py
python main.py
```

## Environment Variables
GROQ_API_KEY=your_groq_key
OPENWEATHER_API_KEY=your_owm_key
NASA_API_KEY=DEMO_KEY
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=your_app_password

## Project Structure

See `/docs/architecture.png` for full system diagram.

## Developer

Muhammad Akif Naveed — BS Software Engineering, COMSATS University Islamabad Wah Campus

---
*Built as a semester project — all tools and APIs used are free and open source.*