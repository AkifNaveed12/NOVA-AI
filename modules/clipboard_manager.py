"""
MODULE 18 — Clipboard Manager
================================
Voice control over the Windows clipboard. Read current clipboard
content via TTS or write new text to clipboard by voice command.
Uses pyperclip which works cross-platform but optimized for Windows.

Tech: pyperclip
Output: Clipboard content read aloud or copy confirmation → TTS engine
"""

import pyperclip

class ClipboardManager:
    def __init__(self, config: dict = None):
        pass

    def read(self) -> str:
        """
        Reads text from the clipboard.
        Truncates the output to 200 characters for TTS friendliness.
        """
        try:
            content = pyperclip.paste()
            if not content or not content.strip():
                return "Your clipboard is currently empty."
            
            content = content.strip()
            if len(content) > 200:
                return f"Your clipboard contains: {content[:200]}... and more."
            return f"Your clipboard contains: {content}"
        except Exception as e:
            print(f"[ClipboardManager] Error reading clipboard: {e}")
            return "I encountered an error trying to read your clipboard."

    def write(self, text: str) -> str:
        """
        Writes text to the clipboard.
        """
        if not text or not text.strip():
            return "What would you like me to copy to the clipboard?"
            
        try:
            pyperclip.copy(text.strip())
            preview = text.strip()
            if len(preview) > 50:
                preview = preview[:50] + "..."
            return f"Copied to clipboard: {preview}"
        except Exception as e:
            print(f"[ClipboardManager] Error writing to clipboard: {e}")
            return "I encountered an error trying to copy to your clipboard."
