# NOVA AI — User Flows
> **Neural Orchestrated Voice Assistant with Autonomous Intelligence**
> Complete interaction flows covering every user scenario, routing decision, and system response

---

## How to Read This Document

Each flow uses this notation:

```
[USER ACTION]          → What the user does (speak / gesture)
[SYSTEM LAYER]         → Which internal layer handles it
[MODULE]               → Which module executes
[OUTPUT]               → What NOVA responds (TTS + HUD update)
[DB]                   → Any SQLite read/write
[BRANCH]               → Decision point — flow splits here
```

**Routing rule (always applies):**
> Every spoken command passes through NLP first.
> NLP routes to a local module directly if the intent is clear and structured.
> NLP escalates to Groq if the command is conversational, ambiguous, creative, or complex.
> Gesture engine is completely independent — it never touches the voice pipeline.

---
---

## FLOW 0 — System Startup

This is the very first thing that happens when `python main.py` is executed.

```
[USER]      Runs: python main.py

[SYSTEM]    main.py loads .env → reads GROQ_API_KEY, GMAIL, OPENWEATHER keys
[SYSTEM]    config.json loaded by ConfigManager → all module enable/disable states read
[SYSTEM]    SQLite memory.db checked → if not exists, all 8 tables created fresh
[SYSTEM]    Default user row inserted (Akif, user_id=1) if first run

[THREAD 1]  HUD Interface starts in main thread (Tkinter must be main thread)
            → Window appears: frameless, docked right side, 320px wide, full height
            → Background: #0D0D0D, semi-transparent (alpha 0.92)
            → Status indicator shows: 🔴 Sleeping
            → Clock starts ticking in top-right corner
            → Waveform animation starts — flat/idle state (low amplitude, #7B6CF6)

[THREAD 2]  WakeWordDetector starts as daemon thread
            → pvporcupine loads "hey nova" keyword model
            → PyAudio stream opens at low CPU energy scan mode
            → threading.Event initialized (wake_event, unset)

[THREAD 3]  GestureEngine starts as daemon thread
            → OpenCV VideoCapture(0) opens webcam
            → MediaPipe Hands model loads (max_num_hands=1, confidence=0.7)
            → Gesture loop starts at ~15-20 FPS
            → Mini cam feed begins updating in HUD bottom-left corner

[THREAD 4]  ReminderEngine starts as daemon thread
            → Checks reminders table every 30 seconds
            → On startup: queries today's pending reminders

[DB]        memory_system.get_facts(10) → top 10 user facts fetched
[DB]        calendar_tasks.get_events_today() → today's events fetched
[DB]        notes_reminders.get_pending_reminders() → pending reminders fetched

[MODULE 21] PersonalityModule.get_greeting() called
            → Detects current time → selects greeting tone:
              06:00–11:59 → "Good morning"
              12:00–17:59 → "Good afternoon"
              18:00–21:59 → "Good evening"
              22:00–05:59 → "Good night"
            → Builds greeting: "Good morning Akif! It's 9:05 AM.
               You have 2 events today and 1 reminder at 5 PM."

[OUTPUT]    TTS speaks greeting
[HUD]       Status → 🔵 Speaking (waveform pulses to speech amplitude)
[HUD]       Conversation panel shows NOVA greeting text in #00D4FF
[HUD]       Reminders ticker at bottom populates with today's upcoming items
[HUD]       Status → 🔴 Sleeping after greeting completes
[HUD]       Waveform returns to flat/idle

[SYSTEM]    NOVA is now fully initialized. All 4 threads running.
            Main thread blocked on wake_event.wait()
```

---

## FLOW 1 — Wake Word Detection (Every Flow Starts Here)

```
[STATE]     NOVA is sleeping — HUD shows 🔴, waveform flat

[USER]      Says: "Hey NOVA"

[THREAD 2]  pvporcupine processes audio frames continuously
            → Keyword score crosses threshold
            → threading.Event (wake_event) is SET

[MAIN]      wake_event.wait() unblocks
            → wake_event.clear() immediately (reset for next cycle)

[HUD]       Status → 🟡 Listening
[HUD]       Waveform transitions: flat → listening pulse (medium amplitude, #00D4FF)
[HUD]       Logo center node brightens (breathe animation accelerates)

[MODULE 2]  STT.listen() called
            → sr.Microphone() opens
            → recognizer.listen() with pause_threshold=0.8, energy_threshold=300
            → Microphone captures audio until silence detected

            [BRANCH] Audio captured?
            ├── YES → proceed to STT.transcribe()
            └── NO (timeout 5s) → speak "I didn't catch that. Say Hey NOVA again."
                                   → HUD: 🔴 Sleeping, waveform flat
                                   → Return to wake_event.wait()

[MODULE 2]  STT.transcribe(audio)
            → Primary: Google Web Speech API called
            [BRANCH] Internet available?
            ├── YES → Google returns text string
            └── NO  → Whisper base model runs locally (offline fallback)
                      → Slightly slower (~2-3s) but fully offline

[HUD]       Status → 🟢 Processing
[HUD]       Waveform: processing spin animation (rotating phase, #7B6CF6)

[MODULE 3]  NLP Engine receives text → classify_intent() + extract_entities()
            → Routing decision made here (see flows below)

[DB]        activity_logger.log(command_text, module, response, success)
            → Every command logged regardless of outcome

[OUTPUT]    Response spoken via pyttsx3 (offline TTS, rate=175, volume=1.0)
[HUD]       Status → 🔵 Speaking
[HUD]       Waveform: speaking pulse (high amplitude, #00D4FF, synced to speech)
[HUD]       Conversation panel: user command in #AAAAAA, NOVA response in #00D4FF

[RETURN]    After response: HUD → 🔴 Sleeping, waveform flat
            Main thread returns to wake_event.wait()
```

