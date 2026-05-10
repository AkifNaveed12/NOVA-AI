"""
MODULE 11 — WhatsApp Automation
================================
Uses pywhatkit to send WhatsApp messages securely via Chrome.
"""

import os
import re
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

        name_lower = name.lower().strip()
        best_score = 0
        best_match = None
        best_phone = None

        for contact in self.contacts:
            candidates = [contact["name"].lower()] + [a.lower() for a in contact.get("aliases", [])]
            match = process.extractOne(name_lower, candidates, scorer=fuzz.WRatio)
            if match and match[1] > best_score:
                best_score = match[1]
                best_match = contact["name"]
                best_phone = contact.get("phone")

        if best_score > 60 and best_phone:
            print(f"[WhatsApp] Resolved '{name}' → {best_match} ({best_phone})")
            return best_phone
            
        return None

    def send_message(self, phone: str, message: str) -> bool:
        """Sends a WhatsApp message via pywhatkit (instantly, no scheduled time)."""
        try:
            import pywhatkit
            print(f"[WhatsApp] Sending to {phone}: {message}")
            # wait_time=15 gives WhatsApp Web time to load
            # tab_close=True closes the browser tab after sending
            pywhatkit.sendwhatmsg_instantly(phone, message, wait_time=15, tab_close=True, close_time=5)
            return True
        except Exception as e:
            print(f"[WhatsApp] Failed to send message: {e}")
            return False

    def _extract_contact_from_text(self, original: str) -> Optional[str]:
        """
        Extracts the contact name from various command patterns:
        - "text mama [message]"
        - "whatsapp mama saying hello"
        - "send message to mama"
        - "send a whatsapp to mama"
        """
        text = original.lower()

        # Pattern: "text <name>" — catches "text mama", "text hamza hello"
        m = re.search(r'\btext\s+([a-zA-Z]+)', text)
        if m:
            return m.group(1).strip()

        # Pattern: "to <name>" — catches "send message to mama", "whatsapp to mama"
        m = re.search(r'\bto\s+([a-zA-Z]+)(?:\s+saying|\s+that|\s+the message|\s+my message|\s*$)', text)
        if m:
            return m.group(1).strip()

        # Pattern: "whatsapp <name>" — catches "whatsapp mama"
        m = re.search(r'\bwhatsapp\s+([a-zA-Z]+)', text)
        if m:
            candidate = m.group(1).strip()
            # Ignore stop words
            if candidate not in ("web", "message", "send", "open", "the"):
                return candidate

        return None

    def _extract_message_from_text(self, original: str) -> Optional[str]:
        """
        Extracts message content from patterns like:
        - "saying <message>"
        - "that <message>"
        - "message <message>"
        """
        m = re.search(r'\b(?:saying|that|message|say)\s+(.+)', original, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return None

    def handle_whatsapp_command(
        self,
        original: str,
        entities: dict,
        speak_func: Callable,
        listen_func: Callable
    ) -> str:
        """Interactive flow for sending a WhatsApp message."""

        # ── Step 1: Resolve contact ────────────────────────────────────
        # Try extracting from command text first
        target_name = self._extract_contact_from_text(original)

        # Fallback to spaCy entities
        if not target_name:
            target_name = entities.get("name") or entities.get("org")

        # Ask the user if still not found
        if not target_name:
            speak_func("Who should I send the WhatsApp message to?")
            target_name = listen_func()
            if not target_name:
                return "Message cancelled. No contact provided."
            target_name = target_name.strip()

        phone = self._resolve_phone(target_name)
        if not phone:
            return f"I couldn't find '{target_name}' in your contacts. Please add them to contacts.json."

        # ── Step 2: Resolve message content ───────────────────────────
        message_content = self._extract_message_from_text(original)

        if not message_content:
            speak_func(f"What should I say to {target_name}?")
            message_content = listen_func()
            if not message_content:
                return "Message cancelled. No content provided."
            message_content = message_content.strip()

        # ── Step 3: Confirm and send ───────────────────────────────────
        speak_func(f"I'll send this to {target_name}: {message_content}. Should I send it?")
        confirmation = listen_func()
        if not confirmation:
            return "Message cancelled."
            
        confirmation = confirmation.lower()
        if any(word in confirmation for word in ("yes", "send", "sure", "yeah", "ok", "go ahead", "do it")):
            speak_func(f"Sending message to {target_name} on WhatsApp. Please wait.")
            success = self.send_message(phone, message_content)
            if success:
                return f"Message sent to {target_name} successfully!"
            else:
                return "Failed to send the message. Make sure WhatsApp Web is open and logged in to your browser."
        else:
            return "WhatsApp message cancelled."
