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

---

## Day 5 — memory_system.py (SQLite DB Integration)

**Date:** 2026-05-03
**Status:** Complete

### What was done:

- `memory_system.py`: Implemented `DatabaseManager` using Python's built-in `sqlite3`.
- **Database Schema**: Created `data/memory.db` and defined 9 tables (`Users`, `UserFacts`, `Notes`, `Tasks`, `Events`, `Reminders`, `Contacts`, `ActivityLog`, `ConversationLog`) representing the core schema from the ERD.
- **Memory Injection**: Implemented `store_fact` and `get_facts`. Wired `main.py` to retrieve facts and inject them into `nova_core.groq_brain` at startup so NOVA natively remembers user details.
- **Activity Logging**: Added `log_activity` and `log_conversation`. Updated `main.py` to log every command, the module triggered, and the response summary into the `ActivityLog` and `ConversationLog` tables automatically.
- `tests/test_all.py`: Added Test 6 to verify SQLite connection, table creation, insertion, and retrieval of facts in an in-memory test database.

---

## Day 6 — hud_interface.py (Tkinter GUI Overlay)

**Date:** 2026-05-04
**Status:** Complete

### What was done:

- `hud_interface.py`: Implemented `NOVAHud` using `tkinter` and `matplotlib`. Created a frameless, transparent, dark-mode window docked to the right edge of the screen.
- **Animated Waveform**: Integrated a cyan polar bar chart using `matplotlib.animation.FuncAnimation` that visually reacts (speed/amplitude) depending on NOVA's current state (Sleeping, Listening, Processing, Speaking).
- **Log Interface**: Added a scrolling text widget to display the conversation history in real-time.
- `main.py`: Re-architected the main loop. Tkinter's `mainloop()` now dominates the main thread, while the core voice/listening loop was pushed to a `threading.Thread(daemon=True)`. Added safe `after()` callbacks in the HUD class to receive status updates from the background thread without crashing the UI.
- `tests/test_all.py`: Added Test 7 to verify the HUD instantiates successfully in a headless CI-safe manner.

### Day 6 Update — Full Screen HUD & Mic Latency Fix

- `hud_interface.py`: Upgraded the HUD layout to fill the entire screen (`state("zoomed")`), enlarged the waveform, centered the UI, and increased typography size.
- `main.py`, `wake_word.py`, `stt.py`: Radically refactored PyAudio stream management. A single `sr.Microphone()` instance is now opened continuously in the background at startup and shared between both the wake word and command detectors. This achieves **0.0s latency**, instantly capturing voice commands the exact millisecond the HUD turns yellow without missing any audio.

---

## Day 7 — Week 1 Integration Test + README Update

**Date:** 2026-05-09
**Status:** Complete

### What was done:

- **Full Pipeline Verified E2E**: Confirmed the complete voice pipeline works — Wake Word → STT → NLP → Groq/local stub → TTS → HUD → SQLite log → reset → loop.
- **Groq Exponential Backoff**: Rewrote `groq_brain.chat()` with 3-attempt exponential backoff (1s, 2s, 4s delays) to gracefully handle rate limits (HTTP 429). Conversation history is not corrupted on failed attempts.
- **Dynamic System Prompt**: `chat()` now rebuilds the system prompt on every call with a fresh timestamp, keeping NOVA's time-awareness accurate across long sessions.
- **`inject_memory()` Fix**: Memory facts are now cached in `_cached_facts` and re-injected into the system prompt on every single `chat()` call, ensuring NOVA never forgets user context mid-session.
- **Day 7 Integration Tests (7 new tests — 22 total, all passing)**:
  - `test_nlp_routes_to_groq_on_conversation` — conversational queries never hit unimplemented local stubs
  - `test_nlp_routes_to_local_on_app` — app commands correctly map to LOCAL_INTENTS
  - `test_groq_backoff_and_history` — verifies multi-turn history and rolling 10-message window
  - `test_db_activity_log_persists` — ActivityLog stores and retrieves entries correctly
  - `test_db_fact_survives_reload` — facts written in one session survive a full restart (new DB connection)
  - `test_nova_core_route_returns_string` — `route()` always returns a non-empty string for any input
  - `test_pipeline_entrypoint_importable` — `main.py` spec loads without side effects
