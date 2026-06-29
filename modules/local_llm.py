"""
MODULE — Local LLM (Ollama Fallback)
=====================================
Provides an offline LLM response when Groq is unavailable (rate limit,
no internet, or API error).

Uses Ollama running locally with the llama3.2 model.

Architecture:
- local_llm.chat() mirrors the groq_brain.chat() signature
- is_available() checks Ollama health at http://localhost:11434
- Used by groq_brain.py as a transparent fallback

Setup:
  ollama is already installed and running (confirmed in preflight).
  Model: ollama pull llama3.2 (2GB — already downloaded per sprint notes)

Tech: requests (built-in to project), Ollama REST API
Output: response text string → TTS engine
"""

import requests


class LocalLLM:
    """Ollama-backed local LLM. Used as fallback when Groq is unavailable.

    Sprint 0 / Module 5 implementation per FINAL-PLAN.md Phase 5.
    """

    BASE_URL = "http://localhost:11434"
    MODEL = "llama3.2"

    def is_available(self) -> bool:
        """Returns True if Ollama server is running and the model is ready."""
        try:
            r = requests.get(f"{self.BASE_URL}/api/tags", timeout=2)
            if r.status_code != 200:
                return False
            # Verify the model is actually pulled
            data = r.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            return any(self.MODEL in m for m in models)
        except Exception:
            return False

    def chat(self, prompt: str, system_prompt: str = "") -> str:
        """Send a prompt to the local Ollama model and return the response.

        Args:
            prompt: The user message.
            system_prompt: Optional system/personality context.

        Returns:
            Response text string. Returns an error message on failure.
        """
        full_prompt = (
            f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
            if system_prompt
            else f"User: {prompt}\nAssistant:"
        )

        payload = {
            "model": self.MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "num_predict": 200,   # ~200 tokens max — keeps responses concise for TTS
                "temperature": 0.7,
            },
        }

        try:
            resp = requests.post(
                f"{self.BASE_URL}/api/generate",
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except requests.exceptions.Timeout:
            return "Local model is taking too long to respond."
        except Exception as e:
            return f"[Local LLM error: {e}]"


# Singleton — imported by groq_brain.py for transparent fallback
local_llm = LocalLLM()
