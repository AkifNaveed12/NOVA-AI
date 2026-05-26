"""
MODULE 26 — Coding Assistant
==============================
A Groq-powered code assistant with its own conversation history and a
code-focused system prompt. Separate from GroqBrain so code context
is never mixed with voice conversation history.

Used exclusively through the app's Dev tab — never routed to TTS
because code is unreadable when spoken.

Model: llama-3.3-70b-versatile (same as GroqBrain — confirmed active)
History window: 20 messages (10 turns) — larger than voice because
                code context is critical for follow-up questions.
"""

import os
import time
from typing import Optional
from groq import Groq


_SYSTEM_PROMPT = """You are a senior software engineer assistant embedded in NOVA AI.
Your job is to help the user write, debug, review, and understand code.

Rules:
- Always use Markdown. Wrap all code in fenced code blocks with the correct language tag.
- Be concise. Explain the WHY, not the WHAT. Well-named code explains itself.
- When debugging: state the root cause first, then the fix.
- When writing code: write clean, minimal, production-quality code. No unnecessary comments.
- When reviewing: list concrete issues with file:line references where possible.
- Supported languages: Python, JavaScript, TypeScript, Dart, C++, SQL, Bash, HTML/CSS.
- If you are unsure, say so. Do not hallucinate APIs or library functions."""


class CodingAssistant:
    HISTORY_WINDOW = 20
    MODEL = "llama-3.3-70b-versatile"
    MAX_TOKENS = 2048

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set. Complete the setup first.")
        self.client = Groq(api_key=api_key)
        self.history: list = []

    def chat(self, user_message: str) -> str:
        # Trim before appending — same fix as GroqBrain to avoid assistant-first history
        if len(self.history) >= self.HISTORY_WINDOW:
            self.history = self.history[-(self.HISTORY_WINDOW - 1):]

        self.history.append({"role": "user", "content": user_message})
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + self.history

        for attempt in range(3):
            try:
                completion = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=self.MAX_TOKENS,
                )
                response = completion.choices[0].message.content.strip()
                self.history.append({"role": "assistant", "content": response})
                return response

            except Exception as e:
                err = str(e).lower()
                if "rate_limit" in err or "429" in err:
                    wait = 2 ** attempt
                    print(f"[CodingAssistant] Rate limit. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"[CodingAssistant] Error: {e}")
                    self.history.pop()
                    return f"Error: {e}"

        self.history.pop()
        return "Rate limit reached. Please wait a few seconds and try again."

    def reset(self):
        self.history = []
        return "Conversation cleared."


# ── Lazy singleton — created only after setup is complete ─────────
_assistant: Optional[CodingAssistant] = None

def get_coding_assistant() -> CodingAssistant:
    """Returns the singleton, creating it on first call. Raises if GROQ_API_KEY not set."""
    global _assistant
    if _assistant is None:
        _assistant = CodingAssistant()
    return _assistant

def reset_coding_assistant():
    """Force re-creation on next call (e.g., after a new Groq key is saved via setup)."""
    global _assistant
    _assistant = None
