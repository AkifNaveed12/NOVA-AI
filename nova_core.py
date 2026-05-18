# nova_core.py — NOVA AI Central Orchestrator
# Routing logic: NLP Engine -> Local Module OR Groq LLM
#
# Routing rule (from idea.md Section 10):
#   if confidence >= 0.75 AND intent in LOCAL_INTENTS -> local module handler
#   elif confidence < 0.75 OR intent in GROQ_INTENTS  -> Groq LLM
#
# LOCAL_INTENTS: weather, news, wikipedia, app_launch, web_open,
#   system_control, screenshot, clipboard, music, notes, reminders,
#   calendar, datetime, math, translation, whatsapp, email_send
#
# GROQ_INTENTS: email_draft, general_conversation, creative_writing,
#   code_explanation, complex_qa, personality, memory_extraction

import json
import os
import re
from typing import Optional


def load_config() -> dict:
    """Load master config.json from project root."""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Initialize GroqBrain globally so history is maintained across routes
from modules.groq_brain import GroqBrain
_config = load_config()
groq_brain = GroqBrain(_config)

# Initialize PersonalityModule once at module level
from modules.personality import PersonalityModule
_personality = PersonalityModule()


# ── Intent routing tables ─────────────────────────────────────────

LOCAL_INTENTS = {
    "weather", "news", "wikipedia", "app", "web",
    "system", "screenshot", "clipboard", "music", "notes",
    "reminder", "calendar", "task", "datetime", "math",
    "translate", "whatsapp", "email", "check_email",
    "task_queue", "introduce", "joke", "motivate", "roast",
}

GROQ_INTENTS = {
    "conversation", "creative", "code",
    "complex_qa", "joke", "roast", "memory",
}


def _split_multi_commands(original: str) -> list:
    """
    Detect and split compound commands like:
    "open LinkedIn and email Hamza"
    "open YouTube, play music, and text mama"
    into separate sub-commands.
    Returns a list of (intent, sub_text) pairs.
    """
    from modules.nlp_engine import process as nlp_process
    
    # Markers that strongly signal a new sub-command
    # Split only on " and " boundaries that start a new verb/intent
    SPLITTERS = re.compile(
        r'\b(and|then|also|plus|open|launch|start|email|text|send|play|check|search)\b',
        re.IGNORECASE
    )
    
    # Quick check: does this sentence contain a whatsapp/email keyword alongside an open/app keyword?
    lower = original.lower()
    has_open   = any(k in lower for k in ("open", "launch", "start"))
    has_email  = any(k in lower for k in ("email", "mail to"))
    has_wa     = any(k in lower for k in ("whatsapp", "text mama", "text baba", "text hamza", "text obaid", "text ibraheem", "send message"))
    
    segments = []
    
    # If the command mixes opening apps/sites with email or whatsapp, split it
    if has_open and (has_email or has_wa):
        # Split by " and "
        parts = re.split(r'\band\b', original, flags=re.IGNORECASE)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            sub_result = nlp_process(part)
            segments.append((sub_result["intent"], part, sub_result))
        return segments
    
    # Single command — no split needed
    return []


def route(
    nlp_result:   dict,
    speak_func:   Optional[callable] = None,
    listen_func:  Optional[callable] = None,
) -> str:
    """
    Central routing function. Receives NLP result dict and dispatches
    to the appropriate module handler.

    Args:
        nlp_result:  dict with keys 'intent', 'entities', 'original'
        speak_func:  optional TTS callback (required for multi-turn flows like email)
        listen_func: optional STT callback (required for multi-turn flows like email)

    Returns:
        Response string to be spoken by TTS engine
    """
    intent   = nlp_result.get("intent", "conversation")
    original = nlp_result.get("original", "")
    entities = nlp_result.get("entities", {})

    # ── Multi-command detection: "open X and email Y" ─────────────────
    if intent in ("app", "web"):
        segments = _split_multi_commands(original)
        if segments:
            responses = []
            for seg_intent, seg_text, seg_result in segments:
                if seg_intent in LOCAL_INTENTS:
                    r = dispatch_local(seg_intent, seg_result["entities"], seg_text,
                                       speak_func=speak_func, listen_func=listen_func)
                    if r:
                        responses.append(r)
                else:
                    responses.append(groq_brain.chat(seg_text))
            return " ".join(responses) if responses else "Done!"

    if intent in LOCAL_INTENTS:
        local_response = dispatch_local(
            intent, entities, original,
            speak_func=speak_func,
            listen_func=listen_func,
        )
        if local_response is not None:
            return local_response
        else:
            return f"The local module for {intent} is not yet implemented."

    else:
        # Route to Groq Brain for conversation, jokes, etc.
        print(f"[Core] Routing to GroqBrain: '{original}'")
        return groq_brain.chat(original)


