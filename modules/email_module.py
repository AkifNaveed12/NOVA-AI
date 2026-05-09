"""
MODULE 10 — Email Compose & Send
=================================
Voice-driven email workflow using Groq for drafting and Gmail SMTP
for sending. Fully self-contained — requires speak_func and
listen_func callbacks passed in from main.py so this module never
touches TTS/STT directly.

Flow:
    1. Extract recipient + topic from the original command
    2. Draft email via Groq (subject + body)
    3. Speak draft summary aloud (via speak_func callback)
    4. Ask for confirmation; listen for "yes" / "no"
    5. If yes: send via Gmail SMTP and confirm
    6. If no: cancel gracefully

No HUD calls inside this module — main.py owns all hud.log_message()
calls based on the string this module returns.

Env vars required (.env):
    GMAIL_ADDRESS       — sender Gmail address
    GMAIL_APP_PASSWORD  — 16-char app password (2FA → App Passwords)

Tech: smtplib + email.mime (stdlib), Groq API, os/re
"""

import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Callable, Optional


class EmailModule:
    """Handles Groq-powered email drafting and Gmail SMTP sending."""

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT   = 587

    def __init__(self, config: dict = None):
        self._config   = config or {}
        self._address  = os.getenv("GMAIL_ADDRESS", "")
        self._password = os.getenv("GMAIL_APP_PASSWORD", "")

    # ── Draft ─────────────────────────────────────────────────────
    def draft_email(
        self,
        recipient_name: str,
        topic: str,
        details: str = "",
    ) -> dict:
        """
        Use Groq to draft a professional email.

        Returns dict: {"subject": str, "body": str, "recipient": str}
        """
        from modules.groq_brain import GroqBrain
        brain = GroqBrain(self._config)

        prompt = (
            f"Draft a professional email to {recipient_name} about {topic}. "
            f"{'Details: ' + details + '. ' if details else ''}"
            "Start with 'Subject: [subject line]' on the first line, "
            "then a blank line, then the email body. "
            "Keep the email concise and professional."
        )

        draft = brain.chat(prompt)

        # Parse subject line
        subject = f"Re: {topic}"
        body    = draft

        subject_match = re.search(r"^Subject:\s*(.+)$", draft, re.MULTILINE | re.IGNORECASE)
        if subject_match:
            subject = subject_match.group(1).strip()
            # Remove Subject: line from body
            body = draft[subject_match.end():].strip()

        return {
            "subject":   subject,
            "body":      body,
            "recipient": recipient_name,
        }

    # ── Send ──────────────────────────────────────────────────────
    def send_email(self, to_address: str, subject: str, body: str) -> str:
        """
        Send email via Gmail SMTP with TLS.

        Returns: success or descriptive error string.
        """
        if not self._address or not self._password:
            return (
                "Email credentials not configured. "
                "Please add GMAIL_ADDRESS and GMAIL_APP_PASSWORD to your .env file."
            )

        msg = MIMEMultipart()
        msg["From"]    = self._address
        msg["To"]      = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.login(self._address, self._password)
                server.sendmail(self._address, to_address, msg.as_string())
            return f"Email sent successfully to {to_address}."

        except smtplib.SMTPAuthenticationError:
            return (
                "Email authentication failed. "
                "Check your GMAIL_APP_PASSWORD in the .env file."
            )
        except smtplib.SMTPConnectError:
            return "Could not connect to Gmail. Please check your internet connection."
        except smtplib.SMTPRecipientsRefused:
            return f"Invalid email address: {to_address}"
        except TimeoutError:
            return "Gmail connection timed out. Try again later."
        except Exception as e:
            print(f"[EmailModule] SMTP error: {e}")
            return "Failed to send email due to an unexpected error."

    # ── Full voice flow ───────────────────────────────────────────
    def handle_email_command(
        self,
        original: str,
        entities: dict,
        speak_func: Callable[[str], None],
        listen_func: Callable[[], str],
    ) -> str:
        """
        Interactive multi-turn email flow.

        speak_func  — calls TTS (from main.py)
        listen_func — captures one STT utterance (from main.py)

        Returns final response string (also spoken by main.py after this returns).
        """
        # ── Extract recipient and topic ───────────────────────────
        recipient_name = entities.get("name", "")
        topic          = ""

        # Try to extract "email to [NAME] about [TOPIC]"
        to_match = re.search(
            r"(?:email|mail|send\s+(?:an?\s+)?email|write\s+(?:an?\s+)?email)\s+to\s+([a-z\s]+?)(?:\s+about\s+(.+))?$",
            original, re.IGNORECASE
        )
        if to_match:
            if not recipient_name:
                recipient_name = to_match.group(1).strip()
            if to_match.group(2):
                topic = to_match.group(2).strip()

        # Ask for missing recipient
        if not recipient_name:
            speak_func("Who should I send the email to?")
            recipient_name = listen_func().strip()
            if not recipient_name:
                return "Email cancelled. No recipient provided."

        # Ask for missing topic
        if not topic:
            speak_func(f"What should the email to {recipient_name} be about?")
            topic = listen_func().strip()
            if not topic:
                return "Email cancelled. No topic provided."

        # ── Draft ────────────────────────────────────────────────
        speak_func(f"Drafting an email to {recipient_name} about {topic}. One moment...")
        try:
            draft = self.draft_email(recipient_name, topic)
        except Exception as e:
            print(f"[EmailModule] Draft error: {e}")
            return "Sorry, I couldn't draft the email. Please check your Groq API key."

        subject = draft["subject"]
        body    = draft["body"]

        # Speak a summary of the draft (first 60 words of body)
        body_preview = " ".join(body.split()[:60])
        speak_func(
            f"Here's the draft. Subject: {subject}. "
            f"Body preview: {body_preview}... "
            "Should I send it? Say yes or no."
        )

        # ── Confirmation ─────────────────────────────────────────
        confirmation = listen_func().lower().strip()

        if "yes" in confirmation or "send" in confirmation or "yeah" in confirmation:
            # Resolve recipient to an actual email address
            to_address = self._resolve_address(recipient_name, entities)
            if not to_address:
                speak_func(
                    f"I don't have an email address for {recipient_name}. "
                    "What's their email address?"
                )
                to_address = listen_func().strip()
                if not to_address:
                    return "Email cancelled. No email address provided."

            return self.send_email(to_address, subject, body)
        else:
            return "Email cancelled. The draft has not been sent."

    # ── Helpers ───────────────────────────────────────────────────
    def _resolve_address(self, name: str, entities: dict) -> str:
        """
        Try to find an email address for the given name.
        Checks contacts.json for an email field, otherwise returns empty string.
        """
        try:
            import json
            contacts_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config", "contacts.json"
            )
            with open(contacts_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for contact in data.get("contacts", []):
                if name.lower() in contact.get("name", "").lower():
                    email = contact.get("email", "")
                    if email:
                        return email
        except Exception:
            pass
        return ""

    def has_credentials(self) -> bool:
        """Returns True if Gmail credentials are configured in .env."""
        return bool(self._address and self._password)
