"""
MODULE 4 — Groq LLM Brain
===========================
Second brain layer. Handles complex, conversational, and ambiguous
queries that the NLP layer cannot resolve with high confidence.
Uses Groq API with LLaMA 3 70B model (free tier, ~1s response).
Maintains rolling conversation history (last 10 messages).
Injects top-10 memory facts from SQLite into each system prompt.

Tech: groq Python SDK, LLaMA 3 70B (llama3-70b-8192)
API Key: GROQ_API_KEY from .env
Output: response text string → TTS engine
"""

# TODO: implement GroqBrain class with chat(), inject_memory(),
#       reset_conversation(), extract_facts() methods
