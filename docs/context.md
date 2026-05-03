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