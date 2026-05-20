"""
MODULE 3 — NLP Intent Engine
==============================
First brain layer. Classifies intent and extracts entities from the
transcribed command text before deciding whether to handle locally
or escalate to Groq. Uses rule-based keyword matching + spaCy NER.

Intent categories: system, web, app, email, whatsapp, music, notes,
reminder, calendar, task, datetime, math, weather, news, wikipedia,
screenshot, clipboard, translate, memory, joke, roast, conversation.

Tech: spaCy (en_core_web_sm), NLTK, dateparser
Output: dict {intent, entities, original} → nova_core router
"""

import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download NLTK data silently if missing
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('stopwords', quiet=True)

import spacy
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("[NLP] Warning: en_core_web_sm not found. Entities won't be extracted properly.")
    nlp = None

# Priority order matters! More specific intents MUST come before generic ones.
INTENT_PATTERNS = {
    # ── Tier 1: Exact phrases — must beat all single-word triggers ────
    "introduce": [
        "introduce yourself", "present yourself", "tell me about yourself",
        "who are you", "what are you", "introduce", "about yourself",
        "who is nova", "tell us about yourself", "your name",
    ],
    "config_manager": [
        "reload config", "reload settings", "reload configuration", "refresh settings",
        "update settings", "reload apps", "reload sites", "reload contacts",
    ],
    "activity_log": [
        "what did i ask you earlier", "what did i ask earlier", "show today's log",
        "show today's logs", "show my activity log", "show command history",
        "what did i say earlier", "what were my last commands", "show history",
    ],
    # WhatsApp before "app" (which catches "open")
    "whatsapp": [
        "whatsapp", "send message", "text mama", "text baba", "text hamza",
        "text obaid", "text ibraheem", "send whatsapp", "message on whatsapp",
        "send a message to", "whatsapp message", "text to", "send text",
        "send message to",
    ],
    # check_email MUST come before "email" — "check my emails" contains "email"
    "check_email": [
        "check email", "check my email", "check my emails", "read my email",
        "any updates on gmail", "new mails", "recent emails", "check inbox",
        "any new mail", "do i have emails", "show my emails", "my inbox",
        "check gmail", "check my gmail", "read my inbox",
    ],
    # ── Tier 2: High-priority specific phrases ────────────────────────
    "weather": ["weather", "temperature", "forecast", "rain", "sunny", "humid", "climate"],
    "news": ["news", "headlines", "nasa", "space news", "science news", "what's happening"],
    "wikipedia": ["what is a", "what is an", "what is the", "what is", "who is", "who was", "explain", "describe"],
    "translate": [
        "translate", "in french", "in arabic", "in urdu", "in hindi", "in spanish",
        "in german", "in chinese", "in japanese", "in korean", "in turkish",
        "in russian", "in italian", "in portuguese", "to french", "to arabic",
        "to urdu", "to hindi", "to spanish", "to german", "what does", "mean in",
    ],
    "screenshot": ["screenshot", "capture screen", "take screenshot", "take a screenshot"],
    "clipboard": ["clipboard", "what did i copy"],
    "memory": ["remember that", "forget that", "what do you know about me"],
    # ── Tier 3: Medium-priority ───────────────────────────────────────
    "music": ["play", "music", "song", "pause", "resume", "next track", "previous track"],
    "system": [
        "shutdown", "restart", "sleep", "lock screen", "lock the screen",
        "set volume", "volume to", "volume up", "volume down", "mute", "unmute",
        "brightness", "battery", "cpu usage", "ram usage", "system info",
        "what's my battery", "how much battery",
    ],
    # University portal → web (before "app" which catches "open")
    "web": [
        "go to", "visit", "browse",
        "university portal", "my university portal", "university login",
        "cuonline", "comsats portal", "student portal", "my portal",
    ],
    "app": ["launch", "start", "run", "open"],
    "email": ["email", "mail", "send email", "write email", "compose email"],
    # List / task dictation
    "task_queue": [
        "make a list", "create a list", "create a task list", "note down the tasks",
        "multiple tasks", "note down tasks", "note down", "list mode",
        "take a list", "start a list", "i have tasks", "list of tasks",
        "add to list", "task list",
    ],
    # Notes — Day 15
    "notes": [
        "take a note", "save a note", "note that", "write down", "jot down",
        "make a note", "save this", "remember this", "read my notes",
        "show my notes", "what are my notes", "search notes",
    ],
    # Reminders — Day 15
    "reminder": [
        "set a reminder", "remind me", "reminder for", "remind me at",
        "alert me at", "alert me in", "set alarm", "set an alarm",
        "remind me in", "add a reminder",
    ],
    # Calendar — Day 16
    "calendar": [
        "add event", "add a calendar event", "schedule", "meeting",
        "what do i have today", "what do i have tomorrow", "today's events",
        "upcoming events", "my schedule", "add to calendar",
    ],
    # Tasks — Day 16
    "task": [
        "add task", "add a task", "to-do", "todo", "add to my task list",
        "add to my to do", "what are my tasks", "show my tasks",
        "pending tasks", "mark done", "mark as done", "complete task",
        "mark task done", "mark complete", "mark the task",
    ],
    # ── Tier 4: Generic / low-priority ───────────────────────────────
    "datetime": ["what time", "what date", "what day", "how many days"],
    "math": ["calculate", "percent"],
    "joke": ["joke", "make me laugh", "funny"],
    "roast": ["roast me"],
}

