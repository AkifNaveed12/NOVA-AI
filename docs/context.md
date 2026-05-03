## NOVA AI — Development Changelog
> All changes documented in chronological order per planning.md

---

## Day 1 — Project Scaffold (Week 1 Setup)
**Date:** 2026-05-03
**Status:** Complete

### What was done:
- Created full folder structure (25 module stubs + config/ + data/ + assets/logo/ + tests/)
- All 25 module stubs created in modules/ with proper docstrings and # TODO markers:
  - M1: wake_word.py, M2: stt.py, M3: nlp_engine.py, M4: groq_brain.py
  - M5: weather.py, M6: news.py, M7: wikipedia_module.py, M8: web_automation.py
  - M9: app_launcher.py, M10: email_module.py, M11: whatsapp_module.py, M12: music_module.py
  - M13: notes_reminders.py, M14: calendar_tasks.py, M15: datetime_calc.py
  - M16: system_controls.py, M17: screenshot_tools.py, M18: clipboard_manager.py
  - M19: translation_module.py, M20: memory_system.py, M21: personality.py
  - M22: gesture_engine.py, M23: hud_interface.py, M24: activity_log.py, M25: config_manager.py
- config.json created at root — full master config with all module toggles, TTS/STT settings, HUD/gesture config
- config/apps.json — 18 apps registered with name, aliases, executable paths
- config/sites.json — 11 sites registered with name, aliases, URLs
- config/contacts.json — 3 sample contacts (Mama, Baba, Ali)
- .env.example — all 5 required env vars with comments and where to get each key
- .env — exists with placeholder values (never committed to git)
- requirements.txt — full pinned requirements for all 25 modules (37 packages)
- main.py — scaffold with thread architecture (wake_event, gesture_queue, reminder_queue), TODO markers per day
- nova_core.py — routing scaffold with LOCAL_INTENTS and GROQ_INTENTS tables, route() and dispatch_local() stubs
- tests/test_all.py — 10 Day 1 tests + stubs for all future test days (up to Day 21)
- data/ directory created for SQLite databases (memory.db created at runtime)

### Tests passed (Day 1):
- python main.py runs without error
- All 25 module files exist
- config.json, apps.json, sites.json, contacts.json all load correctly
- nova_core.route() returns strings for both local and Groq intents
- .env is gitignored
- data/ directory exists

---

## architecture.md
- File: architecture.md (new file)
- Added: System Architecture flowchart in Mermaid (flowchart TD)
- Added: ERD in Mermaid (erDiagram) — all 9 tables and relationships
- Reason: Mermaid-renderable version of architecture diagrams for docs

## planning.md
- File: planning.md (new file, docs/)
- Content: Full 28-day development plan — all 25 modules, task-by-task breakdown
- Structure: Each day has T0 (prereqs) -> T1...Tn (implementation) -> TEST -> PUSH
- Appendix: Master module index, git commit convention, 24 test case summary table

---

## Day 2 — wake_word.py + stt.py
**Date:** 2026-05-03
**Status:** Complete

### What was done:
- `wake_word.py`: Implemented `WakeWordDetector` class running as a daemon thread using `speech_recognition`'s energy-threshold loop (fallback since Porcupine is skipped). Uses `threading.Event` to trigger the main loop.
- `stt.py`: Implemented `SpeechToText` class with `listen()` and `transcribe()` methods. Primary uses Google Web Speech API; fallback uses local `openai-whisper` (base model) with numpy float32 conversion to avoid `soundfile` dependency.
- `main.py`: Wired wake word and STT modules. Set up the core passive-listening loop `wake_event.wait()` -> `stt.listen()` -> `stt.transcribe()` -> `print()`.

---

## Day 3 — nlp_engine.py + TTS Integration
**Date:** 2026-05-03
**Status:** Complete

### What was done:
- `nlp_engine.py`: Implemented intent classification (`classify_intent`) using NLTK stopword removal and tokenization against 21 predefined `INTENT_PATTERNS`.
- `nlp_engine.py`: Implemented entity extraction (`extract_entities`) using spaCy (`en_core_web_sm`) for NER (GPE, PERSON, TIME, ORG) and regex fallbacks.
- `main.py`: Integrated `pyttsx3` for offline TTS and added `speak()` and `speak_online()` (gTTS fallback) functions.
- `main.py`: Wired the `nlp_engine` into the core pipeline. NOVA now listens, transcribes, classifies the intent, and speaks a confirmation.
- `tests/test_all.py`: Added Day 3 unit tests for `classify_intent` and `extract_entities` to ensure proper routing logic.

---

## Day 4 — groq_brain.py (LLM Integration)
**Date:** 2026-05-03
**Status:** Complete

### What was done:
- `groq_brain.py`: Implemented `GroqBrain` class using the official Groq Python SDK and the `llama-3.3-70b-versatile` model (replaced decommissioned model).
- `groq_brain.py`: Built the system prompt setting NOVA's professional/friendly personality and implemented `chat()` with a rolling 10-message history to maintain conversation context. Added stub for `inject_memory()` (for Day 5).
- `nova_core.py`: Wired `GroqBrain` globally to preserve history across commands. Updated `route()` to forward ambiguous requests (`conversation` intent) and Groq-specific intents directly to `groq_brain.chat()`.
- `main.py`: Updated the core voice pipeline to pass the NLP output dictionary to `nova_core.route()` and speak the generated LLM response aloud using `pyttsx3`.
- `tests/test_all.py`: Updated `check_groq.py` and the main test suite to validate the new Groq model and ensure API connectivity.