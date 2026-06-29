"""
MODULE 4 — Groq LLM Brain
===========================
Second brain layer. Handles complex, conversational, and ambiguous
queries that the NLP layer cannot resolve with high confidence.
Uses Groq API with LLaMA 3 70B model (free tier, ~1s response).
Maintains rolling conversation history (last 10 messages).
Injects top-10 memory facts from SQLite into each system prompt.

Tech: groq Python SDK, LLaMA 3.3 70B (llama-3.3-70b-versatile)
API Key: GROQ_API_KEY from .env
Output: response text string → TTS engine
"""

import os
import datetime
from groq import Groq

# Sprint 0 / Module 5: Local LLM fallback (Ollama + llama3.2)
# Import is lazy-safe — local_llm.is_available() returns False if Ollama isn't running
try:
    from modules.local_llm import local_llm as _local_llm
    _LOCAL_LLM_AVAILABLE = True
except ImportError:
    _local_llm = None
    _LOCAL_LLM_AVAILABLE = False

# Module 1: Context Scanner — inject PC awareness into every Groq call
# Import is lazy-safe — if scanner not started yet, get_context_summary() returns ""
try:
    from modules.context_scanner import context_scanner as _ctx_scanner
    _CTX_SCANNER_AVAILABLE = True
except ImportError:
    _ctx_scanner = None
    _CTX_SCANNER_AVAILABLE = False

# Module 2: Semantic Memory — dynamic contextual user model
try:
    from modules.semantic_memory import semantic_memory as _semantic_memory
    _SEMANTIC_MEMORY_AVAILABLE = True
except ImportError:
    _semantic_memory = None
    _SEMANTIC_MEMORY_AVAILABLE = False

class GroqBrain:
    def __init__(self, config: dict):
        self.config = config
        # Use the supported model instead of the decommissioned llama3-70b-8192
        self.model = "llama-3.3-70b-versatile"
        
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key or "your_key" in api_key:
            print("[GroqBrain] WARNING: Invalid or missing GROQ_API_KEY in .env!")
        
        self.client = Groq(api_key=api_key)
        self.conversation_history = []
        
        user_name = self.config.get("user", {}).get("name", "Akif")

        # System prompt defines NOVA's personality
        self.base_system_prompt = (
            f"You are NOVA (Neural Orchestrated Voice Assistant with Autonomous Intelligence). "
            f"You are a professional, helpful, and friendly AI assistant. "
            f"You are speaking to your creator/user, {user_name}, who is a Software Engineering student "
            f"at a university in Wah Cantt, Pakistan. "
            f"Always provide concise, conversational answers because they are spoken aloud via Text-to-Speech. "
            f"Do not use markdown formatting like asterisks or bold text, just plain conversational English. "
            f"Current date and time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        )
        
        self.system_prompt = self.base_system_prompt
        self._cached_facts = []  # Populated by inject_memory()

    def inject_memory(self, facts: list):
        """Prepends long term memory facts into the system prompt."""
        self._cached_facts = facts  # Cache for per-call re-injection
        if not facts:
            self.system_prompt = self.base_system_prompt
            return
        facts_text = "\n".join([f"  - {f[0]}: {f[1]}" for f in facts])
        self.system_prompt = self.base_system_prompt + f"\n\nKnown facts about the user:\n{facts_text}"

    def chat(self, user_message: str) -> str:
        """Sends the message to Groq with exponential backoff for rate limits."""
        import time

        # Rebuild system prompt with a fresh timestamp each call
        fresh_prompt = (
            f"You are NOVA (Neural Orchestrated Voice Assistant with Autonomous Intelligence). "
            f"You are a professional, helpful, and friendly AI assistant. "
            f"You are speaking to your creator/user, {self.config.get('user', {}).get('name', 'Akif')}, "
            f"who is a Software Engineering student at a university in Wah Cantt, Pakistan. "
            f"Always provide concise, conversational answers because they are spoken aloud via Text-to-Speech. "
            f"Do not use markdown formatting like asterisks or bold text, just plain conversational English. "
            f"Current date and time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        )

        # Module 2: Semantic Memory dynamic search injection
        semantic_facts_text = ""
        if _SEMANTIC_MEMORY_AVAILABLE and _semantic_memory is not None:
            try:
                semantic_facts_text = _semantic_memory.inject_for_prompt(user_message)
            except Exception as sm_err:
                print(f"[GroqBrain] Semantic memory search error (non-fatal): {sm_err}")

        if semantic_facts_text:
            fresh_prompt += semantic_facts_text
        elif self._cached_facts:
            facts_text = "\n".join([f"  - {k}: {v}" for k, v in self._cached_facts])
            fresh_prompt += f"\n\nKnown facts about the user:\n{facts_text}"

        self.system_prompt = fresh_prompt


        # Module 1: Inject PC context into user message if available
        # This is NOVA's flagship differentiator — proactive PC awareness
        if _CTX_SCANNER_AVAILABLE and _ctx_scanner is not None:
            try:
                ctx_str = _ctx_scanner.get_context_summary()
                if ctx_str:
                    user_message = (
                        f"[Current PC context: {ctx_str}]\n\nUser says: {user_message}"
                    )
            except Exception as ctx_err:
                print(f"[GroqBrain] Context injection error (non-fatal): {ctx_err}")

        # Rolling window — trim BEFORE appending so the new user message is always last
        # and the first message in history is always a user turn (Groq requires this).
        if len(self.conversation_history) >= 10:
            self.conversation_history = self.conversation_history[-9:]

        self.conversation_history.append({"role": "user", "content": user_message})

        messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history

        # Exponential backoff: up to 3 attempts (handles rate limits and transient errors)
        for attempt in range(3):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=256,
                )
                response = completion.choices[0].message.content.strip()
                self.conversation_history.append({"role": "assistant", "content": response})
                return response

            except Exception as e:
                err_str = str(e).lower()
                if "rate_limit" in err_str or "429" in err_str:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    print(f"[GroqBrain] Rate limit hit. Retrying in {wait}s (attempt {attempt+1}/3)...")
                    time.sleep(wait)
                else:
                    print(f"[GroqBrain] Error: {e}")
                    # Remove the user message we just appended since we won't get a response
                    self.conversation_history.pop()
                    return "I'm having trouble connecting right now. Please try again in a moment."

        # All Groq retries exhausted — attempt local LLM fallback
        self.conversation_history.pop()
        if _LOCAL_LLM_AVAILABLE and _local_llm is not None and _local_llm.is_available():
            print("[GroqBrain] Falling back to local LLM (Ollama llama3.2)...")
            try:
                local_response = _local_llm.chat(
                    user_message,
                    system_prompt=self.base_system_prompt
                )
                if local_response and not local_response.startswith("[Local LLM"):
                    self.conversation_history.append(
                        {"role": "assistant", "content": local_response}
                    )
                    return local_response
            except Exception as local_err:
                print(f"[GroqBrain] Local LLM fallback also failed: {local_err}")

        return "I'm temporarily unavailable due to API rate limits. Please try again in a few seconds."
            
    def reset_conversation(self):
        """Clears the short-term conversation history."""
        self.conversation_history = []