- **README.md**: Complete rewrite with Week 1 status table, quick-start guide, architecture flow diagram, feature module table with status indicators, full project structure tree, and test instructions.

---

## Day 8 — weather.py + news.py (Week 2 begins)

**Date:** 2026-05-09
**Status:** Complete

### What was done:

- `modules/weather.py`: Implemented `WeatherModule` using OpenWeatherMap free API. `get_weather(city)` falls back to default city (`Wah Cantt`) when no city is given. Handles 404 (city not found), 401 (bad key), connection errors, and timeouts gracefully. Returns a natural-language TTS-ready string.
- `modules/news.py`: Implemented `NewsModule` with `get_nasa_apod()` fetching NASA Astronomy Picture of the Day (title + first 3 sentences of explanation). Added `get_science_fact()` with a 20-item offline list as fallback. Caches last successful APOD response for use when offline.
- `nova_core.py`: Wired `weather` and `news` intents into `dispatch_local()` using lazy imports.
- `tests/test_all.py`: Added 6 Day 8 tests (28 total, all passing):
  - `test_weather_live` — live weather for Islamabad via API
  - `test_weather_invalid_city` — graceful error for unknown city
  - `test_weather_default_city` — falls back when no city provided
  - `test_news_science_fact_offline` — offline fact returns from list
  - `test_news_nasa_apod_live` — live NASA APOD fetched successfully
  - `test_nova_core_weather_route` — end-to-end route via nova_core

---

## Day 9 — wikipedia_module.py + translation_module.py

**Date:** 2026-05-09
**Status:** Complete

### What was done:

- `modules/wikipedia_module.py`: Implemented `WikipediaModule` with `search(query)` returning 3-sentence summaries. Handles `DisambiguationError` (offers top 3 options), `PageError`, and empty queries gracefully. Cleans `[1]`-style references from output.
- `modules/translation_module.py`: Implemented `TranslationModule` with `translate(text, target_language)` using `deep-translator` GoogleTranslator backend. Includes a 50-language name→ISO code map covering South Asian, Middle Eastern, European, and East Asian languages. Added `detect_language()` and `get_supported_languages()` helpers.
- `modules/nlp_engine.py`: Enhanced entity extraction with 3 new regex patterns for translation (`translate X to Y`, `what does X mean in Y`, `how do you say X in Y`) and 1 for Wikipedia (`tell me about X`, `what is X`, `who is X`, `explain X`). Expanded translate intent trigger words to cover 16+ language prepositions.
- `nova_core.py`: Wired `wikipedia` and `translate` intents into `dispatch_local()` with full entity pass-through and fallback handling.
- `tests/test_all.py`: Added 9 Day 9 tests (37 total, all passing):
  - `test_wikipedia_valid_query` — live Wikipedia summary for Python programming language
  - `test_wikipedia_not_found` — graceful handling of nonsense query
  - `test_wikipedia_empty_query` — empty input returns prompt
  - `test_translation_to_french` — English→French translation works
  - `test_translation_to_urdu` — English→Urdu translation works
  - `test_translation_unknown_language` — graceful error for fake language
  - `test_nlp_extracts_translate_entities` — NLP regex extracts text + language
  - `test_nlp_extracts_wiki_query` — NLP regex extracts wiki topic
  - `test_nova_core_wikipedia_route` — end-to-end Wikipedia via nova_core

---

## Day 10 — web_automation.py + NLP intent priority fix

**Date:** 2026-05-09
**Status:** Complete

### What was done:

