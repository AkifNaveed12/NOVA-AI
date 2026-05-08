"""
MODULE 1 — Wake Word Detection
===============================
Keeps NOVA always listening in the background using a daemon thread.
Detects "Hey NOVA" via SpeechRecognition + Google Web Speech API.
Signals the main pipeline via threading.Event when the wake phrase is detected.

Thread safety: Uses a dedicated `_mic_active` flag to ensure the background
listener completely stops reading from the shared mic stream BEFORE the main
pipeline begins listening. This prevents the race condition where both
threads fight over the same audio buffer.

Tech: SpeechRecognition, threading
Thread: Daemon thread — never touches main thread directly
Output: threading.Event signal to main pipeline
"""

import threading
import speech_recognition as sr


class WakeWordDetector:
    def __init__(self, wake_event: threading.Event, config: dict, shared_mic=None):
        """
        Args:
            wake_event: Event set when wake word is detected. Main pipeline waits on this.
            config: Full config dictionary loaded from config.json.
            shared_mic: Pre-opened sr.Microphone instance (shared with STT for zero latency).
        """
        self.wake_event = wake_event

        # Read from the correct config section — this was the primary bug
        ww_cfg = config.get("wake_word", {})
        self.wake_phrase = ww_cfg.get("phrase", "hey nova").lower()
        self.energy_threshold = ww_cfg.get("energy_threshold", 400)
        self.phrase_time_limit = ww_cfg.get("phrase_time_limit", 4)
        
        # Own recognizer for wake word — separate from STT's recognizer
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = self.energy_threshold
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15  # Adapt faster
        self.recognizer.pause_threshold = 0.5  # Detect wake phrase end quickly

        self.shared_mic = shared_mic
        self.thread = None
        self.running = False
        # This flag tells the inner listen loop to IMMEDIATELY stop draining the mic
        self._listening_active = threading.Event()
        self._listening_active.set()  # Start in active state

    def start(self):
        """Starts the background listening thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._listen_loop, daemon=True, name="WakeWordThread")
            self.thread.start()
            print(f"[WakeWord] Detector started. Listening for: '{self.wake_phrase}'")

    def stop(self):
        """Signals the background thread to stop."""
        self.running = False
        self._listening_active.set()  # Unblock if waiting

    def pause(self):
        """Called by main pipeline to pause wake word detection while STT/TTS is active."""
        self._listening_active.clear()

    def resume(self):
        """Called by main pipeline to resume passive listening."""
        self._listening_active.set()

    def _listen_loop(self):
        import time

        while self.running:
            # Block here while main pipeline is busy (STT listening or TTS speaking)
            self._listening_active.wait(timeout=0.5)

            if not self.running:
                break

            if not self._listening_active.is_set():
                continue

            try:
                # Single listen attempt — short phrase_time_limit is critical
                # because we only need to capture "Hey NOVA", not a full sentence
                audio = self.recognizer.listen(
                    self.shared_mic,
                    timeout=0.5,        # Give up quickly if silence
                    phrase_time_limit=self.phrase_time_limit
                )

                # Only transcribe if we haven't been paused mid-listen
                if not self._listening_active.is_set():
                    continue

                text = self.recognizer.recognize_google(audio).lower()
                text = text.replace(",", "").replace(".", "").replace("!", "").replace("?", "")

                if self.wake_phrase in text:
                    print(f"\n[WakeWord] Detected: '{self.wake_phrase}'")
                    # CRITICAL: Pause ourselves BEFORE setting wake_event
                    # so STT can immediately use the mic without a race condition
                    self.pause()
                    self.wake_event.set()

            except sr.WaitTimeoutError:
                # Normal — no speech detected in timeout window, loop again
                pass
            except sr.UnknownValueError:
                # Speech detected but not recognizable — loop again
                pass
            except sr.RequestError as e:
                print(f"[WakeWord] Google API error: {e}. Retrying in 2s...")
                time.sleep(2)
            except Exception as e:
                # Log unexpected errors but keep running
                import traceback
                traceback.print_exc()
                time.sleep(0.5)
