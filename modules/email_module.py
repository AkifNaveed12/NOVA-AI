"""
MODULE 10 — Email Compose & Send
===================================
Full voice-driven email workflow: describe → Groq drafts → review
via TTS → confirm → send via Gmail SMTP. Multi-turn dialog with
confirmation before sending. Gmail App Password in .env only.

Tech: smtplib + email (built-in), Groq API for drafting
Secrets: GMAIL_ADDRESS, GMAIL_APP_PASSWORD from .env
Output: Email sent confirmation or cancellation string → TTS engine
"""

# TODO: implement EmailModule class with draft_email(), send_email(),
#       handle_email_command() methods