---

## FLOW 2 — NLP Routing Decision (The Brain Fork)

This is the core decision point that determines whether a command goes local or to Groq.

```
[INPUT]     Transcribed text arrives at nlp_engine.process(text)

[MODULE 3]  Step 1 — Tokenization
            → NLTK tokenizes text, removes stopwords

[MODULE 3]  Step 2 — Intent Classification
            → Rule-based keyword matching against INTENT_PATTERNS dict
            → spaCy NER extracts entities: GPE (city), PERSON (name),
              TIME/DATE (time), ORG (organization)
            → Returns: { intent, entities, original_text }

[MODULE 3]  Step 3 — Routing Decision

            Intent classification priority order:
            ┌─────────────────────────────────────────────────────┐
            │ PRIORITY │ INTENT      │ ROUTE TO         │         │
            ├─────────────────────────────────────────────────────┤
            │    1     │ system      │ SystemControls   │ LOCAL   │
            │    2     │ datetime    │ DateTimeCalc     │ LOCAL   │
            │    3     │ math        │ DateTimeCalc     │ LOCAL   │
            │    4     │ app         │ AppLauncher      │ LOCAL   │
            │    5     │ screenshot  │ ScreenshotTools  │ LOCAL   │
            │    6     │ clipboard   │ ClipboardManager │ LOCAL   │
            │    7     │ weather     │ WeatherModule    │ LOCAL   │
            │    8     │ news        │ NewsModule       │ LOCAL   │
            │    9     │ wikipedia   │ WikipediaModule  │ LOCAL   │
            │   10     │ translate   │ Translation      │ LOCAL   │
            │   11     │ web         │ WebAutomation    │ LOCAL   │
            │   12     │ music       │ MusicModule      │ LOCAL   │
            │   13     │ whatsapp    │ WhatsApp         │ LOCAL   │
            │   14     │ notes       │ NotesReminders   │ LOCAL   │
            │   15     │ reminder    │ NotesReminders   │ LOCAL   │
            │   16     │ calendar    │ CalendarTasks    │ LOCAL   │
            │   17     │ task        │ CalendarTasks    │ LOCAL   │
            │   18     │ memory      │ MemorySystem     │ LOCAL   │
            │   19     │ joke        │ Personality      │ LOCAL   │
            │   20     │ email       │ EmailModule      │ GROQ+   │
            │   21     │ conversation│ GroqBrain        │ GROQ    │
            │   22     │ [fallback]  │ GroqBrain        │ GROQ    │
            └─────────────────────────────────────────────────────┘

            [BRANCH]
            ├── LOCAL INTENT → Execute module directly (milliseconds)
            └── GROQ INTENT  → GroqBrain.chat(text) called
                               → Memory injected into system prompt first
                               → See Flow 3 for full Groq path
```

---

## FLOW 3 — Groq LLM Path (Complex / Conversational)

Triggered when: intent = `conversation`, `email` (draft part), or NLP confidence is low.

```
[INPUT]     text arrives at GroqBrain.chat(user_message)

[MODULE 20] MemorySystem.get_facts(10) called
            → SQLite query: SELECT top 10 facts by updated_at DESC
            → Returns: [("favorite_editor", "VS Code"), ("university", "..."), ...]

[MODULE 4]  System prompt constructed:
            ┌──────────────────────────────────────────────────────────┐
            │ You are NOVA — Neural Orchestrated Voice Assistant.      │
            │ Personality: professional, friendly, concise.            │
            │ User: Akif — Software Engineering student, Wah Cantt.   │
            │ Current datetime: {datetime.now()}                       │
            │ Known facts about Akif: {injected_memories}             │
            │ Respond in 1-3 sentences for voice output unless asked   │
            │ for longer content (emails, explanations, code).         │
            └──────────────────────────────────────────────────────────┘

[MODULE 4]  conversation_history managed (rolling window, last 10 messages)
            → {"role": "user", "content": user_message} appended

[MODULE 4]  API call: groq.chat.completions.create()
            → Model: llama3-70b-8192
            → max_tokens: 1024, temperature: 0.7
            → Messages: [system_prompt] + conversation_history[-10:]

            [BRANCH] API response?
            ├── SUCCESS → response text extracted
            ├── RATE LIMIT → exponential backoff (0.5s → 1s → 2s, max 3 retries)
            │               → speak "One moment..." during retry
            └── CONNECTION ERROR → speak "I'm having trouble connecting.
                                    Let me try locally." → fallback to NLP only

[MODULE 4]  {"role": "assistant", "content": response} appended to history

[MODULE 4]  extract_facts(conversation) called asynchronously
            → Groq asked to identify key user facts in JSON format
            → Results stored to UserFacts table in SQLite

[DB]        ConversationLog — role, content, session_id, timestamp written

[OUTPUT]    Response spoken via TTS
[HUD]       Response text displayed in conversation panel
```

