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

    import json
    
    # Load config
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}")
        return

    # ── Shared state ─────────────────────────────────────────────────
    # wake_event: set() by wake_word_thread → main pipeline waits on it
    wake_event = threading.Event()

    # gesture_queue: gesture_thread puts OS actions here → main pops them
    gesture_queue: queue.Queue = queue.Queue()

    # reminder_queue: reminder_thread puts alert strings → main speaks them
    reminder_queue: queue.Queue = queue.Queue()

    # ── Module Imports ────────────────────────────────────────────────
    from modules.wake_word import WakeWordDetector
    from modules.stt import SpeechToText
    from modules.nlp_engine import process as nlp_process
    # TODO Day 4: from modules.groq_brain import GroqBrain
    # TODO Day 5: from modules.memory_system import DatabaseManager
    # TODO Day 6: from modules.hud_interface import NOVAHud
    # TODO Day 15: from modules.notes_reminders import ReminderEngine
    # TODO Day 18: from modules.gesture_engine import GestureEngine

    # ── Initialize Modules ────────────────────────────────────────────
    wake_word = WakeWordDetector(wake_event, config)
    stt = SpeechToText(config)

    import pyttsx3
    import tempfile
    from gtts import gTTS
    import os

    # Initialize pyttsx3 TTS
    tts_engine = pyttsx3.init()
    tts_cfg = config.get("tts", {})
    tts_engine.setProperty('rate', tts_cfg.get("rate", 175))
    tts_engine.setProperty('volume', tts_cfg.get("volume", 0.9))

    def speak(text: str):
        """Speaks the text aloud using pyttsx3."""
        print(f"[NOVA] {text}")
        tts_engine.say(text)
        tts_engine.runAndWait()

    def speak_online(text: str):
        """Fallback TTS using gTTS."""
        print(f"[NOVA (gTTS)] {text}")
        try:
            tts = gTTS(text=text, lang='en')
            temp_path = os.path.join(tempfile.gettempdir(), "nova_tts.mp3")
            tts.save(temp_path)
            # Use built-in OS command to play audio on Windows
            if os.name == 'nt':
                os.system(f"start {temp_path}")
        except Exception as e:
            print(f"[TTS Error] {e}")

    # ── Core start sequence ───────────────────────────────────────────
    # Start background threads
    wake_word.start()
    
    # TODO: Launch HUD in main thread (Tkinter must own the mainloop)

    print("\nNOVA AI — Ready (Listening for wake word...)")
    
    # Main voice pipeline loop
    try:
        while True:
            # Block until WakeWordDetector sets the event
            wake_event.wait()
            
            # Listen for user command
            audio = stt.listen()
            
            if audio:
                # Convert to text
                text = stt.transcribe(audio)
                if text:
                    print(f"\n[USER] {text}")
                    
                    # NLP Processing
                    result = nlp_process(text)
                    intent = result["intent"]
                    entities = result["entities"]
                    
                    print(f"[NLP] Intent: {intent} | Entities: {entities}")
                    speak(f"I understood your intent is {intent}.")
                    
            # Reset event to go back to passive listening
            wake_event.clear()
            print("\n[NOVA] Resuming background listening...")
            
    except KeyboardInterrupt:
        print("\nNOVA AI — Shutting down gracefully...")
        wake_word.stop()


if __name__ == "__main__":
    main()
