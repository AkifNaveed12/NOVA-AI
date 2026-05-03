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
    # TODO: implement full routing logic
    # Stub for Day 1 — returns placeholder
    intent = nlp_result.get("intent", "conversation")
    original = nlp_result.get("original", "")

    if intent in LOCAL_INTENTS:
        return f"[LOCAL] Intent '{intent}' recognised. Module not yet implemented."
    else:
        return f"[GROQ] Routing to Groq for: '{original[:60]}'"


def dispatch_local(intent: str, entities: dict) -> Optional[str]:
    """
    Dispatch to the correct local module handler based on intent.
    Each module is imported lazily to avoid startup cost.

    Returns:
        Response string or None if module not yet implemented
    """
    # TODO Day 2+: import and call each module as it's implemented
    # Example (Day 8):
    #   if intent == "weather":
    #       from modules.weather import WeatherModule
    #       return WeatherModule().get_weather(entities.get("city"))
    return None
