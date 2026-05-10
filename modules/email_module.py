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
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
from typing import Callable, Optional


class EmailModule:
    """Handles Groq-powered email drafting and Gmail SMTP sending."""

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT   = 587

    def __init__(self, config: dict = None):
        self._config   = config or {}
        self._address  = os.getenv("GMAIL_ADDRESS", "")
        self._password = os.getenv("GMAIL_APP_PASSWORD", "")
        self._imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")

    # ── Inbox Checking ────────────────────────────────────────────
    def check_inbox(self, unseen_only: bool = True, limit: int = 5) -> list:
        """
        Connects to IMAP, fetches emails, and returns a list of dicts.
        If unseen_only is True, fetches only UNSEEN emails.
        Otherwise, fetches the latest `limit` emails.
        """
        if not self.has_credentials():
            return []
            
        try:
            mail = imaplib.IMAP4_SSL(self._imap_server)
            mail.login(self._address, self._password)
            mail.select("inbox")
            
            if unseen_only:
                status, messages = mail.search(None, "UNSEEN")
                if status != "OK":
                    return []
                email_ids = messages[0].split()
            else:
                status, messages = mail.search(None, "ALL")
                if status != "OK":
                    return []
                email_ids = messages[0].split()[-limit:] # Get the last N emails
                
            new_emails = []
            
            for e_id in email_ids:
                # Fetch full message without marking as read
                status, msg_data = mail.fetch(e_id, "(BODY.PEEK[])")
                if status != "OK":
                    continue
                    
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Decode Subject
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                            
                        # Decode Sender
                        sender = msg.get("From")
                        sender_name = sender.split("<")[0].strip().replace('"', '') if "<" in sender else sender
                        sender_email = sender.split("<")[1].split(">")[0] if "<" in sender else sender
                        
                        # Extract body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode(errors="ignore")
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode(errors="ignore")
                            
                        new_emails.append({
                            "sender_name": sender_name,
                            "sender_email": sender_email,
                            "subject": subject,
                            "body": body
                        })
                        
            mail.close()
            mail.logout()
            return new_emails
            
        except Exception as e:
            print(f"[EmailModule] Error checking inbox: {e}")
            return []

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
            # Also check 'org' in case spaCy misclassified it
            recipient_name = entities.get("org", "")
        
        if not recipient_name:
            speak_func("Who should I send the email to?")
            recipient_name = listen_func().strip()
            if not recipient_name:
                return "Email cancelled. No recipient provided."
            # Clean up spoken replies like "send it to Hamza" or "to Hamza"
            clean_match = re.search(r"(?:send(?:ing)?\s+(?:the\s+)?email\s+)?(?:to|for)\s+([a-z\s]+)$", recipient_name, re.IGNORECASE)
            if clean_match:
                recipient_name = clean_match.group(1).strip()

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
                spoken_address = listen_func().strip()
                if not spoken_address:
                    return "Email cancelled. No email address provided."
                
                # Parse the spoken address (e.g. "john at gmail dot com")
                to_address = self._parse_spoken_email(spoken_address)

            return self.send_email(to_address, subject, body)
        else:
            return "Email cancelled. The draft has not been sent."

    def handle_check_email_command(self, speak_func: Callable, listen_func: Callable) -> str:
        """
        Triggered when user asks "check my emails" or "any new mail".
        """
        speak_func("Checking your inbox. One moment...")
        emails = self.check_inbox(unseen_only=True)
        
        is_unseen = True
        if not emails:
            # Fallback to recent emails if no new ones
            emails = self.check_inbox(unseen_only=False, limit=3)
            is_unseen = False
            
        if not emails:
            return "Your inbox is completely empty right now."
            
        if is_unseen:
            speak_func(f"You have {len(emails)} new emails. Here is the summary:")
        else:
            speak_func(f"You have no new emails, but here are your {len(emails)} most recent ones:")
        
        # Give a quick summary of senders and subjects
        for i, email_obj in enumerate(emails):
            speak_func(f"Email {i+1}: from {email_obj['sender_name']}, about {email_obj['subject']}.")
            
        speak_func("Do you want me to read or reply to any of these? If yes, tell me the number or the sender's name.")
        response = listen_func().lower()
        
        if not response or "no" in response or "none" in response or "skip" in response:
            return "Okay, I'll leave them for now."
            
        # Try to match the response to an email
        selected_email = None
        for i, email_obj in enumerate(emails):
            if str(i+1) in response or email_obj['sender_name'].lower() in response:
                selected_email = email_obj
                break
                
        if not selected_email:
            return "I couldn't figure out which email you meant. Try asking me again later."
            
        from modules.groq_brain import GroqBrain
        brain = GroqBrain(self._config)
        
        speak_func("Summarizing the email...")
        prompt = f"Summarize this email in 2 short sentences for voice dictation:\nSender: {selected_email['sender_name']}\nSubject: {selected_email['subject']}\nBody:\n{selected_email['body']}"
        summary = brain.chat(prompt)
        
        speak_func(f"Here is the summary: {summary}. What should I say in the reply?")
        reply_context = listen_func()
        
        if reply_context and "nothing" not in reply_context.lower() and "cancel" not in reply_context.lower():
            speak_func("Drafting your reply...")
            draft_prompt = f"Draft an email reply to {selected_email['sender_name']}.\nContext of original email:\n{selected_email['body']}\nUser's reply instructions:\n{reply_context}\nWrite only the professional email body, no subject line."
            draft_body = brain.chat(draft_prompt)
            
            speak_func(f"Here is the draft: {draft_body}. Should I send it?")
            send_resp = listen_func().lower()
            if "yes" in send_resp or "send" in send_resp:
                self.send_email(selected_email["sender_email"], f"Re: {selected_email['subject']}", draft_body)
                return "Reply sent."
            else:
                return "Reply cancelled."
        else:
            return "Okay, skipping the reply."

    # ── Helpers ───────────────────────────────────────────────────
    def _resolve_address(self, name: str, entities: dict) -> str:
        """
        Try to find an email address for the given name.
        Checks contacts.json for an email field, otherwise returns empty string.
        """
        if not name:
            return ""
        name_lower = name.lower()
        try:
            import json
            contacts_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config", "contacts.json"
            )
            with open(contacts_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for contact in data.get("contacts", []):
                contact_name = contact.get("name", "").lower()
                aliases = [a.lower() for a in contact.get("aliases", [])]
                
                # Match if the spoken name contains the contact name/alias, or vice versa
                if contact_name in name_lower or name_lower in contact_name:
                    email = contact.get("email", "")
                    if email: return email
                
                for alias in aliases:
                    if alias in name_lower or name_lower in alias:
                        email = contact.get("email", "")
                        if email: return email
                        
        except Exception as e:
            print(f"[EmailModule] Error resolving address: {e}")
        return ""

    def _parse_spoken_email(self, spoken: str) -> str:
        """Converts spoken text like 'john 123 at gmail dot com no spaces' to a real email."""
        # Strip common trailing conversational additions
        email = spoken.lower()
        if " without spaces" in email:
            email = email.split(" without spaces")[0]
        if " it is " in email:
            email = email.split(" it is ")[0]
            
        email = email.replace("at the rate", "@").replace(" at ", "@")
        email = email.replace(" dot ", ".")
        # Remove spaces
        email = email.replace(" ", "")
        return email

    def has_credentials(self) -> bool:
        """Returns True if Gmail credentials are configured in .env."""
        return bool(self._address and self._password)
