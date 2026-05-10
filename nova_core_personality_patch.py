# ─────────────────────────────────────────────────────────────────────────────
# nova_core.py — PATCH for Module 21 (Personality)
# Add these lines to your existing nova_core.py
# ─────────────────────────────────────────────────────────────────────────────

# 1. ADD "introduce" and "joke" to LOCAL_INTENTS at the top of nova_core.py:
#
#    LOCAL_INTENTS = {
#        ...existing intents...
#        "joke",
#        "introduce",      ← ADD THIS
#        "motivate",       ← ADD THIS
#    }

# 2. ADD lazy import + personality instance near the top (after groq_brain init):
#
#    from modules.personality import PersonalityModule
#    _personality = PersonalityModule()

# 3. ADD these cases inside dispatch_local() in nova_core.py:

def _personality_dispatch(intent: str, entities: dict, original: str, hud=None) -> str:
    """
    Handles all personality-related intents.
    Paste the body of this into your dispatch_local() if/elif chain.
    """
    from modules.personality import PersonalityModule
    # Singleton — instantiate once at module level in real nova_core.py
    _personality = PersonalityModule()

    if intent == "introduce":
        # Run in-place (blocking) — caller already set HUD to "speaking"
        _personality.introduce()
        return ""   # Empty string: main.py won't call speak() again

    elif intent == "joke":
        return _personality.get_joke()

    elif intent == "motivate":
        # Delegate to Groq with a crafted prompt
        from modules.groq_brain import GroqBrain
        prompt = _personality.get_motivation_prompt()
        return groq_brain.chat(prompt)

    elif intent == "roast":
        from modules.groq_brain import GroqBrain
        prompt = _personality.get_roast_prompt("Akif")
        return groq_brain.chat(prompt)

    return ""


# ─────────────────────────────────────────────────────────────────────────────
# nlp_engine.py — PATCH: Add "introduce" intent patterns
# Add to INTENT_PATTERNS dict in modules/nlp_engine.py
# ─────────────────────────────────────────────────────────────────────────────

INTRODUCE_PATTERNS = [
    "introduce yourself",
    "present yourself",
    "tell me about yourself",
    "who are you",
    "what are you",
    "introduce",
    "presentation",
    "who is nova",
    "tell us about yourself",
]

# In classify_intent(), add this BEFORE the "conversation" fallback:
#
#   if any(p in text_lower for p in INTRODUCE_PATTERNS):
#       return "introduce"
#
# Make sure it's checked BEFORE the generic "conversation" fallback.