# NOVA AI — Dramatic Self-Introduction Feature

> Module 21 (personality.py) — Integration Reference

## Overview

NOVA's self-introduction is a 5-act dramatic performance triggered by:
"Hey NOVA, introduce yourself" / "Hey NOVA, present yourself" / "Hey NOVA, who are you"

It uses:

- pyttsx3 with variable rate/volume per act (whisper → emotional → excited → epic)
- pygame.mixer for background music that transitions between acts
- A fully scripted ~3-minute performance with comedy, emotion, and power declarations

---

## Files Placed (DO NOT MOVE)

| File                             | Location                                | Purpose                          |
| -------------------------------- | --------------------------------------- | -------------------------------- |
| `personality.py`                 | `modules/personality.py`                | Module 21 — full implementation  |
| `setup_music.py`                 | `setup_music.py` (root)                 | One-time music downloader        |
| `nova_core_personality_patch.py` | `nova_core_personality_patch.py` (root) | Reference patch — apply manually |

Music tracks (downloaded via setup_music.py):
| File | Location |
|------|----------|
| `suspense.mp3` | `assets/music/suspense.mp3` |
| `emotional.mp3` | `assets/music/emotional.mp3` |
| `joke_sting.mp3` | `assets/music/joke_sting.mp3` |
| `epic_rise.mp3` | `assets/music/epic_rise.mp3` |

---

## Integration Tasks — Follow in Order

### TASK 1 — Install new dependency

```bash
pip install pygame
```

Add to `requirements.txt`:
pygame==2.5.2

### TASK 2 — Update `modules/nlp_engine.py`

In `INTENT_PATTERNS` dict, add a new key `"introduce"` with these triggers:

```python
"introduce": [
    "introduce yourself", "present yourself", "tell me about yourself",
    "who are you", "what are you", "introduce", "presentation",
    "who is nova", "tell us about yourself", "about yourself"
],
```

In `classify_intent()` function, add this block BEFORE the `"conversation"` fallback
(it must be the second-to-last check, right before the return "conversation" line):

```python
# Check introduce intent — must be before conversation fallback
introduce_phrases = [
    "introduce yourself", "present yourself", "tell me about yourself",
    "who are you", "what are you", "who is nova", "tell us about yourself"
]
if any(phrase in text_lower for phrase in introduce_phrases):
    return "introduce"
```

### TASK 3 — Update `nova_core.py`

**3a.** Add `"introduce"`, `"joke"`, `"motivate"`, `"roast"` to `LOCAL_INTENTS` set.

**3b.** At the top of `nova_core.py`, after existing imports, add:

```python
from modules.personality import PersonalityModule
_personality = PersonalityModule()
```

**3c.** Inside `dispatch_local()`, add these elif branches (add after the existing
clipboard/app/web cases, before the final else/fallback):

```python
elif intent == "introduce":
    _personality.introduce()
    return ""   # personality.py manages its own TTS — do NOT double-speak

elif intent == "joke":
    return _personality.get_joke()

elif intent == "motivate":
    prompt = _personality.get_motivation_prompt()
    return groq_brain.chat(prompt)

elif intent == "roast":
    prompt = _personality.get_roast_prompt("Akif")
    return groq_brain.chat(prompt)
```

### TASK 4 — Update `main.py`

In `voice_pipeline()`, after `response = nova_core.route(result)`, add this guard
so that when intent is "introduce", main.py does NOT call speak() on an empty string:

```python
response = nova_core.route(result)

# Guard: personality intro manages its own TTS — skip speak()
if response == "" and result.get("intent") == "introduce":
    wake_event.clear()
    wake_word.resume()
    hud.update_status("sleeping")
    continue
```

### TASK 5 — Update startup greeting in `main.py`

Replace the existing hardcoded startup print with a call to personality greeting.
Find where NOVA speaks its startup greeting and replace with:

```python
from modules.personality import PersonalityModule
_personality_startup = PersonalityModule()
greeting = _personality_startup.get_greeting(
    user_name=config.get("user", {}).get("name", "Akif"),
    notes_count=db_manager.get_notes_count() if hasattr(db_manager, 'get_notes_count') else 0,
    reminders=[],
    events=[]
)
speak(greeting)
```

### TASK 6 — Update `planning.md`

In the module index table, find the row for Module 21 and update:

| 21 | M15, M21 | Week 3 Integration + DateTime + Personality | datetime_calc.py, personality.py |

