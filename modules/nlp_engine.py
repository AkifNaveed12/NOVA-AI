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
# "today" in "what's the weather today" must match weather, NOT datetime.
INTENT_PATTERNS = {
    # ── High-priority: specific multi-word phrases first ──────────
    "weather": ["weather", "temperature", "forecast", "rain", "sunny", "humid", "climate"],
    "news": ["news", "headlines", "nasa", "space news", "science news", "what's happening"],
    "wikipedia": ["tell me about", "what is a", "what is an", "what is the", "what is", "who is", "who was", "explain", "describe"],
    "translate": ["translate", "in french", "in arabic", "in urdu", "in hindi", "in spanish",
                   "in german", "in chinese", "in japanese", "in korean", "in turkish",
                   "in russian", "in italian", "in portuguese", "to french", "to arabic",
                   "to urdu", "to hindi", "to spanish", "to german", "what does", "mean in"],
    "screenshot": ["screenshot", "capture screen", "take screenshot"],
    "clipboard": ["clipboard", "what did i copy"],
    "memory": ["remember that", "forget that", "what do you know"],
    # ── Medium-priority: single-word triggers ─────────────────────
    "music": ["play", "music", "song", "pause", "resume", "next"],
    "system": ["shutdown", "restart", "sleep", "lock", "volume", "brightness", "battery", "cpu", "ram"],
    "app": ["launch", "start", "run", "open"],
    "web": ["go to", "visit", "browse"],
    "check_email": ["check email", "read my email", "any updates on gmail", "new mails", "recent emails", "check inbox", "any new mail"],
    "email": ["email", "mail", "send email", "write email"],
    "whatsapp": ["whatsapp", "send message"],
    "task_queue": ["note down the tasks", "create a task list", "multiple tasks", "note down tasks", "note down"],
    "notes": ["note", "take a note", "write down"],
    "reminder": ["remind", "reminder", "alert me", "set alarm"],
    "calendar": ["calendar", "event", "schedule", "meeting"],
    "task": ["task", "to-do", "todo", "add task", "mark done"],
    # ── Low-priority: very generic words like "today", "time" ─────
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
