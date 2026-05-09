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
        local_response = dispatch_local(intent, entities)
        if local_response:
            return local_response
        else:
            return f"The local module for {intent} is not yet implemented."
            
    else:
        # Route to Groq Brain for conversation, emails, jokes, etc.
        print(f"[Core] Routing to GroqBrain: '{original}'")
        return groq_brain.chat(original)


def dispatch_local(intent: str, entities: dict) -> Optional[str]:
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

    # ── Future days ───────────────────────────────────────────────────
    # Day 9:  wikipedia, translate
    # Day 10: web
    # Day 11: app
    # Day 12: system
    # Day 13: music
    # Day 14: screenshot, clipboard
    # Day 15: notes, reminder, calendar, task, datetime
    return None
