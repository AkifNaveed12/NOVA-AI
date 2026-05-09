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


# ── Intent routing tables ─────────────────────────────────────────

LOCAL_INTENTS = {
    "weather", "news", "wikipedia", "app", "web",
    "system", "screenshot", "clipboard", "music", "notes",
    "reminder", "calendar", "task", "datetime", "math",
    "translate", "whatsapp",
}

GROQ_INTENTS = {
    "email", "conversation", "creative", "code",
    "complex_qa", "joke", "roast", "memory",
}


def route(nlp_result: dict) -> str:
    """
    Central routing function. Receives NLP result dict and dispatches
    to the appropriate module handler.

    Args:
        nlp_result: dict with keys 'intent', 'entities', 'original'

    Returns:
        Response string to be spoken by TTS engine
    """
    intent = nlp_result.get("intent", "conversation")
    original = nlp_result.get("original", "")
    entities = nlp_result.get("entities", {})

    if intent in LOCAL_INTENTS:
        # Dispatch to local module
        local_response = dispatch_local(intent, entities, original)
        if local_response:
            return local_response
        else:
            return f"The local module for {intent} is not yet implemented."
            
    else:
        # Route to Groq Brain for conversation, emails, jokes, etc.
        print(f"[Core] Routing to GroqBrain: '{original}'")
        return groq_brain.chat(original)


def dispatch_local(intent: str, entities: dict, original: str = "") -> Optional[str]:
    """
    Dispatch to the correct local module handler based on intent.
    Each module is imported lazily to avoid startup cost.

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

    # ── Day 10 ────────────────────────────────────────────────────────
    if intent == "web":
        from modules.web_automation import WebAutomation
        import re
        wa = WebAutomation(_config)

        # "search YouTube for X" / "search X on YouTube"
        yt_match = re.search(
            r"(?:search|find|look up)\s+(?:for\s+)?(.+?)(?:\s+on\s+youtube)",
            original, re.IGNORECASE
        )
        if not yt_match:
            yt_match = re.search(
                r"(?:search|find)\s+(?:on\s+)?youtube\s+(?:for\s+)?(.+)",
                original, re.IGNORECASE
            )
        if yt_match:
            return wa.search_youtube(yt_match.group(1).strip())

        # "search Google for X" / "google X"
        google_match = re.search(
            r"(?:search|find|look up)\s+(?:for\s+)?(.+?)(?:\s+on\s+google)",
            original, re.IGNORECASE
        )
        if not google_match:
            google_match = re.search(
                r"(?:google|search google for)\s+(.+)",
                original, re.IGNORECASE
            )
        if google_match:
            return wa.search_google(google_match.group(1).strip())

        # "scroll down" / "scroll up"
        if "scroll down" in original.lower():
            return wa.scroll_down()
        if "scroll up" in original.lower():
            return wa.scroll_up()

        # Default: extract site name and open it
        site_name = re.sub(
            r"^(open|go to|visit|browse|launch)\s+", "",
            original, flags=re.IGNORECASE
        ).strip()
        return wa.open_site(site_name)

    # ── Day 11 ────────────────────────────────────────────────────────
    if intent == "app":
        from modules.app_launcher import AppLauncher
        import re
        al = AppLauncher(_config)
        original = entities.get("original", "")
        # Extract app name from "open X", "launch X", "start X", "run X"
        app_name = re.sub(
            r"^(open|launch|start|run)\s+", "",
            original, flags=re.IGNORECASE
        ).strip()
        return al.launch(app_name)

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

    # ── Future days ───────────────────────────────────────────────────
    # Day 12: system
    # Day 13: music
    # Day 14: screenshot
    # Day 15: notes, reminder, calendar, task, datetime
    return None