def classify_intent(text: str) -> str:
    """Classifies the user text into one of the known intents.
    
    Uses priority-ordered pattern matching. Longer/multi-word patterns
    are checked first to prevent generic words like 'today' from
    stealing specific intents like 'weather'.
    """
    text_lower = text.lower()
    
    # Check strict math expressions via regex first
    if re.search(r'\d+\s*[\+\-\*\/]\s*\d+', text_lower):
        return "math"

    if "percent" in text_lower:
        return "math"

    if "what is the date" in text_lower or "what's the date" in text_lower or "what is today's date" in text_lower:
        return "datetime"

    # Priority-ordered matching — first match in dict order wins
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if pattern in text_lower:
                return intent

    return "conversation"

def extract_entities(text: str) -> dict:
    """Extracts relevant entities using spaCy and Regex."""
    entities = {}
    
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ("GPE", "LOC"):
                entities["city"] = ent.text
            elif ent.label_ == "PERSON":
                entities["name"] = ent.text
            elif ent.label_ in ("TIME", "DATE"):
                entities["time"] = ent.text
            elif ent.label_ == "ORG":
                entities["org"] = ent.text
                
    # Fallback/specific extractions via Regex
    # Quoted strings for web searches or wikipedia
    quotes = re.findall(r'"([^"]*)"', text)
    if quotes:
        entities["query"] = quotes[0]

    # ── Translation entities ──────────────────────────────────────────
    # Pattern: "translate 'text' to language" or "translate text to language"
    trans_match = re.search(
        r"translate\s+['\"]?(.+?)['\"]?\s+(?:to|into)\s+([a-zA-Z]+)",
        text, re.IGNORECASE
    )
    if trans_match:
        entities["translate_text"]     = trans_match.group(1).strip()
        entities["target_language"]    = trans_match.group(2).strip().lower()

    # Pattern: "what does 'word' mean in language"
    meaning_match = re.search(
        r"what\s+does\s+['\"]?(.+?)['\"]?\s+mean\s+in\s+([a-zA-Z]+)",
        text, re.IGNORECASE
    )
    if meaning_match:
        entities["translate_text"]  = meaning_match.group(1).strip()
        entities["target_language"] = meaning_match.group(2).strip().lower()

    # Pattern: "how do you say 'text' in language"
    how_say_match = re.search(
        r"how\s+(?:do\s+you\s+)?say\s+['\"]?(.+?)['\"]?\s+in\s+([a-zA-Z]+)",
        text, re.IGNORECASE
    )
    if how_say_match:
        entities["translate_text"]  = how_say_match.group(1).strip()
        entities["target_language"] = how_say_match.group(2).strip().lower()

    # ── Wikipedia query entity ────────────────────────────────────────
    # Pattern: "tell me about X", "what is X", "who is X", "explain X"
    wiki_match = re.search(
        r"(?:tell\s+me\s+about|what\s+is\s+a?n?|who\s+is|explain|describe)\s+(.+)",
        text, re.IGNORECASE
    )
    if wiki_match and "query" not in entities:
        raw = wiki_match.group(1).strip()
        # Remove trailing question marks and filler
        raw = re.sub(r'[?!.]+$', '', raw).strip()
        entities["wiki_query"] = raw

    # ── Math expression extraction ────────────────────────────────────
    math_match = re.search(r"calculate\s+(.+)", text, re.IGNORECASE)
    if math_match:
        entities["math_expr"] = math_match.group(1).strip()
    else:
        what_is_math = re.search(r"what\s+is\s+(.+)", text, re.IGNORECASE)
        candidate = what_is_math.group(1).strip() if what_is_math else text
        if re.search(r"\d", candidate) and (re.search(r"[\+\-\*\/%]", candidate) or any(k in candidate.lower() for k in ("percent", "plus", "minus", "times", "divided", "multiplied"))):
            entities["math_expr"] = re.sub(r"[?!.]+$", "", candidate).strip()

    # ── Date calculation extraction ───────────────────────────────────
    days_until_match = re.search(r"(?:how\s+many\s+)?days\s+until\s+(.+)", text, re.IGNORECASE)
    if days_until_match:
        raw_date = days_until_match.group(1).strip()
        entities["target_date"] = re.sub(r"[?!.]+$", "", raw_date).strip()

    return entities

def process(text: str) -> dict:
    """Main entry point for NLP processing."""
    intent = classify_intent(text)
    entities = extract_entities(text)
    
    return {
        "intent": intent,
        "entities": entities,
        "original": text
    }