---

## FLOW 4 — System Commands (NLP Local Path)

Commands like volume, brightness, shutdown, battery. Zero latency — no API call.

```
[USER]      "Hey NOVA, set volume to 60 percent"
            "Hey NOVA, mute"
            "Hey NOVA, increase brightness"
            "Hey NOVA, what's my battery?"
            "Hey NOVA, shutdown"
            "Hey NOVA, lock the screen"
            "Hey NOVA, how much RAM is being used?"

[MODULE 3]  intent = "system"
            entities extracted: action verb + value (if any)

[MODULE 16] SystemControls routes sub-action:

            ┌─────────────────────────────────────────────────────────┐
            │ COMMAND PATTERN         │ METHOD          │ LIBRARY     │
            ├─────────────────────────────────────────────────────────┤
            │ "set volume to N%"      │ set_volume(N)   │ pycaw       │
            │ "volume up/down"        │ volume_up/down()│ pycaw       │
            │ "mute / unmute"         │ mute/unmute()   │ pycaw       │
            │ "set brightness to N%"  │ set_brightness()│ screen_bc   │
            │ "brightness up/down"    │ brightness_up() │ screen_bc   │
            │ "shutdown"              │ shutdown()      │ os.system   │
            │ "restart"               │ restart()       │ os.system   │
            │ "sleep"                 │ sleep()         │ os.system   │
            │ "lock the screen"       │ lock_screen()   │ os.system   │
            │ "battery / charge"      │ get_battery()   │ psutil      │
            │ "cpu usage"             │ get_cpu_usage() │ psutil      │
            │ "ram usage"             │ get_ram_usage() │ psutil      │
            └─────────────────────────────────────────────────────────┘

Example — "shutdown":
[MODULE 16] os.system("shutdown /s /t 5")
[OUTPUT]    TTS: "Shutting down in 5 seconds, Akif. Goodbye."
[HUD]       Status → 🔴 Sleeping (final state before OS shutdown)

Example — "what's my battery?":
[MODULE 16] psutil.sensors_battery() → percent=78, plugged=True
[OUTPUT]    TTS: "Your battery is at 78 percent and plugged in."

[DB]        activity_log: command, "system_controls", response, success=True
```

---

## FLOW 5 — App Launcher (NLP Local Path)

```
[USER]      "Hey NOVA, open Chrome"
            "Hey NOVA, launch Visual Studio"
            "Hey NOVA, start Calculator"

[MODULE 3]  intent = "app"
            entity extracted: app name string

[MODULE 9]  AppLauncher.launch(app_name)
            → Load apps.json
            → rapidfuzz.process.extractOne(app_name, apps_dict.keys())
            → Match score evaluated:

            [BRANCH] Score >= 65?
            ├── YES → subprocess.Popen([executable_path])
            │         TTS: "Opening {matched_name}."
            │         HUD: conversation panel updated
            └── NO  → TTS: "I don't know that application. You can add it
                        by saying 'add app [name]'."

Example — "open Visual Studio":
            → rapidfuzz matches "Visual Studio" → "VS Code" (score: 87)
            → subprocess.Popen(["C:/Program Files/Microsoft VS Code/Code.exe"])
[OUTPUT]    TTS: "Opening VS Code."

[DB]        activity_log: "open Visual Studio", "app_launcher", "Opened VS Code", True
```

---

## FLOW 6 — Weather (NLP Local Path)

```
[USER]      "Hey NOVA, what's the weather in Islamabad?"
            "Hey NOVA, weather" (no city — uses default)
            "Hey NOVA, will it rain today?"

[MODULE 3]  intent = "weather"
            entity: GPE (city) extracted by spaCy → "Islamabad"
            If no city entity found → default_city = "Wah Cantt" from config

[MODULE 5]  WeatherModule.get_weather(city="Islamabad")
            → requests.get(OpenWeatherMap API, params={q, appid, units=metric})
            → Timeout: 5 seconds

            [BRANCH] API response?
            ├── 200 OK  → parse: temp, feels_like, humidity, description, wind
            │            → format response string
            ├── 404     → TTS: "I couldn't find weather for {city}."
            └── Timeout → TTS: "Weather service isn't responding right now."

[OUTPUT]    TTS: "It's currently 28°C in Islamabad, feels like 31°C,
                  humidity 65%, clear skies."
[HUD]       Response text displayed in conversation panel

[DB]        activity_log written
```