- `modules/web_automation.py`: Implemented `WebAutomation` with `open_site(name)` using rapidfuzz fuzzy matching against `sites.json` aliases (score threshold 65). YouTube search via `search_youtube(query)`, Google search via `search_google(query)`. Selenium lazy-init with `scroll_down()` / `scroll_up()`. Falls back to `webbrowser.open()` for speed on simple opens.
- `nova_core.py`: Wired `web` intent with regex parsing for YouTube/Google search, scroll commands, and default site opening. Updated `dispatch_local()` signature to pass `original` text for full-command parsing.
- `modules/nlp_engine.py` (**critical fix**): Reordered `INTENT_PATTERNS` — weather/news/wikipedia/translate now checked **before** datetime. Removed the generic word `"today"` from datetime triggers. Fixed "what's the weather today" being misclassified as `datetime`.
- `tests/test_all.py`: Added 4 Day 10 tests (41 total, all passing):
  - `test_web_open_known_site` — site list contains YouTube, GitHub
  - `test_web_fuzzy_match` — alias map resolves yt, github, gmail
  - `test_web_unknown_site` — graceful error for fake sites
  - `test_web_nlp_classifies_open_youtube` — go to/visit/browse → web intent

---

## Day 11 — app_launcher.py + clipboard_manager.py

**Date:** 2026-05-09
**Status:** Complete

### What was done:

- `modules/app_launcher.py`: Implemented `AppLauncher` with `launch(app_name)` using rapidfuzz fuzzy matching against `apps.json` aliases (score threshold 65). Uses `subprocess.Popen` for non-blocking app launch.
- `modules/clipboard_manager.py`: Implemented `ClipboardManager` with `read()` (truncates to 200 chars for TTS) and `write(text)` using `pyperclip`.
- `config/sites.json`: Added `Portfolio` entry mapped to the user's personal website.
- `nova_core.py`: Wired `app` intent to `AppLauncher.launch()` and `clipboard` intent to `ClipboardManager` with regex parsing for read vs write sub-actions. Fixed an issue where the `original` parameter was getting shadowed by `entities.get("original")` during local dispatch.
- `tests/test_all.py`: Added 5 Day 11 tests (46 total, all passing):
  - `test_app_launcher_list` — loads apps.json properly
  - `test_app_launcher_unknown_app` — graceful error for fake app
  - `test_clipboard_manager_write_and_read` — successfully writes and reads using pyperclip
  - `test_nova_core_app_route` — end-to-end app route via nova_core
  - `test_nova_core_clipboard_route` — end-to-end clipboard read/write route via nova_core

## Day 11 (B) — HUD Architecture Modernization

**Date:** 2026-05-09
**Status:** Complete

### Decision

The Tkinter fullscreen HUD (Day 6) blocked the entire desktop, preventing users from seeing apps and browser windows open in real time. The matplotlib waveform was CPU-heavy. A pywebview-based approach was selected: it embeds a native OS webview window, renders standard HTML/CSS/JS, and communicates back to Python via `evaluate_js()`. This required zero changes to `main.py` — the public API of `NOVAHud` is identical.

### Files changed

**`modules/hud_interface.py`** — Full replacement

- BEFORE: `NOVAHud` built on `tk.Tk()`, `overrideredirect(True)`, `state("zoomed")` fullscreen, `matplotlib.animation.FuncAnimation` waveform, `scrolledtext.ScrolledText` log, `root.after(0, fn)` for thread safety.
- AFTER: `NOVAHud` built on `webview.create_window()` (frameless, always-on-top, 380×900, `#0D0D0D` background). `update_status(state)`, `log_message(role, text)`, `update_ticker(text)` push state by calling `window.evaluate_js(js_string)`. `start()` calls `webview.start()` — blocks on main thread exactly as before.
- REASON: pywebview gives a native frameless window with full HTML/CSS/JS rendering, enabling the cinematic UI without touching the voice pipeline.
  **`modules/nova_hud.html`** — New file
