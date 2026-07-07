# main.py — NOVA AI Entry Point
# Neural Orchestrated Voice Assistant with Autonomous Intelligence
# Python 3.11 | Windows 10/11 | All free tools

import os
# Force CPU-only for TensorFlow/DeepFace to prevent GPU VRAM exhaustion and WebView2 crashes
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import sys
# Reconfigure console output to UTF-8 to prevent UnicodeEncodeError crashes on Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import threading
import queue
import time
from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()


def main() -> None:
    """Entry point — initialises all threads and launches HUD."""

    # ── Singleton guard — prevent two instances fighting over the mic ──
    from pathlib import Path
    _lockfile = Path("data/.nova.lock")
    _lockfile.parent.mkdir(exist_ok=True)
    try:
        import msvcrt
        _lock_fd = open(_lockfile, "w")
        msvcrt.locking(_lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
    except (OSError, IOError):
        print("NOVA AI is already running! Close the other instance first.")
        return

    print("NOVA AI — Initializing...")
    
    # Initialize assignment pipeline folders
    from pathlib import Path
    Path("nova_inbox").mkdir(exist_ok=True)
    Path("nova_outbox").mkdir(exist_ok=True)

    from modules.config_manager import config_proxy
    config = config_proxy

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
    from modules.memory_system import db_singleton as db_manager
    from modules.hud_interface import NOVAHud
    # Module 1: Context Scanner — Flagship PC awareness feature
    from modules.context_scanner import context_scanner

    # ── Initialize Modules ────────────────────────────────────────────
    from modules.activity_log import ActivityLogger
    activity_logger = ActivityLogger(db_manager)
    
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
    
    print("[STT] Available microphones:")
    for i, name in enumerate(sr.Microphone.list_microphone_names()):
        try:
            print(f"  [{i}] {name}")
        except Exception:
            try:
                # Handle potential Windows console encoding issues gracefully
                clean_name = name.encode('ascii', errors='ignore').decode('ascii').strip()
                print(f"  [{i}] {clean_name}")
            except Exception:
                print(f"  [{i}] [Encoding Error]")
                
    stt_cfg = config.get("stt", {})
    mic_idx = stt_cfg.get("device_index", None)
    if mic_idx is not None:
        try:
            mic_idx = int(mic_idx)
            # Validate that the chosen index is actually an input device
            mic_names = sr.Microphone.list_microphone_names()
            if mic_idx >= len(mic_names):
                print(f"[STT] device_index {mic_idx} out of range — falling back to system default.")
                mic_idx = None
            else:
                name_lower = mic_names[mic_idx].lower()
                if "output" in name_lower or "speaker" in name_lower:
                    print(f"[STT] device_index {mic_idx} is an output device — falling back to system default.")
                    mic_idx = None
                else:
                    print(f"[STT] Using configured microphone index: {mic_idx}")
        except ValueError:
            mic_idx = None
            print("[STT] Invalid device_index in config.json, using default microphone.")
    else:
        print("[STT] Using default microphone index.")

    shared_mic = sr.Microphone(device_index=mic_idx)

    stt = SpeechToText(config, shared_mic=shared_mic)
    wake_word = WakeWordDetector(wake_event, config, shared_mic=shared_mic, stt_instance=stt)

    import pyttsx3
    import tempfile
    from gtts import gTTS
    import os

    tts_cfg = config.get("tts", {})

    def speak(text: str, lang: str = "en", english_translation: str = None):
        """Speaks the text aloud using pyttsx3 (for English) or gTTS (for other languages)."""
        hud.update_status("speaking")
        from modules.api_server import push_status as _push
        
        if lang != "en" and english_translation:
            hud_log_text = f"{text}\nTranslation: {english_translation}"
            hud.log_message("nova", hud_log_text)
            print(f"[NOVA ({lang})] {text} (EN: {english_translation})")
            try:
                _push("speaking", text[:60])
            except Exception:
                pass
        else:
            hud.log_message("nova", text)
            print(f"[NOVA] {text}")
            try:
                _push("speaking", text[:60])
            except Exception:
                pass
        
        if lang == "en":
            import subprocess, sys
            rate = tts_cfg.get("rate", 175)
            volume = tts_cfg.get("volume", 0.9)
            script = f"import pyttsx3, sys; e=pyttsx3.init(); e.setProperty('rate', {rate}); e.setProperty('volume', {volume}); e.say(sys.argv[1]); e.runAndWait()"
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
            subprocess.run([sys.executable, "-c", script, text], creationflags=flags)
        else:
            from modules.multilingual import multilingual
            multilingual.speak(text, lang=lang)
            
        hud.update_status("sleeping")
        try:
            _push("sleeping")
        except Exception:
            pass

    def speak_online(text: str):
        """Fallback TTS using gTTS."""
        print(f"[NOVA (gTTS)] {text}")
        try:
            tts = gTTS(text=text, lang='en')
            temp_path = os.path.join(tempfile.gettempdir(), "nova_tts.mp3")
            tts.save(temp_path)
            # Use built-in OS command to play audio on Windows
            if os.name == 'nt':
                os.system(f'start "" "{temp_path}"')
        except Exception as e:
            print(f"[TTS Error] {e}")

    # Define STT wrapper globally for multi-turn flows (email, etc.)
    def _listen_once() -> str:
        hud.update_status("listening")
        _audio = stt.listen()
        hud.update_status("processing")
        if _audio:
            if config.get("multilingual", {}).get("enabled", True):
                from modules.multilingual import multilingual
                _text, _lang = multilingual.transcribe_audio_data(_audio)
                if _lang != "en":
                    _eng_text = multilingual.translate_to_english(_text, _lang)
                    print(f"[USER follow-up ({_lang})] {_text} (EN: {_eng_text})")
                    hud.log_message("user", _text)
                    return _eng_text
            else:
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
        """Polls inbox every 60s; announces when unread count is higher than last seen."""
        # Track the set of message-IDs already announced, not just a count.
        # This way reading emails on another device correctly resets the baseline,
        # and new arrivals are always caught regardless of current count.
        last_count = 0
        while True:
            time.sleep(60)
            if not wake_event.is_set():
                try:
                    new_emails = em.check_inbox(unseen_only=True)
                    count = len(new_emails)
                    # Always update baseline to current; announce only net-new arrivals
                    if count > last_count:
                        net_new = count - last_count
                        print(f"[EmailPoller] {net_new} new email(s) arrived (total unseen: {count}).")
                        announcement_queue.put(
                            f"You have {net_new} new email{'s' if net_new > 1 else ''}. "
                            "Just say, check my emails, if you want me to read them."
                        )
                    # Always sync the baseline so reads on other devices are reflected
                    last_count = count
                except Exception as e:
                    print(f"[EmailPoller] Error: {e}")

    threading.Thread(target=email_poller, daemon=True, name="EmailPollerThread").start()

    # ── ReminderEngine — Day 15 ───────────────────────────────────────
    from modules.notes_reminders import RemindersModule, ReminderEngine
    _reminders_module = RemindersModule()
    reminder_engine = ReminderEngine(_reminders_module, announcement_queue, hud_ticker_queue)
    reminder_engine.start()

    # ── Gesture Engine — Day 18-19 (Placeholder, started after FaceLogin) ──
    gesture_engine = None

    # Define the voice pipeline thread
    def voice_pipeline():
        """Background thread: wakes on event, listens, routes, speaks, loops."""
        import pythoncom
        pythoncom.CoInitialize()

        def extract_command(text: str, wake_phrase: str) -> str:
            text_lower = text.lower().strip()
            wake_keywords = [wake_phrase, "hey nova", "innova", "nava", "novel", "no standard", "no double", "no one", "hey no", "hi no", "hello no", "okay no", "ok no", "nov", "nav"]
            for kw in wake_keywords:
                if kw in text_lower:
                    parts = text_lower.split(kw, 1)
                    if len(parts) > 1:
                        cmd = parts[1].strip()
                        cmd = cmd.lstrip(",.!? ")
                        if cmd:
                            return cmd
            return ""

        from modules.api_server import push_status

        from modules.personality import PersonalityModule
        _personality_startup = PersonalityModule()
        
        # Brief settle delay — speak() runs TTS in a subprocess so no COM
        # conflict with pywebview; we just let threads finish initialising.
        time.sleep(1.0)

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
                push_status("sleeping")

                # Block until wake word detector fires
                triggered = wake_event.wait(timeout=1.0)
                if not triggered:
                    continue
                    
                # At this point, wake_word is already paused (called self.pause()
                # before setting the event), so STT has exclusive mic access.

                wake_text = getattr(wake_word, "detected_text", "")
                wake_word.detected_text = ""  # Clear immediately
                
                cmd_text = ""
                if wake_text:
                    cmd_text = extract_command(wake_text, wake_word.wake_phrase)

                if cmd_text:
                    print(f"[VoicePipeline] Extracted command from single-breath wake utterance: '{cmd_text}'")
                    hud.update_status("processing")
                    push_status("processing")
                    text = cmd_text
                    detected_lang = "ur" if any(ord(c) > 127 for c in cmd_text) else "en"
                else:
                    hud.update_status("listening")
                    push_status("listening")
                    audio = stt.listen()

                    if audio:
                        hud.update_status("processing")
                        push_status("processing")
                        
                        if config.get("multilingual", {}).get("enabled", True):
                            from modules.multilingual import multilingual
                            text, detected_lang = multilingual.transcribe_audio_data(audio)
                        else:
                            text = stt.transcribe(audio)
                            detected_lang = "en"
                    else:
                        text = None

                    if text:
                        if detected_lang != "en":
                            english_text = multilingual.translate_to_english(text, detected_lang)
                            print(f"\n[USER ({detected_lang})] {text} (EN: {english_text})")
                        else:
                            english_text = text
                            print(f"\n[USER] {text}")
                            
                        hud.log_message("user", text)

                        result = nlp_process(english_text)
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
                            push_status("sleeping")
                            continue

                        # Normalise: None means the module had nothing to say
                        if response is None:
                            response = ""

                        activity_id = activity_logger.log(
                            command_text=text,
                            module_triggered=intent,
                            response_summary=response,
                            success=True
                        )

                        if intent == "conversation" or intent in nova_core.GROQ_INTENTS:
                            db_manager.log_conversation("user", text, activity_id=activity_id)
                            db_manager.log_conversation("assistant", response, activity_id=activity_id)

                        if response:
                            if detected_lang != "en":
                                response_local = multilingual.translate_from_english(response, detected_lang)
                                speak(response_local, lang=detected_lang, english_translation=response)
                            else:
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
                push_status("sleeping")

        except Exception as e:
            import traceback
            print(f"\nNOVA AI — Pipeline Error: {e}")
            traceback.print_exc()
            wake_word.stop()

    # Initialize and start assignment pipeline components
    from modules.assignment_manager import AssignmentManager
    from modules.folder_watcher import FolderWatcher

    assignment_manager = AssignmentManager(
        db_manager=db_manager,
        speak_func=speak,
        listen_func=_listen_once,
        wake_word=wake_word
    )
    folder_watcher = FolderWatcher(
        inbox_path=config.get("assignment_pipeline", {}).get("inbox_folder", "nova_inbox"),
        assignment_manager=assignment_manager
    )
    folder_watcher.start()

    # Startup Face Login check
    from modules.face_auth import FaceAuth
    face_auth_module = FaceAuth(db_manager)
    user_name = config.get("user", {}).get("name", "Akif")

    if face_auth_module.is_registered(user_name):
        print("[FaceLogin] Scanning for registered face...")
        auth_result = face_auth_module.verify_from_webcam(user_name)
        if auth_result.get("authenticated"):
            print(f"[FaceLogin] ✅ Welcome back, {user_name}! (similarity: {auth_result['similarity']})")
            hud.log_message("nova", f"Welcome back, {user_name} (Face Verified)!")
        else:
            print("[FaceLogin] ❌ Face not recognized. Continuing with standard startup.")
    else:
        print("[FaceLogin] No face registered. Run registration via app or voice command.")

    # ── Core start sequence ───────────────────────────────────────────
    # Start background threads
    wake_word.start()

    # ── Start Gesture Engine after FaceLogin releases the webcam ─────
    if config.get("modules", {}).get("gesture_control", False):
        from modules.gesture_engine import GestureEngine
        gesture_cfg = config.get("gesture", {})
        pinch_thresh = gesture_cfg.get("pinch_threshold_px", 30) / 300.0 
        gesture_engine = GestureEngine(
            camera_index=gesture_cfg.get("camera_index", 0),
            fps_target=gesture_cfg.get("fps_target", 20),
            debounce_seconds=gesture_cfg.get("debounce_seconds", 0.4),
            pinch_threshold=pinch_thresh
        )
        gesture_engine.start()

    # Module 1: Start context scanner daemon (10s polling, PC awareness)
    context_scanner.start()
    print("[ContextScanner] Started — building PC context for Groq injection.")

    from modules.api_server import start_api_server, start_udp_broadcaster
    api_thread = threading.Thread(target=start_api_server, daemon=True, name="APIServerThread")
    api_thread.start()
    start_udp_broadcaster(api_port=8000)
    print("[API] Server starting on http://0.0.0.0:8000")

    pipeline_thread = threading.Thread(target=voice_pipeline, daemon=True)
    pipeline_thread.start()

    # Launch HUD in main thread (pywebview.start() MUST run on main thread)
    # This call blocks until the HUD window is closed by the user.
    try:
        hud.start()
    except Exception as e:
        print(f"[HUD] Error: {e}")

    # After hud.start() returns (user closed window OR pywebview crashed),
    # keep the process alive so voice pipeline daemon threads keep running.
    # Press Ctrl+C to trigger a clean shutdown.
    print("[NOVA] HUD closed — voice pipeline still active. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    print("\nNOVA AI — Shutting down gracefully...")
    try:
        folder_watcher.stop()
        context_scanner.stop()  # Module 1: Stop PC context scanner
        if gesture_engine:
            gesture_engine.stop()
        wake_word.stop()
        from modules.api_server import stop_api_server, stop_udp_broadcaster
        stop_api_server()
        stop_udp_broadcaster()
        if getattr(shared_mic, 'stream', None) is not None:
            shared_mic.__exit__(None, None, None) # Close the PyAudio stream
    except OSError:
        pass
    import os
    os._exit(0)


if __name__ == "__main__":
    main()