---

## FLOW 7 — Wikipedia Knowledge (NLP Local Path)

```
[USER]      "Hey NOVA, tell me about machine learning"
            "Hey NOVA, what is the Eiffel Tower?"
            "Hey NOVA, who is Alan Turing?"

[MODULE 3]  intent = "wikipedia"
            entity: query string extracted (everything after trigger phrase)

[MODULE 7]  WikipediaModule.search(query="machine learning")
            → wikipedia.summary(query, sentences=3)

            [BRANCH] Result type?
            ├── CLEAN RESULT     → 3-sentence summary returned
            ├── DISAMBIGUATION   → TTS: "Did you mean: {option1}, {option2},
            │                       or {option3}?"
            │                     → Wait for next wake word + clarification
            └── PAGE NOT FOUND   → TTS: "I couldn't find anything about {query}.
                                    Want me to search the web?"
                                    → If yes → WebAutomation opens Google search

[OUTPUT]    TTS: speaks 3-sentence summary
[HUD]       Full summary text displayed in conversation panel (scrollable)
```

---

## FLOW 8 — Translation (NLP Local Path)

```
[USER]      "Hey NOVA, translate 'how are you' to Arabic"
            "Hey NOVA, what does 'marhaba' mean in English?"
            "Hey NOVA, say 'good morning' in French"

[MODULE 3]  intent = "translate"
            entities: source_text (quoted or described), target_language

[MODULE 19] TranslationModule.translate(text, target_language)
            → Map language name to ISO code: "arabic" → "ar", "french" → "fr"
            → GoogleTranslator(source="auto", target=lang_code).translate(text)

            [BRANCH] Language recognized?
            ├── YES → translated text returned
            └── NO  → TTS: "I don't know that language."

[OUTPUT]    TTS: "In Arabic, 'how are you' is: [translated text]"
[HUD]       Both original and translated text displayed
```

---

## FLOW 9 — Web Automation (NLP + Selenium Path)

```
[USER]      "Hey NOVA, open YouTube"
            "Hey NOVA, search for Python tutorials on YouTube"
            "Hey NOVA, like this post"
            "Hey NOVA, scroll down"
            "Hey NOVA, comment 'great video' on this"

[MODULE 3]  intent = "web"
            entities: site name, action verb, content (if any)

[MODULE 8]  WebAutomation routes sub-action:

            ┌───────────────────────────────────────────────────────────┐
            │ COMMAND                 │ METHOD            │ LIBRARY     │
            ├───────────────────────────────────────────────────────────┤
            │ "open [site]"           │ open_site(name)   │ webbrowser  │
            │ "search [X] on YouTube" │ search_youtube()  │ Selenium    │
            │ "like this post"        │ like_current()    │ Selenium    │
            │ "comment [text]"        │ comment_on()      │ Selenium    │
            │ "scroll down/up"        │ scroll_down/up()  │ Selenium JS │
            └───────────────────────────────────────────────────────────┘

Example — "open YouTube":
[MODULE 8]  rapidfuzz matches "YouTube" → sites.json → "https://youtube.com"
            webbrowser.open("https://youtube.com")
[OUTPUT]    TTS: "Opening YouTube."

Example — "like this post":
[MODULE 8]  Selenium driver checks active tab domain
            → LinkedIn: clicks .react-button__trigger (like)
            → YouTube: clicks #like-button
[OUTPUT]    TTS: "Liked."

Example — "scroll down":
[MODULE 8]  driver.execute_script("window.scrollBy(0, 500);") × 3
[OUTPUT]    TTS: "Scrolling down."

[DB]        activity_log written
```

---

## FLOW 10 — Email Compose & Send (NLP + Groq Path)

This is a multi-turn flow — NOVA asks follow-up questions before sending.

```
[USER]      "Hey NOVA, write an email to Ali about the project meeting"

[MODULE 3]  intent = "email"
            entities: recipient = "Ali", topic = "project meeting"

[MODULE 10] EmailModule.handle_email_command(text) starts multi-turn flow:

TURN 1:
[MODULE 10] Checks: recipient known? topic known?
            If missing recipient:
[OUTPUT]    TTS: "Who should I send the email to?"
[USER]      Responds → STT captures → fills recipient

            If missing topic/details:
[OUTPUT]    TTS: "What should the email say?"
[USER]      Responds → STT captures → fills content details

TURN 2:
[MODULE 10] EmailModule.draft_email(recipient="Ali", topic, details)
            → Builds Groq prompt: "Draft a professional email to Ali about
               the project meeting. Include Subject line. Details: {user_details}"

[MODULE 4]  GroqBrain.chat(prompt)
            → Returns full email draft with Subject + Body

TURN 3:
[OUTPUT]    TTS: reads Subject and Body aloud
[HUD]       Full email draft displayed in conversation panel

[OUTPUT]    TTS: "Should I send it? Say yes or no."
[USER]      Says "yes" or "no"
[MODULE 2]  STT captures → transcribe → NLP extracts yes/no

            [BRANCH]
            ├── "YES" → EmailModule.send_email(to, subject, body)
            │           → smtplib.SMTP("smtp.gmail.com", 587)
            │           → starttls() → login(GMAIL_ADDRESS, APP_PASSWORD)
            │           → sendmail()
            │           → TTS: "Email sent successfully."
            ├── "NO"  → TTS: "Email cancelled."
            └── "EDIT"→ TTS: "What would you like to change?"
                        → Returns to TURN 2 with new details

[DB]        activity_log: "write email to Ali", "email_module", "Email sent", True
```

