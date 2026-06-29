"""
MODULE 1 — Wake Word Detection
===============================
Keeps NOVA always listening in the background using a daemon thread.
Detects "Hey NOVA" via SpeechRecognition + Google Web Speech API.
Signals the main pipeline via threading.Event when the wake phrase is detected.

Key fixes applied:
- pause()/resume() API eliminates race condition with STT mic sharing
- Debounce: minimum 2.0s gap between consecutive wake events
- Short settle delay after resume() to let PyAudio buffer drain
- Reads config from correct wake_word section

Tech: SpeechRecognition, threading
Thread: Daemon thread — never touches main thread directly
Output: threading.Event signal to main pipeline
"""

import threading
import time
import speech_recognition as sr


class WakeWordDetector:
    def __init__(self, wake_event: threading.Event, config: dict, shared_mic=None):
        """
        Args:
            wake_event: Event set when wake word is detected. Main pipeline waits on this.
            config: Full config dictionary loaded from config.json.
            shared_mic: Pre-opened sr.Microphone instance (shared with STT).
        """
        self.wake_event = wake_event

        # Read from the correct config section
        ww_cfg = config.get("wake_word", {})
        self.wake_phrase = ww_cfg.get("phrase", "hey nova").lower()
        self.energy_threshold = ww_cfg.get("energy_threshold", 300)
        self.phrase_time_limit = ww_cfg.get("phrase_time_limit", 4)

        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = self.energy_threshold
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.10  # Faster adaptation
        self.recognizer.pause_threshold = 0.4  # Faster triggers

        self.shared_mic = shared_mic
        self.thread = None
        self.running = False

        # Pause flag: cleared by pause(), set by resume()
        self._active = threading.Event()
        self._active.set()

        # Debounce: track last detection time to avoid false re-triggers
        self._last_detected_at = 0.0
        self._debounce_seconds = 2.0   # Minimum gap between wake events

    def start(self):
        """Starts the background listening thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._listen_loop, daemon=True, name="WakeWordThread")
            self.thread.start()
            print(f"[WakeWord] Detector started. Listening for: '{self.wake_phrase}'")

    def stop(self):
        """Signals the background thread to stop and unblocks it."""
        self.running = False
        self._active.set()  # Unblock in case it's waiting

    def pause(self):
        """
        Called BEFORE the main pipeline starts STT listening.
        Clears the active flag so the detector stops draining the mic buffer.
        """
        self._active.clear()

    def resume(self):
        """
        Called AFTER the pipeline finishes speaking and draining the buffer.
        Adds a settle delay before re-arming to prevent false re-triggers
        from stale audio that accumulated during TTS playback.
        """
        # Settle: wait for buffer to clear before listening again
        # This runs in the voice_pipeline thread so it blocks the pipeline briefly
        time.sleep(1.2)
        self._active.set()

    def _listen_loop(self):
        """Main detection loop — runs in daemon thread."""

        while self.running:
            # Block while the main pipeline is busy (STT or TTS active)
            if not self._active.wait(timeout=0.3):
                continue

            if not self.running:
                break

            # Debounce guard — ignore detections too soon after the last one
            now = time.time()
            if (now - self._last_detected_at) < self._debounce_seconds:
                time.sleep(0.1)
                continue

            try:
                audio = self.recognizer.listen(
                    self.shared_mic,
                    timeout=0.5,
                    phrase_time_limit=self.phrase_time_limit
                )

                # Double-check we haven't been paused while listening
                if not self._active.is_set():
                    continue

                text = self.recognizer.recognize_google(audio).lower()
                text = text.replace(",", "").replace(".", "").replace("!", "").replace("?", "")

                wake_keywords = ["nova", "innova", "nava", "novel", "no standard", "no double", "no one", "hey no", "hi no", "hello no", "okay no", "ok no", "nov", "nav"]
                if self.wake_phrase in text or any(kw in text for kw in wake_keywords):
                    print(f"\n[WakeWord] Detected: '{text}'")
                    self._last_detected_at = time.time()
                    # Pause ourselves BEFORE setting wake_event so STT gets exclusive mic access
                    self.pause()
                    self.wake_event.set()

            except sr.WaitTimeoutError:
                # Normal — no speech in window, loop again immediately
                pass
            except sr.UnknownValueError:
                # Speech too unclear — loop again
                pass
            except sr.RequestError as e:
                print(f"[WakeWord] Google API error: {e}. Retrying in 3s...")
                time.sleep(3)
            except Exception as e:
                err_str = str(e).lower()
                if "unanticipated host error" in err_str or "-9999" in err_str or "overflow" in err_str:
                    print(f"[WakeWord] Mic error: {e}. Attempting restart...")
                    try:
                        # Safely close the stream without crashing on -9988
                        if getattr(self.shared_mic, 'stream', None) is not None:
                            try:
                                self.shared_mic.stream.close()
                            except Exception:
                                pass
                            finally:
                                self.shared_mic.stream = None
                                
                        # Fully rebuild PyAudio instance to clear Errno -9988
                        if getattr(self.shared_mic, 'audio', None) is not None:
                            try:
                                self.shared_mic.audio.terminate()
                            except Exception:
                                pass
                                
                        self.shared_mic.audio = self.shared_mic.pyaudio_module.PyAudio()
                        
                        self.shared_mic.__enter__()
                        print("[WakeWord] Mic restarted successfully.")
                    except Exception as ex:
                        print(f"[WakeWord] Mic restart failed: {ex}")
                time.sleep(0.5)