def dispatch_local(
    intent:      str,
    entities:    dict,
    original:    str = "",
    speak_func:  Optional[callable] = None,
    listen_func: Optional[callable] = None,
) -> Optional[str]:
    """
    Dispatch to the correct local module handler based on intent.
    Each module is imported lazily to avoid startup cost.

    speak_func / listen_func are passed through for multi-turn flows
    (currently only email). All other modules are single-turn.

    Returns:
        Response string or None if module not yet implemented
    """
    # ── Day 8 ─────────────────────────────────────────────────────────
    if intent == "weather":
        from modules.weather import WeatherModule
        city = entities.get("city") or entities.get("location") or None
        return WeatherModule(_config).get_weather(city)

    if intent == "news":
        from modules.news import NewsModule
        return NewsModule(_config).get_nasa_apod()

    # ── Day 9 ─────────────────────────────────────────────────────────
    if intent == "wikipedia":
        from modules.wikipedia_module import WikipediaModule
        # Use wiki_query extracted by NLP, fall back to the raw original text
        query = (
            entities.get("wiki_query")
            or entities.get("query")
            or entities.get("org")
            or entities.get("name")
        )
        if not query:
            # Strip common filler phrases and use what's left
            import re
            query = re.sub(
                r"^(tell me about|what is|who is|explain|describe|what are)\s+",
                "", entities.get("original", ""),
                flags=re.IGNORECASE
            ).strip()
        return WikipediaModule().search(query)

    if intent == "translate":
        from modules.translation_module import TranslationModule
        text_to_translate = entities.get("translate_text", "")
        target_lang       = entities.get("target_language", "")
        if not text_to_translate or not target_lang:
            return (
                "Please tell me what to translate and which language. "
                "For example: translate hello to French."
            )
        return TranslationModule().translate(text_to_translate, target_lang)

    # ── Day 10 & 11: Web and App (Unified) ────────────────────────────
    if intent in ("web", "app"):
        from modules.web_automation import WebAutomation
        from modules.app_launcher import AppLauncher
        import re
        wa = WebAutomation(_config)
        al = AppLauncher(_config)

        # Handle explicit web search/scroll commands
        yt_match = re.search(r"(?:search|find|look up|play)\s+(?:for\s+)?(.+?)(?:\s+on\s+youtube)", original, re.IGNORECASE)
        if not yt_match:
            yt_match = re.search(r"(?:search|find|play)\s+(?:on\s+)?youtube\s+(?:for\s+)?(.+)", original, re.IGNORECASE)
        if yt_match:
            is_play = "play" in original.lower()
            return wa.search_youtube(yt_match.group(1).strip(), play=is_play)

        google_match = re.search(r"(?:search|find|look up)\s+(?:for\s+)?(.+?)(?:\s+on\s+google)", original, re.IGNORECASE)
        if not google_match:
            google_match = re.search(r"(?:google|search google for)\s+(.+)", original, re.IGNORECASE)
        if google_match:
            return wa.search_google(google_match.group(1).strip())

        if "scroll down" in original.lower():
            return wa.scroll_down()
        if "scroll up" in original.lower():
            return wa.scroll_up()

        # Extract target name to open
        target_name = re.sub(
            r"^(open|go to|visit|browse|launch|start|run)\s+", "",
            original, flags=re.IGNORECASE
        ).strip()

        # Split multiple targets (e.g., "linkedin, edge and youtube")
        # Replace " and " with a comma, then split by comma
        raw_targets = target_name.replace(" and ", ",").split(",")
        targets = [t.strip() for t in raw_targets if t.strip()]
        
        responses = []
        for target in targets:
            # Priority 1: Check if it's a known app
            if al.is_app_known(target):
                responses.append(al.launch(target))
                continue
            
            # Priority 2: Check if it's a known site
            if wa.is_site_known(target):
                responses.append(wa.open_site(target))
                continue
                
            # Priority 3: Fallback based on original intent
            if intent == "app":
                responses.append(al.launch(target))
            else:
                responses.append(wa.open_site(target))
                
        # Combine responses into a single string for TTS
        if len(responses) == 1:
            return responses[0]
        else:
            return " ".join(responses)

    if intent == "clipboard":
        from modules.clipboard_manager import ClipboardManager
        import re
        cm = ClipboardManager(_config)
        original_lower = original.lower()
        
        # Determine if reading or writing
        if "what" in original_lower or "read" in original_lower:
            return cm.read()
        elif "copy" in original_lower or "write" in original_lower:
            # Extract text to copy: "copy X to clipboard" or "copy X"
            copy_match = re.search(r"copy\s+(.*?)(?:\s+to\s+clipboard)?$", original, re.IGNORECASE)
            if copy_match:
                text_to_copy = copy_match.group(1).strip()
                if text_to_copy:
                    return cm.write(text_to_copy)
            return "What would you like me to copy?"
        
        return "I didn't understand the clipboard command. Try saying 'read clipboard' or 'copy text'."

    # ── Day 12 ────────────────────────────────────────────────────────
    if intent in ("email", "check_email"):
        from modules.email_module import EmailModule
        em = EmailModule(_config)

        if speak_func is None or listen_func is None:
            return "Interactive voice flow is required for email commands."
            
        if intent == "check_email":
            return em.handle_check_email_command(speak_func, listen_func)

        return em.handle_email_command(
            original   = original,
            entities   = entities,
            speak_func = speak_func,
            listen_func= listen_func,
        )

    # ── Task Queue ────────────────────────────────────────────────────
    if intent == "task_queue":
        from modules.task_manager import TaskManager
        tm = TaskManager(_config)
        
        if speak_func is None or listen_func is None:
            return "Interactive voice flow is required for task dictation."
            
        return tm.handle_task_queue(speak_func, listen_func)

    # ── Future days ───────────────────────────────────────────────────
    # Day 13: whatsapp, music
    
    if intent == "whatsapp":
        from modules.whatsapp_module import WhatsAppModule
        wam = WhatsAppModule(_config)
        
        if speak_func is None or listen_func is None:
            return "Interactive voice flow is required for WhatsApp commands."
            
        return wam.handle_whatsapp_command(
            original=original,
            entities=entities,
            speak_func=speak_func,
            listen_func=listen_func
        )
        
    if intent == "music":
        if "youtube" in original.lower() or "yt" in original.lower():
            from modules.web_automation import WebAutomation
            import re
            wa = WebAutomation(_config)
            yt_match = re.search(r"(?:play|search|find)\s+(.*?)(?:\s+on\s+youtube|\s+on\s+yt)", original, re.IGNORECASE)
            song = yt_match.group(1).strip() if yt_match else original.lower().replace("play ", "").replace(" on youtube", "")
            return wa.search_youtube(song, play=True)
            
        from modules.music_module import MusicModule
        mm = MusicModule(_config)
        return mm.handle_music_command(
            original=original,
            entities=entities,
            speak_func=speak_func,
            listen_func=listen_func
        )
        
    if intent == "introduce":
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

    # ── Day 15: Notes ────────────────────────────────────────────────
    if intent == "notes":
        from modules.notes_reminders import NotesModule
        nm = NotesModule()
        lower = original.lower()

        # Determine if reading or writing
        if any(k in lower for k in ("read", "show", "what are", "tell me my", "list my")):
            return nm.read_notes()
        if any(k in lower for k in ("search", "find", "look for")):
            # Extract search query
            import re as _re
            q = _re.sub(r"^(search|find|look for)\s+(notes?|about)?\s*", "", lower).strip()
            return nm.search_notes(q) if q else nm.read_notes()

        # Default: save a new note — strip verb prefix
        import re as _re
        content = _re.sub(
            r"^(take a note|save a note|note that|write down|jot down|make a note|save this|remember this)[:\s]*",
            "", original, flags=_re.IGNORECASE
        ).strip()
        return nm.save_note(content) if content else "What would you like me to note down?"

    # ── Day 15: Reminders ────────────────────────────────────────────
    if intent == "reminder":
        from modules.notes_reminders import RemindersModule
        rm = RemindersModule()
        lower = original.lower()
        import re as _re

        # Extract: "remind me [in X / at Y] to [message]" or "set a reminder for [message] at [time]"
        # Pattern 1: "remind me in/at [time] to [message]"
        m = _re.search(
            r"remind\s+me\s+(in\s+[\w\s]+?|at\s+[\w:\s]+?)\s+to\s+(.+)",
            original, _re.IGNORECASE
        )
        if m:
            time_str = m.group(1).strip()
            message  = m.group(2).strip()
            return rm.set_reminder(message, time_str)

        # Pattern 2: "set a reminder for [time] to [message]" / "reminder at [time] [message]"
        m = _re.search(
            r"(?:set\s+(?:a\s+)?reminder|reminder)\s+(?:for\s+|in\s+|at\s+)([\w\s:]+?)\s+(?:to\s+|that\s+|—\s*)?(.+)",
            original, _re.IGNORECASE
        )
        if m:
            time_str = m.group(1).strip()
            message  = m.group(2).strip()
            return rm.set_reminder(message, time_str)

        # Ask interactively
        if speak_func and listen_func:
            speak_func("What should the reminder say?")
            message = listen_func()
            if not message:
                return "Reminder cancelled."
            speak_func("When should I remind you?")
            time_str = listen_func()
            if not time_str:
                return "Reminder cancelled."
            return rm.set_reminder(message.strip(), time_str.strip())

        return "Please tell me the reminder message and time."

    # ── Day 16: Calendar ─────────────────────────────────────────────
    if intent == "calendar":
        from modules.calendar_tasks import CalendarModule
        cm = CalendarModule()
        lower = original.lower()

        if any(k in lower for k in ("today", "what do i have today", "today's events")):
            return cm.get_events_today()
        if any(k in lower for k in ("tomorrow", "what do i have tomorrow")):
            return cm.get_events_tomorrow()
        if any(k in lower for k in ("upcoming", "next week", "this week", "my schedule")):
            return cm.get_upcoming_events()

        # Add event — extract title and time
        import re as _re
        # "add event: title on/at datetime"
        m = _re.search(
            r"(?:add\s+(?:a\s+)?(?:calendar\s+)?event|schedule)[:\s]+(.+?)(?:\s+on\s+|\s+at\s+|\s+for\s+)(.+)",
            original, _re.IGNORECASE
        )
        if m:
            return cm.add_event(m.group(1).strip(), m.group(2).strip())

        if speak_func and listen_func:
            speak_func("What's the event title?")
            title = listen_func()
            if not title:
                return "Event cancelled."
            speak_func("When is the event?")
            dt_str = listen_func()
            if not dt_str:
                return "Event cancelled."
            return cm.add_event(title.strip(), dt_str.strip())

        return "Please specify the event name and time."

    # ── Day 16: Tasks ────────────────────────────────────────────────
    if intent == "task":
        from modules.calendar_tasks import TasksModule
        tm = TasksModule()
        lower = original.lower()

        if any(k in lower for k in ("what are my tasks", "show my tasks", "pending tasks", "my to-do", "my todo")):
            return tm.get_pending_tasks()

        if any(k in lower for k in ("mark done", "mark as done", "complete task", "mark task done", "finished")):
            import re as _re
            # Extract task title/id after the verb
            task_ref = _re.sub(
                r"(mark|complete|finished?|done)\s*(task\s*|as\s*done\s*)?", "",
                lower
            ).strip()
            return tm.mark_done(task_ref) if task_ref else "Which task should I mark as done?"

        # Add task — strip verb prefix
        import re as _re
        content = _re.sub(
            r"^(add\s+(?:a\s+)?task|add\s+to\s+my\s+(?:task\s+list|to.?do)|to-?do)[:\s]*",
            "", original, flags=_re.IGNORECASE
        ).strip()
        # Parse priority
        priority = "medium"
        if "high priority" in lower:
            priority = "high"
            content = content.replace("high priority", "").strip()
        elif "low priority" in lower:
            priority = "low"
            content = content.replace("low priority", "").strip()

        return tm.add_task(content, priority) if content else "What task would you like to add?"

    # ── Day 17: System Controls ───────────────────────────────────────
    if intent == "system":
        from modules.system_controls import SystemControls
        sc = SystemControls()
        lower = original.lower()
        import re as _re

        # Volume commands
        vol_match = _re.search(r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)", lower)
        if vol_match:
            return sc.set_volume(int(vol_match.group(1)))
        if any(k in lower for k in ("volume up", "turn it up", "louder")):
            return sc.volume_up()
        if any(k in lower for k in ("volume down", "turn it down", "quieter")):
            return sc.volume_down()
        if "mute" in lower and "unmute" not in lower:
            return sc.mute()
        if "unmute" in lower:
            return sc.unmute()
        if "get volume" in lower or "what's the volume" in lower or "current volume" in lower:
            return sc.get_volume()

        # Brightness commands
        bright_match = _re.search(r"brightness\s+(?:to\s+)?(\d+)", lower)
        if bright_match:
            return sc.set_brightness(int(bright_match.group(1)))
        if "brightness up" in lower or "brighter" in lower:
            return sc.brightness_up()
        if "brightness down" in lower or "dimmer" in lower:
            return sc.brightness_down()

        # System info
        if any(k in lower for k in ("battery", "how much battery")):
            return sc.get_battery()
        if any(k in lower for k in ("cpu", "cpu usage", "processor")):
            return sc.get_cpu_usage()
        if any(k in lower for k in ("ram", "ram usage", "memory usage")):
            return sc.get_ram_usage()

        # Power
        if "shutdown" in lower:
            return sc.shutdown()
        if "restart" in lower or "reboot" in lower:
            return sc.restart()
        if "sleep" in lower:
            return sc.sleep()
        if any(k in lower for k in ("lock screen", "lock the screen", "lock computer")):
            return sc.lock_screen()

        return "I didn't understand the system command. Try: 'set volume to 50', 'mute', 'battery level', or 'lock screen'."

    # ── Day 17: Screenshot ────────────────────────────────────────────
    if intent == "screenshot":
        from modules.screenshot_tools import ScreenshotTools
        st = ScreenshotTools()
        return st.take_screenshot()

    # Day 21: datetime, math
    return None