---

## FLOW 11 — WhatsApp Messaging (NLP Local Path)

```
[USER]      "Hey NOVA, send a WhatsApp to Mama saying I'll be home by 8"

[MODULE 3]  intent = "whatsapp"
            entities: contact = "Mama", message = "I'll be home by 8"

[MODULE 11] WhatsAppModule.send_message("Mama", "I'll be home by 8")
            → Load contacts.json
            → rapidfuzz match "Mama" against contact names

            [BRANCH] Contact found?
            ├── YES (score >= 70) → phone = "+923001234567"
            │   → pywhatkit.sendwhatmsg_instantly(phone, message,
            │                                      wait_time=10, tab_close=True)
            │   → Opens WhatsApp Web in Chrome → navigates → types → sends
            │   → TTS: "WhatsApp sent to Mama."
            └── NO  → TTS: "I don't have Mama in your contacts.
                       Say 'add contact Mama' to add them."

[DB]        activity_log written

Note: Requires Chrome open + active WhatsApp Web session.
      If WhatsApp Web not logged in → TTS: "Please log into WhatsApp Web
      in Chrome first, then try again."
```

---

## FLOW 12 — Music & Media Control (NLP Local Path)

```
[USER]      "Hey NOVA, play lo-fi hip hop on YouTube"
            "Hey NOVA, play my playlist"
            "Hey NOVA, pause"
            "Hey NOVA, next song"

[MODULE 3]  intent = "music"
            entity: sub-action + query (if play)

[MODULE 12] MusicModule routes sub-action:

            [BRANCH] Sub-action?
            ├── "play [X] on YouTube"
            │   → pywhatkit.playonyt("lo-fi hip hop")
            │   → Opens Chrome → YouTube search → autoplays first result
            │   → TTS: "Playing lo-fi hip hop on YouTube."
            │
            ├── "play my playlist" / "play local"
            │   → subprocess.Popen(["vlc", default_music_path])
            │   → TTS: "Opening your playlist in VLC."
            │
            ├── "pause" / "stop"
            │   → pyautogui.press("space")
            │   → TTS: "Paused."
            │
            ├── "resume" / "continue"
            │   → pyautogui.press("space")
            │   → TTS: "Resuming."
            │
            ├── "next" / "next song"
            │   → pyautogui.hotkey("ctrl", "right")  [VLC]
            │   → or shift+n  [YouTube]
            │   → TTS: "Next track."
            │
            └── "previous" / "go back"
                → pyautogui.hotkey("ctrl", "left")
                → TTS: "Previous track."
```

---

## FLOW 13 — Notes & Reminders (NLP + SQLite Path)

```
── NOTES SUB-FLOW ──

[USER]      "Hey NOVA, take a note: submit OOP assignment by Friday"
            "Hey NOVA, read my notes"
            "Hey NOVA, search my notes for assignment"

[MODULE 3]  intent = "notes"
[MODULE 13] NotesModule routes:

            ├── "take a note: [content]"
            │   → save_note(content="submit OOP assignment by Friday")
            │   → INSERT into Notes table
            │   → TTS: "Note saved."
            │
            ├── "read my notes"
            │   → read_notes(n=5) → SELECT last 5 notes
            │   → TTS reads each note aloud
            │
            └── "search notes for [query]"
                → search_notes(query) → SELECT WHERE content LIKE %query%
                → TTS: "I found 2 notes about assignments: ..."

── REMINDERS SUB-FLOW ──

[USER]      "Hey NOVA, set a reminder for 5 PM to call Ali"
            "Hey NOVA, remind me in 1 hour to review slides"

[MODULE 3]  intent = "reminder"
[MODULE 13] RemindersModule:
            → dateparser.parse("5 PM") → datetime object
            → INSERT into Reminders: message, trigger_at, is_done=False
            → TTS: "Reminder set for 5:00 PM — call Ali."

── REMINDER ENGINE BACKGROUND FIRING ──

[THREAD 4]  Every 30 seconds: SELECT pending reminders WHERE trigger_at <= now
            [BRANCH] Due reminder found?
            ├── YES → TTS: "Reminder: {message}"
            │         UPDATE is_done = True
            │         HUD ticker updates
            │         Waveform pulses briefly (#5DCAA5 green accent)
            └── NO  → Sleep 30 seconds, check again

[DB]        Notes table, Reminders table in memory.db
```