- Self-contained single HTML file (no external CDN, works fully offline).
- Animated NOVA SVG logo: radial glow pulse, 5 orbiting dots (3 violet CW, 2 teal CCW), neural convergence symbol with breathe animation.
- Canvas 2D waveform: 64 radial bars, `requestAnimationFrame` loop at ~60fps. State-driven colour and amplitude: sleeping (violet, 6px), listening (gold, 28px + random), processing (green, 18px rotating), speaking (cyan, 38px + random).
- Status bar: dot + text label with CSS class-driven colour transitions; listening dot blinks at 1Hz via CSS animation.
- Live clock via JS `setInterval`.
- Scrolling command log: last 6 user/nova pairs, auto-scroll to bottom.
- Reminders ticker: CSS marquee animation, updated via `novaSetTicker()`.
- Exposes three global functions called by Python: `window.novaSetStatus(state)`, `window.novaAppendLog(role, text)`, `window.novaSetTicker(text)`.
- REASON: All UI logic lives in HTML/CSS/JS — zero Python rendering code needed.
  **`main.py`** — No changes required.
- The `hud.update_status()`, `hud.log_message()`, and `hud.start()` calls in `main.py` are identical to the old Tkinter API.

### Dependency changes

- ADDED: `pywebview` (`pip install pywebview`)
- REMOVED from active HUD: `matplotlib`, `tkinter` (still available in Python stdlib but no longer imported by the HUD module)
- Add to `requirements.txt`: `pywebview==5.1`
- Remove from `requirements.txt` HUD section: `matplotlib==3.8.3` (may still be needed for gesture cam — leave in requirements but note it is no longer a HUD dependency)

### Test update

- Test 7 (`test_hud_status_update_without_tkinter_error`) should be updated: instead of importing `NOVAHud` and calling `update_status()`, mock `webview.create_window` and verify `evaluate_js` is called with the correct JS string.
- Updated test name: `test_hud_evaluate_js_called_on_status_update`

### How future modules integrate with the HUD

All modules communicate with the HUD exclusively through `main.py`'s `hud` reference. The pattern is:

```python
# In main.py voice_pipeline() — called after any module execution:
hud.update_status("processing")
# ... module executes ...
hud.log_message("user", command_text)
hud.log_message("nova", response_text)
hud.update_status("speaking")
```

No module (weather.py, email_module.py, etc.) should import or call `hud` directly. The HUD is updated only from `main.py`'s pipeline loop. This keeps modules fully decoupled from the frontend.

For reminders (Module 13) and calendar (Module 14), the reminder engine thread should place ticker strings into the `reminder_queue` already defined in `main.py`, and `main.py` should drain the queue and call `hud.update_ticker(text)`. This preserves thread safety.

---

## Day 12 — Module 10 (Email Compose & Send)

**Date:** 2026-05-09
**Status:** Complete

### What was done

**`modules/email_module.py`** — fully implemented (replaces TODO stub):

- `EmailModule.__init__()` — loads `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` from `.env`; stores SMTP config (`smtp.gmail.com:587`)
- `draft_email(recipient, topic, details)` — builds a Groq prompt; calls `GroqBrain.chat()`; parses the `Subject:` line from the response; returns `{"subject", "body", "recipient"}`
- `send_email(to_address, subject, body)` — builds `MIMEMultipart` message; connects via `smtplib.SMTP`; calls `starttls()` → `login()` → `sendmail()`; handles `SMTPAuthenticationError`, `SMTPConnectError`, `SMTPRecipientsRefused`, and `TimeoutError` gracefully (return descriptive string, never raise)
- `handle_email_command(original, entities, speak_func, listen_func)` — full interactive multi-turn flow:
  1. Extracts recipient + topic via regex on `original` text; fills gaps with spoken follow-up questions
  2. Calls `draft_email()` and speaks a 60-word preview via `speak_func`
  3. Asks `"Should I send it?"` and listens for `"yes"` / `"no"` via `listen_func`
  4. On yes: resolves email address from `contacts.json`; falls back to asking the user; calls `send_email()`
  5. On no: returns `"Email cancelled."` string