Change the M21 description to:

| 21 | M15, M21 | Week 3 Integration + DateTime + Personality (with dramatic intro) | datetime_calc.py, personality.py |

Also add a note under the Day 21 section:

Note: personality.py was implemented as a pre-Day-15 feature addition.
It includes MusicManager (pygame), PersonalitySpeaker (pyttsx3 multi-rate),
and a 5-act scripted dramatic introduction. Music assets in assets/music/.

### TASK 7 — Update `context.md`

Add this entry AFTER the Day 14 entry:

Pre-Day-15 Addition — Module 21 personality.py (Dramatic Introduction)
Date: [today's date]
Status: Complete
Files created:

modules/personality.py — Full Module 21 implementation

MusicManager: pygame.mixer wrapper, plays/switches/fades 4 background tracks
PersonalitySpeaker: pyttsx3 wrapper with rate/volume presets per emotional state
perform_introduction(): 5-act scripted dramatic intro (~3 min runtime)
PersonalityModule: public API — introduce(), get_joke(), get_greeting(), get_roast_prompt()

setup_music.py — One-time music downloader (project root)
assets/music/ — Directory containing 4 royalty-free .mp3 tracks
nova_core_personality_patch.py — Reference patch file (applied, now safe to delete)

Files modified:

modules/nlp_engine.py: Added "introduce" to INTENT_PATTERNS; added introduce_phrases check
in classify_intent() before conversation fallback
nova_core.py: Added PersonalityModule import + \_personality instance;
added introduce/joke/motivate/roast cases to dispatch_local();
added "introduce", "joke", "motivate", "roast" to LOCAL_INTENTS
main.py: Added empty-response guard for "introduce" intent in voice_pipeline();
startup greeting now uses \_personality_startup.get_greeting()
requirements.txt: Added pygame==2.5.2
planning.md: Module 21 row updated to reflect dramatic intro feature

Tests:

Say "Hey NOVA, introduce yourself" → 5-act intro plays with music transitions
Say "Hey NOVA, tell me a joke" → offline pyjoke returned
Say "Hey NOVA, who are you" → same intro triggers
After intro completes → NOVA returns to sleeping state cleanly, wake word re-arms

### TASK 8 — Verify music paths

In `modules/personality.py`, confirm `MusicManager.TRACKS` paths match actual files:

```python
TRACKS = {
    "suspense":  "assets/music/suspense.mp3",
    "emotional": "assets/music/emotional.mp3",
    "joke":      "assets/music/joke_sting.mp3",
    "epic":      "assets/music/epic_rise.mp3",
    "silence":   None,
}
```

These are relative to the project root where `main.py` lives — no changes needed
if you ran `python setup_music.py` from the project root.

### TASK 9 — Quick standalone test

Before full pipeline test, verify intro works in isolation:

```bash
cd nova-ai
python modules/personality.py
```

Expected: 5-act introduction plays with music. No errors.

### TASK 10 — Full pipeline test

Start NOVA normally:

```bash
python main.py
```

Say: "Hey NOVA, introduce yourself"
Expected flow:

1. HUD → Listening → Processing
2. NLP classifies intent as "introduce"
3. nova_core routes to \_personality.introduce()
4. Music starts, 5 acts play sequentially (~3 min)
5. Music fades, NOVA returns to sleeping
6. HUD → Sleeping, wake_event cleared, wake_word resumed

---

## The 5-Act Script Summary

| Act                   | Music          | Voice             | Key Moment                                     |
| --------------------- | -------------- | ----------------- | ---------------------------------------------- |
| 1 — The Mystery       | Suspense drone | Whisper, 130wpm   | "Something extraordinary is about to speak"    |
| 2 — Origin Story      | Soft piano     | Emotional, 140wpm | Akif's story, the late night, the dream        |
| 3 — The Joke Break    | Comedy sting   | Excited, 200wpm   | "Controls everything except your life choices" |
| 4 — Power Declaration | Epic cinematic | Epic, 155wpm      | Every capability listed dramatically           |
| 5 — Closing Quote     | Fade out       | Whisper→Epic      | "Always listening. Always ready. I am NOVA."   |

---

## New Dependencies

| Package | Version | Purpose                                       |
| ------- | ------- | --------------------------------------------- |
| pygame  | 2.5.2   | Background music playback and track switching |

All other dependencies already in requirements.txt.