---

## FLOW 14 — Calendar & Tasks (NLP + SQLite Path)

```
── CALENDAR SUB-FLOW ──

[USER]      "Hey NOVA, add a calendar event: AI class on Monday at 9 AM"
            "Hey NOVA, what do I have tomorrow?"
            "Hey NOVA, show my upcoming events"

[MODULE 3]  intent = "calendar"
[MODULE 14] CalendarModule routes:

            ├── "add event: [title] on [datetime]"
            │   → dateparser.parse("Monday at 9 AM") → datetime object
            │   → INSERT into Events table
            │   → TTS: "Event added: AI class on Monday at 9:00 AM."
            │
            ├── "what do I have today?"
            │   → get_events_today() → SELECT where date = today
            │   → TTS: lists events or "You have nothing scheduled today."
            │
            └── "what do I have tomorrow?"
                → get_events_tomorrow()
                → TTS: lists tomorrow's events

── TASKS SUB-FLOW ──

[USER]      "Hey NOVA, add to my task list: finish the NOVA project"
            "Hey NOVA, what are my tasks?"
            "Hey NOVA, mark finish NOVA project as done"

[MODULE 14] TasksModule routes:

            ├── "add task: [title]"
            │   → INSERT into Tasks, is_done=False
            │   → TTS: "Task added: finish the NOVA project."
            │
            ├── "what are my tasks?"
            │   → get_pending_tasks() → sorted by priority, due_date
            │   → TTS: "You have 3 pending tasks: 1. finish NOVA project..."
            │
            └── "mark [task] as done"
                → rapidfuzz match task title → UPDATE is_done=True
                → TTS: "Marked as done: finish the NOVA project."

[DB]        Events, Tasks tables in memory.db
[HUD]       Ticker updates with newly added events
```

---

## FLOW 15 — Memory System (NLP + Groq Extraction Path)

```
── EXPLICIT MEMORY STORAGE ──

[USER]      "Hey NOVA, remember that my favourite editor is VS Code"
            "Hey NOVA, remember that Ali's number is 0300-1234567"

[MODULE 3]  intent = "memory", sub-action = "store"
[MODULE 20] MemorySystem.store_fact(key, value, category)
            → INSERT OR REPLACE into UserFacts
            → TTS: "Got it. I'll remember that your favourite editor is VS Code."
[DB]        UserFacts table updated

── MEMORY RECALL ──

[USER]      "Hey NOVA, what do you know about me?"

[MODULE 20] get_facts(limit=10) → SELECT all user facts
            → TTS: "Here's what I know about you, Akif:
                    Your favourite editor is VS Code.
                    You're a Software Engineering student..."

── MEMORY DELETION ──

[USER]      "Hey NOVA, forget that I told you [X]"

[MODULE 20] delete_fact(key)
            → DELETE FROM UserFacts WHERE key LIKE %X%
            → TTS: "Done. I've forgotten that."

── AUTO MEMORY EXTRACTION (runs after every Groq conversation) ──

[MODULE 4]  After each chat() call:
            → extract_facts(conversation_text) called
            → Groq asked: "Extract key facts about the user from this
               conversation as JSON: [{key, value, category}]"
            → Each extracted fact → store_fact() silently
[DB]        UserFacts updated automatically in background

── MEMORY INJECTION (before every Groq call) ──

[MODULE 4]  Before chat():
            → get_facts(10) → top 10 facts by recency
            → Injected into system prompt
            → Groq now "knows" user context without being re-told
```

---

## FLOW 16 — Date, Time & Math (NLP Local Path)

```
[USER]      "Hey NOVA, what time is it?"
            "Hey NOVA, what's today's date?"
            "Hey NOVA, how many days until Friday?"
            "Hey NOVA, what's 15 percent of 3500?"

[MODULE 3]  intent = "datetime" or "math"

[MODULE 15] DateTimeCalc routes:

            ├── "what time is it?"
            │   → datetime.now().strftime("%I:%M %p")
            │   → TTS: "It's 9:35 PM."
            │
            ├── "what's today's date?"
            │   → datetime.now().strftime("%A, %d %B %Y")
            │   → TTS: "Today is Monday, 5th May 2025."
            │
            ├── "how many days until [event]?"
            │   → dateparser.parse(event_date) → delta = target - today
            │   → TTS: "There are 12 days until Friday."
            │
            └── "what's [math expression]?"
                → extract numeric expression from text
                → safe eval with ast sandboxing
                → TTS: "15 percent of 3500 is 525."
```

---

## FLOW 17 — Screenshot & Clipboard (NLP Local Path)