- `has_credentials()` — returns `True` if both env vars are set
- `_resolve_address(name)` — looks up email from `config/contacts.json` by fuzzy name match

**`nova_core.py`** changes:

- `"email"` moved from `GROQ_INTENTS` → `LOCAL_INTENTS` (it now runs through the interactive local flow instead of plain Groq)
- `route()` signature extended: `route(nlp_result, speak_func=None, listen_func=None)` — optional callbacks passed through to `dispatch_local()`
- `dispatch_local()` signature extended with the same callbacks
- Email handler block added: calls `em.handle_email_command()` when callbacks are present; falls back to a descriptive string when in non-interactive mode (e.g., unit tests, CI)

**`main.py`** changes:

- Added `_listen_once()` inner function inside `voice_pipeline()` — wraps `stt.listen()` + `stt.transcribe()`; updates HUD to "listening" / "processing"; logs the follow-up utterance via `hud.log_message()`
- `nova_core.route()` call updated to pass `speak_func=speak` and `listen_func=_listen_once`

### Architecture contract enforced

- `email_module.py` does NOT import or call `hud` directly
- All HUD updates (status, log) during the multi-turn email flow happen via the `_listen_once` wrapper and `speak()` function in `main.py` which already call `hud.*` before delegating to the module

### Test coverage added (8 new tests)

| Test | Coverage |
|---|---|
| `test_email_module_importable` | API surface / public methods |
| `test_email_module_has_credentials_false` | Env var detection |
| `test_email_send_no_credentials` | Graceful error path |
| `test_email_draft_parsing` | Groq draft + subject extraction (live, skipped without key) |
| `test_email_handle_command_cancel` | Multi-turn cancel path (mocked speak/listen) |
| `test_email_handle_command_send_flow` | Multi-turn send path (SMTP mocked) |
| `test_nlp_classifies_email_intent` | NLP pattern matching for email commands |
| `test_nova_core_email_route_no_callbacks` | Graceful degradation without callbacks |

### Total test count: 54 (46 passed offline, 8 API-skipped on CI)

---

## Out-of-Order / Continuous Enhancements

**Status:** Complete

### What was done

**Music Module (`modules/music_module.py`)**:
- Implemented robust Spotify control using PyAutoGUI to type search queries and press `Down` + `Enter` to guarantee playback of the top result.
- Added intelligent intent extraction to strip verbs (e.g. removing "play " from "play my playlist").

**YouTube Autoplay (`modules/web_automation.py`)**:
- Modified `search_youtube()` to optionally extract the first video ID from the search results page and load it directly, achieving instant playback via the `music` intent.

**Background Email Polling (`main.py`)**:
- Added an `EmailPollerThread` that safely wakes NOVA and speaks announcements via the `announcement_queue` without blocking the main voice thread or entering continuous STT loops.

**Multi-App Parsing (`nova_core.py`)**:
- Upgraded the `"app"` and `"web"` intent handlers to split compound target strings (using commas and `" and "`), allowing NOVA to launch multiple apps sequentially in a single command.

**Task Dictation & Priority Engine (`modules/task_manager.py`)**:
- Implemented interactive multi-turn dictation loop (triggered by `"note down the tasks"`).
- Integrated `GroqBrain` to logically sort the dictated tasks based on chronological urgency and category (e.g., communications first).
- Sequentially executes the sorted task strings through the `nova_core` pipeline.

---

## Day 13 — Module 11 (WhatsApp)

**Status:** Complete

### What was done

