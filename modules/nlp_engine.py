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

# TODO: implement classify_intent(), extract_entities(), process()
