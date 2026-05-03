# main.py — NOVA AI Entry Point
# Neural Orchestrated Voice Assistant with Autonomous Intelligence
# Python 3.11 | Windows 10/11 | All free tools
#
# Thread architecture:
#   main thread         — Primary pipeline + HUD (Tkinter mainloop)
#   wake_word_thread    — Daemon: "Hey NOVA" detection (threading.Event)
#   gesture_thread      — Daemon: Camera + MediaPipe (queue.Queue)
#   reminder_thread     — Daemon: Reminder checker every 30s (queue.Queue)

import os
import threading
import queue
from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()


def main() -> None:
    """Entry point — initialises all threads and launches HUD."""
    print("NOVA AI — Initializing...")

    # TODO: Week 1 Day 1 — scaffold only. Real implementation added daily.

    # ── Shared state ─────────────────────────────────────────────────
    # wake_event: set() by wake_word_thread → main pipeline waits on it
    wake_event = threading.Event()

    # gesture_queue: gesture_thread puts OS actions here → main pops them
    gesture_queue: queue.Queue = queue.Queue()

    # reminder_queue: reminder_thread puts alert strings → main speaks them
    reminder_queue: queue.Queue = queue.Queue()

    # ── Thread stubs (replaced as each module is implemented) ─────────
    # TODO Day 2: from modules.wake_word import WakeWordDetector
    # TODO Day 2: from modules.stt import SpeechToText
    # TODO Day 3: from modules.nlp_engine import process as nlp_process
    # TODO Day 4: from modules.groq_brain import GroqBrain
    # TODO Day 5: from modules.memory_system import DatabaseManager
    # TODO Day 6: from modules.hud_interface import NOVAHud
    # TODO Day 15: from modules.notes_reminders import ReminderEngine
    # TODO Day 18: from modules.gesture_engine import GestureEngine

    # ── Core start sequence ───────────────────────────────────────────
    # TODO: Start daemon threads here (wake_word, gesture, reminder)
    # TODO: Launch HUD in main thread (Tkinter must own the mainloop)
    # TODO: Enter main voice pipeline loop

    print("NOVA AI — Ready (scaffold mode — no modules active yet)")
    print("Run 'python main.py' after each Day to verify the pipeline builds.")


if __name__ == "__main__":
    main()
