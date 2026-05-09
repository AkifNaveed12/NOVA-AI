# main.py — NOVA AI Entry Point
# Neural Orchestrated Voice Assistant with Autonomous Intelligence
# Python 3.11 | Windows 10/11 | All free tools
#
# Thread architecture:
#   main thread         — pywebview event loop (webview.start())
#   voice_pipeline_thread — Daemon: STT → NLP → route → TTS → HUD updates
#   wake_word_thread    — Daemon: "Hey NOVA" detection (threading.Event)
#   gesture_thread      — Daemon: Camera + MediaPipe (queue.Queue)
#   reminder_thread     — Daemon: Reminder checker every 30s (queue.Queue)

import os
import threading
import queue
import time
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
    from modules.memory_system import DatabaseManager
    from modules.hud_interface import NOVAHud

    # ── Initialize Modules ────────────────────────────────────────────
    db_manager = DatabaseManager()
    
    # Inject memory facts into GroqBrain (which is globally imported in nova_core)
    import nova_core
    facts = db_manager.get_facts(limit=10)
    nova_core.groq_brain.inject_memory(facts)

    # Initialize HUD (must be in main thread)
    hud = NOVAHud()

    # ── Global Microphone Stream ──────────────────────────────────────
    # To achieve 0.0s latency between wake word and command listening,
    # we open the microphone exactly ONCE at startup and keep it open.
    import speech_recognition as sr
    shared_mic = sr.Microphone()
    shared_mic.__enter__() # Open the PyAudio stream permanently

    wake_word = WakeWordDetector(wake_event, config, shared_mic=shared_mic)
    stt = SpeechToText(config, shared_mic=shared_mic)

    import pyttsx3
    import tempfile
    from gtts import gTTS
    import os

    # Initialize pyttsx3 TTS using thread-local storage 
    # to prevent SAPI5 COM hangs when called from background threads
    tts_local = threading.local()
    tts_cfg = config.get("tts", {})

    def get_tts_engine():
        if not hasattr(tts_local, "engine"):
            engine = pyttsx3.init()
            engine.setProperty('rate', tts_cfg.get("rate", 175))
            engine.setProperty('volume', tts_cfg.get("volume", 0.9))
            tts_local.engine = engine
        return tts_local.engine

    def speak(text: str):
        """Speaks the text aloud using pyttsx3. Pauses wake word during speech."""
        hud.update_status("speaking")
        hud.log_message("nova", text)
        print(f"[NOVA] {text}")
        engine = get_tts_engine()
        engine.say(text)
        engine.runAndWait()
        # Note: wake_word.resume() is called by voice_pipeline AFTER draining
        hud.update_status("sleeping")

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

    # Define STT wrapper globally for multi-turn flows (email, etc.)
    def _listen_once() -> str:
        hud.update_status("listening")
        _audio = stt.listen()
        hud.update_status("processing")
        if _audio:
            _text = stt.transcribe(_audio)
            if _text:
                print(f"[USER follow-up] {_text}")
                hud.log_message("user", _text)
                return _text
        return ""

    # Email polling background thread
    from modules.email_module import EmailModule
    em = EmailModule(config)
    
    announcement_queue = queue.Queue()
    
    def email_poller():
        while True:
            time.sleep(60)
            # Only check if NOVA is sleeping
            if not wake_event.is_set():
                new_emails = em.check_inbox()
                if new_emails:
                    print(f"[EmailPoller] Found {len(new_emails)} new emails.")
                    announcement_queue.put(f"You have {len(new_emails)} new emails. Just say, check my emails, if you want me to read them.")

    threading.Thread(target=email_poller, daemon=True, name="EmailPollerThread").start()

    # Define the voice pipeline thread
    def voice_pipeline():
        """Background thread: wakes on event, listens, routes, speaks, loops."""
        print("\nNOVA AI — Ready (Listening for wake word...)")
        try:
            while True:
                # Check for pending background announcements
                while not announcement_queue.empty():
                    ann = announcement_queue.get()
                    wake_word.pause()
                    speak(ann)
                    wake_word.resume()
                
                hud.update_status("sleeping")

                # Block until wake word detector fires
                triggered = wake_event.wait(timeout=1.0)
                if not triggered:
                    continue
                    
                # At this point, wake_word is already paused (called self.pause()
                # before setting the event), so STT has exclusive mic access.

                hud.update_status("listening")
                audio = stt.listen()

                if audio:
                    hud.update_status("processing")
                    text = stt.transcribe(audio)

                    if text:
                        print(f"\n[USER] {text}")
                        hud.log_message("user", text)

                        result = nlp_process(text)
                        intent = result["intent"]
                        entities = result["entities"]
                        print(f"[NLP] Intent: {intent} | Entities: {entities}")

                        import nova_core

                        response = nova_core.route(
                            result,
                            speak_func  = speak,
                            listen_func = _listen_once,
                        )

                        activity_id = db_manager.log_activity(
                            command=text,
                            module=intent,
                            response=response,
                            success=True
                        )

                        if intent == "conversation" or intent in nova_core.GROQ_INTENTS:
                            db_manager.log_conversation("user", text, activity_id=activity_id)
                            db_manager.log_conversation("assistant", response, activity_id=activity_id)

                        speak(response)

                # --- Pipeline reset ---
                # Reset the wake event first so the detector loop doesn't re-arm too soon
                wake_event.clear()
                print("\n[NOVA] Resuming background listening...")
                # wake_word.resume() internally sleeps 1.2s to let the PyAudio buffer
                # drain before arming the detector again. This prevents TTS audio or
                # stale mic buffer from triggering a false wake detection.
                wake_word.resume()
                hud.update_status("sleeping")

        except Exception as e:
            import traceback
            print(f"\nNOVA AI — Pipeline Error: {e}")
            traceback.print_exc()
            wake_word.stop()

    # ── Core start sequence ───────────────────────────────────────────
    # Start background threads
    wake_word.start()
    
    pipeline_thread = threading.Thread(target=voice_pipeline, daemon=True)
    pipeline_thread.start()

    # Launch HUD in main thread (pywebview.start() MUST run on main thread)
    # This call blocks until the HUD window is closed by the user
    hud.start()
    
    print("\nNOVA AI — Shutting down gracefully...")
    try:
        wake_word.stop()
        if getattr(shared_mic, 'stream', None) is not None:
            shared_mic.__exit__(None, None, None) # Close the PyAudio stream
    except OSError:
        pass


if __name__ == "__main__":
    main()