**`modules/whatsapp_module.py`**:
- Implemented `WhatsAppModule` with `pywhatkit` integration.
- `find_contact(name)` — Loads `config/contacts.json` and uses `rapidfuzz` to robustly match spoken names to phone numbers with a 70% confidence threshold.
- `send_message(phone, message)` — Triggers Chrome to open `web.whatsapp.com`, waits 15 seconds for the DOM to load, types the message, and hits Enter automatically. Closes the tab afterwards.
- `handle_whatsapp_command()` — Multi-turn voice flow:
  1. Extracts target contact and message content via Regex from the NLP `original` string.
  2. Fallback to `speak_func` / `listen_func` questions if contact or message is missing.
  3. Looks up the phone number and validates.
  4. Speaks a confirmation prompt asking `"Should I send it?"`.
  5. Upon `"yes"`, triggers the `send_message` automation.

**`nova_core.py`** changes:
- Routed the `"whatsapp"` intent to `whatsapp_module.handle_whatsapp_command`.
- Maintains the same callback-injection architecture as Email for smooth multi-turn flow.

---

## Day 14 — Week 2 Integration Test

**Status:** Complete

### What was done

**`tests/test_all.py`**:
- Added `test_weather_islamabad` to verify the Weather API integration and response formatting.
- Added `test_news_nasa_apod` to verify the NASA API returns the space news string.
- Added `test_wikipedia_python` to ensure Wikipedia summary extraction works.
- Added `test_translation_french` to ensure `deep-translator` accurately translates text to target languages.
- Added `test_sites_json_loading` to verify that `config/sites.json` is parsed as a list of dictionaries and successfully mapped.
- Added `test_clipboard_rw` to verify `pyperclip` successfully reads and writes system clipboard memory.
- Added WhatsApp import and intent classification tests.

**Bug Fixes**:
- Discovered and implemented the missing `TranslationModule` for Day 9 which was an empty stub.
- Restored the `"reminder"` and `"calendar"` intent classifications in `nlp_engine.py` which were accidentally shadowed by `task_queue`.
- Re-formatted `WebAutomation` testing to iterate correctly over the new `sites.json` structure.

**Total Test Count:** 62 tests passing. All modules from Week 1 and Week 2 are completely integrated, stable, and ready for Week 3.

---

## Pre-Day-15 Addition — Module 21 personality.py (Dramatic Introduction)
**Date:** 2026-05-10
**Status:** Complete

### Files created:
- `modules/personality.py` — Full Module 21 implementation
  - `MusicManager`: pygame.mixer wrapper, plays/switches/fades 4 background tracks
  - `PersonalitySpeaker`: pyttsx3 wrapper with rate/volume presets per emotional state
  - `perform_introduction()`: 5-act scripted dramatic intro (~3 min runtime)
  - `PersonalityModule`: public API — introduce(), get_joke(), get_greeting(), get_roast_prompt()
- `setup_music.py` — One-time music downloader (project root)
- `assets/music/` — Directory containing 4 royalty-free .mp3 tracks
- `nova_core_personality_patch.py` — Reference patch file (applied, now safe to delete)

### Files modified:
- `modules/nlp_engine.py`: Added "introduce" to INTENT_PATTERNS; added introduce_phrases check in classify_intent() before conversation fallback
- `nova_core.py`: Added PersonalityModule import + `_personality` instance; added introduce/joke/motivate/roast cases to dispatch_local(); added "introduce", "joke", "motivate", "roast" to LOCAL_INTENTS
- `main.py`: Added empty-response guard for "introduce" intent in voice_pipeline(); startup greeting now uses `_personality_startup.get_greeting()`
- `requirements.txt`: Added pygame==2.5.2
- `planning.md`: Module 21 row updated to reflect dramatic intro feature

### Tests:
- Say "Hey NOVA, introduce yourself" → 5-act intro plays with music transitions
- Say "Hey NOVA, tell me a joke" → offline pyjoke returned
- Say "Hey NOVA, who are you" → same intro triggers
- After intro completes → NOVA returns to sleeping state cleanly, wake word re-arms
