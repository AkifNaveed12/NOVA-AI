"""
MODULE 17 — Screenshot & Screen Automation
============================================
Takes screenshots on voice command and saves to Desktop with
timestamp. Also supports cursor-based screen interaction.

Tech: pyautogui, Pillow (PIL), os
Output: Screenshot filename confirmation → TTS engine
Storage: Desktop folder (screenshot PNG files)
"""

import os
import datetime


class ScreenshotTools:
    """Handles screenshot capture and basic screen automation."""

    def get_desktop_path(self) -> str:
        """Returns the path to the user's Desktop folder."""
        return os.path.join(os.path.expanduser("~"), "Desktop")

    def take_screenshot(self) -> str:
        """
        Takes a full-screen screenshot and saves it to the Desktop
        with a timestamp filename. Returns a confirmation string for TTS.
        """
        try:
            import pyautogui
            from PIL import Image

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"NOVA_Screenshot_{timestamp}.png"
            desktop = self.get_desktop_path()
            filepath = os.path.join(desktop, filename)

            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            print(f"[Screenshot] Saved: {filepath}")
            return f"Screenshot saved to your Desktop as {filename}."

        except ImportError:
            return "pyautogui or Pillow is not installed. Please run: pip install pyautogui Pillow"
        except Exception as e:
            print(f"[Screenshot] Error: {e}")
            return "I couldn't take a screenshot. Please check if pyautogui is installed correctly."

    def click_position(self, x: int, y: int) -> str:
        """Clicks at the given screen coordinates."""
        try:
            import pyautogui
            pyautogui.click(x, y)
            return f"Clicked at position {x}, {y}."
        except Exception as e:
            return f"Couldn't click at position: {e}"

    def type_text(self, text: str) -> str:
        """Types the given text at the current cursor position."""
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=0.05)
            return f"Typed: {text[:50]}."
        except Exception as e:
            return f"Couldn't type text: {e}"
