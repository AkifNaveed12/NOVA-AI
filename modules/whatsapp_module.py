"""
MODULE 11 — WhatsApp Automation
================================
Uses pywhatkit to send WhatsApp messages securely via Chrome.
"""

import os
import re
import json
import webbrowser
from rapidfuzz import process, fuzz
from typing import Callable, Optional


class WhatsAppModule:
    def __init__(self, config: dict = None):
        self._config = config or {}
        
        from modules.config_manager import config_manager
        self.contacts = config_manager.contacts.get("contacts", [])

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

    def _open_url(self, url: str):
        """Helper to open URLs reliably on Windows using native os.startfile, with fallback to webbrowser."""
        try:
            import platform
            if platform.system() == "Windows":
                os.startfile(url)
            else:
                webbrowser.open(url)
        except Exception as e:
            print(f"[WhatsApp] Error opening URL {url}: {e}")
            webbrowser.open(url)

    def send_message(self, phone: str, message: str) -> str:
        """
        Sends a WhatsApp message via browser automation.
        Returns a status string: 'sent', 'timeout', or 'error:<reason>'.
        """
        try:
            import urllib.parse
            import time
            try:
                import pyautogui
            except ImportError:
                return "error:pyautogui not installed"

            encoded_msg = urllib.parse.quote(message)
            url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}"

            print(f"[WhatsApp] Opening browser to send to {phone}...")
            self._open_url(url)

            # Poll for the WhatsApp Web tab to be active (up to 30s)
            deadline = time.time() + 30
            loaded = False
            try:
                import pygetwindow as gw
                while time.time() < deadline:
                    time.sleep(1)
                    titles = [w.title for w in gw.getAllWindows()]
                    if any("WhatsApp" in t for t in titles):
                        loaded = True
                        break
            except ImportError:
                # pygetwindow not available — fall back to fixed wait
                time.sleep(20)
                loaded = True

            if not loaded:
                print("[WhatsApp] Timed out waiting for WhatsApp Web to load.")
                return "timeout"

            # Extra buffer to ensure the chat input field is ready
            time.sleep(2)
            print("[WhatsApp] Pressing enter to send...")
            pyautogui.press("enter")
            time.sleep(3)

            print("[WhatsApp] Closing WhatsApp Web tab...")
            pyautogui.hotkey("ctrl", "w")
            return "sent"

        except Exception as e:
            print(f"[WhatsApp] Failed to send message: {e}")
            return f"error:{e}"

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
            status = self.send_message(phone, message_content)
            if status == "sent":
                return f"Message sent to {target_name}."
            elif status == "timeout":
                return "WhatsApp Web took too long to load. Please make sure you're logged in and try again."
            else:
                return f"Failed to send the message. {status.replace('error:', '')}".strip()
        else:
            return "WhatsApp message cancelled."