```
── SCREENSHOT ──

[USER]      "Hey NOVA, take a screenshot"

[MODULE 17] ScreenshotTools.take_screenshot()
            → pyautogui.screenshot()
            → Save as: screenshot_20250505_213045.png to Desktop
            → TTS: "Screenshot saved to your Desktop."
[HUD]       Conversation panel shows filename

── CLIPBOARD ──

[USER]      "Hey NOVA, what's in my clipboard?"
            "Hey NOVA, copy hello world to clipboard"

[MODULE 18] ClipboardManager routes:

            ├── "what's in my clipboard?" / "read what I copied"
            │   → pyperclip.paste()
            │   → truncate to 200 chars for TTS
            │   → TTS: "Your clipboard contains: [text]"
            │   → Empty clipboard: "Your clipboard is empty."
            │
            └── "copy [text] to clipboard"
                → pyperclip.copy(text)
                → TTS: "Copied to clipboard."
```

---

## FLOW 18 — Personality & Small Talk (Groq Path)

```
[USER]      "Hey NOVA, tell me a joke"
            "Hey NOVA, roast me"
            "Hey NOVA, motivate me"
            "Hey NOVA, what do you think about AI?"

── JOKES (local, no API call) ──

[MODULE 3]  intent = "joke"
[MODULE 21] PersonalityModule.get_joke()
            → pyjokes.get_joke() → random offline programmer joke
            → TTS: speaks joke
            → Response time: < 0.1s (fully offline)

── ROAST (Groq) ──

[MODULE 3]  intent = "roast"
[MODULE 21] PersonalityModule.roast("Akif")
            → Groq prompt: "Give Akif a short, friendly, funny roast.
               Keep it light and clever. 2 sentences max."
            → GroqBrain.chat(prompt)
            → TTS: speaks roast

── GENERAL CONVERSATION / PHILOSOPHY (Groq) ──

[MODULE 3]  intent = "conversation" (fallback)
[MODULE 4]  GroqBrain.chat(text)
            → Full conversation with memory injection
            → See Flow 3 for complete Groq path
```

---

## FLOW 19 — NASA News (NLP Local Path)

```
[USER]      "Hey NOVA, what's in the news today?"
            "Hey NOVA, tell me something about space"
            "Hey NOVA, give me a science fact"

[MODULE 3]  intent = "news"

[MODULE 6]  NewsModule routes:

            ├── "news" / "space news"
            │   → GET https://api.nasa.gov/planetary/apod?api_key={key}
            │   → Extract: title, explanation (first 3 sentences), date
            │   → TTS: "Today's space news: {title}. {explanation}"
            │
            └── "science fact" / "random fact"
                → random.choice(hardcoded_facts_list)
                → TTS: speaks fact

            [BRANCH] API available?
            ├── YES → live APOD data
            └── NO  → TTS: "I can't reach NASA right now, but here's
                        a science fact instead." → fallback to facts list
```

---

## FLOW 20 — Config Manager & Activity Log (NLP Local Path)

```
── CONFIG HOT-RELOAD ──

[USER]      "Hey NOVA, reload config"
            "Hey NOVA, add site Stack Overflow"

[MODULE 25] ConfigManager.reload()
            → Re-reads config.json, apps.json, sites.json, contacts.json
            → All modules pick up new config from memory
            → TTS: "Configuration reloaded."

── ACTIVITY LOG QUERY ──

[USER]      "Hey NOVA, what did I ask you earlier?"
            "Hey NOVA, show me today's log"

[MODULE 24] ActivityLogger:

            ├── "what did I ask earlier?"
            │   → get_recent(n=3)
            │   → TTS: "Your last 3 commands were:
            │            Open Chrome, Weather in Islamabad, Tell me a joke."
            │
            └── "show today's log"
                → get_today() → all today's entries
                → TTS: lists commands with timestamps
                → HUD: full log shown in conversation panel

[DB]        ActivityLog table — auto-cleanup of entries > 30 days on startup
```

---

## FLOW 21 — Hand Gesture Engine (Completely Independent Path)

The gesture engine NEVER touches the voice pipeline. It runs in its own thread with its own action dispatch loop.

