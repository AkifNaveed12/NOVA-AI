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

import os
import datetime
from groq import Groq

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
        
        user_name = self.config.get("nova", {}).get("user_name", "Akif")
        
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

    def inject_memory(self, facts: list):
        """Prepends long term memory facts into the system prompt."""
        if not facts:
            self.system_prompt = self.base_system_prompt
            return
            
        facts_text = " ".join([f"Fact: {f[0]} = {f[1]}" for f in facts])
        self.system_prompt = self.base_system_prompt + f"\n\nHere are some known facts about the user:\n{facts_text}"

    def chat(self, user_message: str) -> str:
        """Sends the message to Groq, keeping the last 10 messages of history."""
        try:
            # Append user message
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Keep only the last 10 messages (rolling window) to save tokens
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            # Build messages payload (System + History)
            messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=256,
            )
            
            response = completion.choices[0].message.content.strip()
            
            # Append assistant response to history
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
            
        except Exception as e:
            print(f"[GroqBrain] Error communicating with Groq: {e}")
            return "I'm having trouble connecting to my brain right now. Please check my API key."
            
    def reset_conversation(self):
        """Clears the short-term conversation history."""
        self.conversation_history = []
