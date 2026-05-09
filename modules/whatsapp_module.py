"""
MODULE 11 — WhatsApp Automation
================================
Uses pywhatkit to send WhatsApp messages securely via Chrome.
"""

import os
import json
from rapidfuzz import process, fuzz
from typing import Callable, Optional

class WhatsAppModule:
    def __init__(self, config: dict = None):
        self._config = config or {}
        
        # Load contacts
        self.contacts = []
        contacts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "contacts.json")
        try:
            with open(contacts_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.contacts = data.get("contacts", [])
        except Exception as e:
            print(f"[WhatsApp] Error loading contacts: {e}")

    def _resolve_phone(self, name: str) -> Optional[str]:
        """Fuzzy match a name against contacts.json aliases/names to find a phone number."""
        if not name or not self.contacts:
            return None

        name_lower = name.lower()
        best_match = None
        best_score = 0
        best_phone = None

        for contact in self.contacts:
            candidates = [contact["name"].lower()] + [a.lower() for a in contact.get("aliases", [])]
            match = process.extractOne(name_lower, candidates, scorer=fuzz.WRatio)
            if match and match[1] > best_score:
                best_score = match[1]
                best_match = contact["name"]
                best_phone = contact.get("phone")

        if best_score > 70 and best_phone:
            print(f"[WhatsApp] Resolved '{name}' to {best_match} ({best_phone})")
            return best_phone
            
        return None

    def send_message(self, phone: str, message: str) -> bool:
        """Sends a WhatsApp message via pywhatkit."""
        try:
            import pywhatkit
            # wait_time=15 gives browser time to load, tab_close=True closes it after
            pywhatkit.sendwhatmsg_instantly(phone, message, wait_time=15, tab_close=True)
            return True
        except Exception as e:
            print(f"[WhatsApp] Failed to send message: {e}")
            return False

    def handle_whatsapp_command(
        self,
        original: str,
        entities: dict,
        speak_func: Callable,
        listen_func: Callable
    ) -> str:
        """Interactive flow for sending a WhatsApp message."""
        
        # Extract target name
        target_name = entities.get("name") or entities.get("org")
        if not target_name:
            import re
            match = re.search(r"to\s+([a-zA-Z\s]+?)(?:\s+saying|\s+that|\s+message|\s+say|\s*$)", original, re.IGNORECASE)
            if match:
                target_name = match.group(1).strip()
                
        # If still no target, ask the user
        if not target_name:
            speak_func("Who should I send the WhatsApp message to?")
            target_name = listen_func().strip()
            if not target_name:
                return "Message cancelled. No contact provided."
                
        phone = self._resolve_phone(target_name)
        if not phone:
            return f"I couldn't find {target_name} in your contacts."
            
        # Extract the message content
        message_content = None
        import re
        msg_match = re.search(r"(?:saying|that|message|say)\s+(.+)", original, re.IGNORECASE)
        if msg_match:
            message_content = msg_match.group(1).strip()
            
        if not message_content:
            speak_func(f"What should I say to {target_name}?")
            message_content = listen_func().strip()
            if not message_content:
                return "Message cancelled. No content provided."
                
        speak_func(f"I will send the following WhatsApp message to {target_name}: {message_content}. Should I send it?")
        confirmation = listen_func().lower()
        
        if "yes" in confirmation or "send" in confirmation or "sure" in confirmation or "yeah" in confirmation:
            speak_func(f"Opening WhatsApp to send your message. Please wait a moment.")
            success = self.send_message(phone, message_content)
            if success:
                return f"Message sent to {target_name}."
            else:
                return "Failed to send the message. Make sure WhatsApp Web is logged into your default browser."
        else:
            return "WhatsApp message cancelled."