```
[STATE]     NOVA running — Gesture engine thread active (always, from startup)

[THREAD 3]  OpenCV captures frame from webcam (VideoCapture(0))
            → Frame flipped horizontally (mirror mode)
            → Converted to RGB
            → MediaPipe Hands.process(frame)

            [BRANCH] Hand detected?
            ├── NO  → Continue to next frame (no action)
            └── YES → 21 hand landmarks extracted as (x, y) coordinates

[THREAD 3]  _fingers_up(landmarks) called
            → Compare each fingertip (4,8,12,16,20) vs knuckle (3,6,10,14,18) y-pos
            → Returns boolean list: [thumb, index, middle, ring, pinky]

[THREAD 3]  _classify_gesture(landmarks, fingers) called:

            ┌─────────────────────────────────────────────────────────┐
            │ GESTURE              │ DETECTION         │ ACTION       │
            ├─────────────────────────────────────────────────────────┤
            │ Open palm (5 up)     │ All tips > knuckle│ Play/Resume  │
            │ Fist (0 up)          │ All fingers curled│ Pause        │
            │ Index only           │ Only index up     │ Volume +5%   │
            │ Index + middle       │ Two fingers up    │ Scroll up    │
            │ Three fingers        │ Three fingers up  │ Scroll down  │
            │ Pinch                │ dist(4,8) < 30px  │ Zoom in      │
            │ OK sign              │ Thumb+index touch │ Next tab     │
            │ Swipe left           │ Wrist x-delta > T │ Prev track   │
            │ Swipe right          │ Wrist x-delta > T │ Next track   │
            │ Thumb-index dist.    │ Continuous linear │ Volume 0-100%│
            └─────────────────────────────────────────────────────────┘

[THREAD 3]  Debouncing check:
            → Same gesture must be held ≥ 0.4 seconds before triggering
            → Prevents accidental fires from brief hand movements

            [BRANCH] Debounce passed?
            ├── NO  → Reset timer, continue watching
            └── YES → _dispatch_action(gesture) called

[THREAD 3]  Action dispatched (no voice, no wake word, no TTS):
            → Volume: pycaw ISimpleAudioVolume.SetMasterVolume()
            → Scroll: pyautogui.scroll()
            → Media: pyautogui.press("space") / hotkey
            → Tab: pyautogui.hotkey("ctrl", "tab")

[HUD]       Gesture cam feed (mini window, bottom-left of HUD) shows:
            → Live processed frame with MediaPipe skeleton overlay
            → Current detected gesture name as text label
            → Gesture icon shown in HUD corner

Note: Gesture engine acts DIRECTLY on the OS.
      It bypasses the voice pipeline entirely.
      It does NOT speak. It does NOT update the conversation panel.
      It does NOT log to ActivityLog (silent background operation).
```

---

## FLOW 22 — Error & Edge Case Handling (Universal)

Every module follows these error handling conventions.

```
── STT ERRORS ──
Silence captured          → "I didn't catch that. Say Hey NOVA to try again."
Google API unavailable    → Whisper local fallback (silent switch, no user message)
Whisper fails             → "I'm having trouble hearing you. Please try again."

── GROQ ERRORS ──
Rate limit (429)          → Exponential backoff: 0.5s → 1s → 2s (max 3 retries)
                            TTS: "One moment..." during retries
Connection error          → "I can't reach my thinking engine right now.
                             Let me handle this locally."
Invalid API key           → "There's an issue with my configuration.
                             Check the .env file."

── NETWORK ERRORS ──
No internet (weather)     → "Weather service isn't responding right now."
No internet (Wikipedia)   → "I can't access Wikipedia at the moment."
No internet (NASA)        → Fallback to hardcoded science facts list

── HARDWARE ERRORS ──
Mic disconnected          → TTS: "Microphone disconnected. Please reconnect."
                            → Wake word thread retries connection
Webcam not found          → Gesture engine disables gracefully
                            → HUD cam feed shows "Camera unavailable" message
Brightness unsupported    → TTS: "Brightness control isn't available on this display."

── FUZZY MATCH FAILURES ──
App not found (score<65)  → "I don't know that application. You can add it
                             to apps.json or say 'add app [name]'."
Site not found            → "I don't have that site. Say 'open browser' and
                             I'll take you to Google."
Contact not found         → "I don't have that contact. Say 'add contact
                             [name]' to add them."

── DATABASE ERRORS ──
DB file corrupted         → Recreate all tables (data loss warning spoken)
Concurrent write conflict → SQLite WAL mode handles this automatically
```

---

## FLOW 23 — Complete Session Lifecycle

```
START
  │
  ▼
System Startup (Flow 0)
  → HUD appears, 4 threads start, greeting spoken
  │
  ▼
NOVA SLEEPING 🔴
  → wake_event.wait() blocks main thread
  → Gesture engine runs continuously (independent)
  → Reminder engine checks every 30s (independent)
  │
  ▼ (wake word detected)
NOVA LISTENING 🟡
  → STT captures and transcribes audio
  │
  ▼
NOVA PROCESSING 🟢
  → NLP classifies intent and extracts entities
  → Routes to local module OR Groq brain
  → Module executes, response generated
  → ActivityLog entry written
  │
  ▼
NOVA SPEAKING 🔵
  → TTS speaks response (pyttsx3)
  → HUD waveform pulses to speech
  → HUD conversation panel updates
  │
  ▼
Return to SLEEPING 🔴
  → wake_event cleared and reset
  → Back to wake_event.wait()
  │
  └── Cycle repeats for every command

SHUTDOWN
  → "Hey NOVA, shutdown"
  → os.system("shutdown /s /t 5")
  → All daemon threads terminate automatically
  → Tkinter HUD closes
  → TTS: "Shutting down. Goodbye, Akif."
```

---

*NOVA AI — User Flows v1.0*
*All flows reflect finalized 25-module architecture*
*NLP-first routing, Groq escalation, gesture fully independent*