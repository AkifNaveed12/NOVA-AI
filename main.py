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

    tts_cfg = config.get("tts", {})

    def speak(text: str):
        """Speaks the text aloud using pyttsx3. Pauses wake word during speech."""
        hud.update_status("speaking")
        hud.log_message("nova", text)
        print(f"[NOVA] {text}")
        
        import subprocess, sys
        rate = tts_cfg.get("rate", 175)
        volume = tts_cfg.get("volume", 0.9)
        script = f"import pyttsx3, sys; e=pyttsx3.init(); e.setProperty('rate', {rate}); e.setProperty('volume', {volume}); e.say(sys.argv[1]); e.runAndWait()"
        
        # Run TTS in a completely isolated process to bypass Windows SAPI5 background thread deadlocks
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
        subprocess.run([sys.executable, "-c", script, text], creationflags=flags)
        
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
    hud_ticker_queue   = queue.Queue()

    def email_poller():
        """Polls inbox every 60s; only announces when unread count INCREASES."""
        last_announced_count = 0
        while True:
            time.sleep(60)
            if not wake_event.is_set():
                try:
                    new_emails = em.check_inbox(unseen_only=True)
                    count = len(new_emails)
                    if count > last_announced_count:
                        print(f"[EmailPoller] Found {count} new emails.")
                        announcement_queue.put(
                            f"You have {count} new email{'s' if count > 1 else ''}. "
                            "Just say, check my emails, if you want me to read them."
                        )
                        last_announced_count = count
                    elif count == 0:
                        last_announced_count = 0  # Reset so next batch is announced
                except Exception as e:
                    print(f"[EmailPoller] Error: {e}")

    threading.Thread(target=email_poller, daemon=True, name="EmailPollerThread").start()

    # ── ReminderEngine — Day 15 ───────────────────────────────────────
    from modules.notes_reminders import RemindersModule, ReminderEngine
    _reminders_module = RemindersModule()
    reminder_engine = ReminderEngine(_reminders_module, announcement_queue, hud_ticker_queue)
    reminder_engine.start()

    # Define the voice pipeline thread
    def voice_pipeline():
        """Background thread: wakes on event, listens, routes, speaks, loops."""
        import pythoncom
        pythoncom.CoInitialize()
        
        from modules.personality import PersonalityModule
        _personality_startup = PersonalityModule()
        
        # CRITICAL: Wait for PyWebView to finish COM initialization before using SAPI5
        while not getattr(hud, "_ready", False):
            import time
            time.sleep(0.1)

        # ── Load today's calendar events into HUD ticker ───────────────
        try:
            from modules.calendar_tasks import CalendarModule
            _cal = CalendarModule()
            ticker_text = _cal.get_today_ticker_text()
            if ticker_text:
                hud.update_ticker(ticker_text)
        except Exception:
            pass

        # Drain any pending ticker messages from reminder engine
        while not hud_ticker_queue.empty():
            hud.update_ticker(hud_ticker_queue.get())
            
        greeting = _personality_startup.get_greeting(
            user_name=config.get("user", {}).get("name", "Akif"),
            notes_count=0,
            reminders=_reminders_module.get_upcoming_reminders(),
            events=[]
        )
        wake_word.pause()
        speak(greeting)
        wake_word.resume()
        
        try:
            while True:
                # Check for pending background announcements
                while not announcement_queue.empty():
                    ann = announcement_queue.get()
                    wake_word.pause()
                    speak(ann)
                    wake_word.resume()

                # Drain HUD ticker updates from reminder engine
                while not hud_ticker_queue.empty():
                    hud.update_ticker(hud_ticker_queue.get())
                
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

                        # Guard: personality intro manages its own TTS — skip speak()
                        if response == "" and result.get("intent") == "introduce":
                            wake_event.clear()
                            wake_word.resume()
                            hud.update_status("sleeping")
                            continue

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
