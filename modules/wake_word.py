"""
MODULE 1 — Wake Word Detection
===============================
Keeps NOVA always listening in the background using a daemon thread.
Detects "Hey NOVA" via pvporcupine (offline) or energy-threshold
fallback using SpeechRecognition. Signals the main pipeline via
threading.Event when the wake phrase is detected.

Tech: pvporcupine, SpeechRecognition, threading
Thread: Daemon thread — never touches main thread directly
Output: threading.Event signal to main pipeline
"""

import os
import threading
import speech_recognition as sr


class WakeWordDetector:
    def __init__(self, wake_event: threading.Event, config: dict, shared_mic=None):
        """
        Initializes the wake word detector.
        Args:
            wake_event: Event to trigger when wake word is detected.
            config: Full config dictionary.
            shared_mic: Pre-opened sr.Microphone instance to avoid latency.
        """
        self.wake_event = wake_event
        self.config = config.get("wake_word", {})
        
        self.engine = self.config.get("engine", "google")
        self.wake_phrase = self.config.get("phrase", "hey nova").lower()
        self.energy_threshold = self.config.get("energy_threshold", 4000)
        
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = self.energy_threshold
        self.recognizer.dynamic_energy_threshold = False # Disable dynamic thresholding to prevent spikes
        
        self.shared_mic = shared_mic
        self.thread = None
        self.running = False
        
    def start(self):
        """Starts the background listening thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.thread.start()
            print(f"[WakeWord] Detector started in background. Listening for: {self.wake_phrase}")
            
    def stop(self):
        """Stops the background listening thread."""
        self.running = False
        
    def _listen_loop(self):
        import time
        
        while self.running:
            # 1. Wait while the main pipeline is busy
            while self.wake_event.is_set() and self.running:
                time.sleep(0.1)
                
            if not self.running:
                break
                
            # 2. Main pipeline is idle. Use the pre-opened global microphone.
            try:
                # 3. Fast continuous listening loop
                while self.running and not self.wake_event.is_set():
                    try:
                        audio = self.recognizer.listen(self.shared_mic, timeout=1, phrase_time_limit=3)
                        
                        text = self.recognizer.recognize_google(audio).lower()
                        text = text.replace(",", "").replace(".", "").replace("!", "").replace("?", "")
                        
                        if self.wake_phrase in text:
                            print(f"\n[WakeWord] Wake phrase '{self.wake_phrase}' detected!")
                            self.wake_event.set()
                            break # Break to yield the microphone to STT
                            
                    except sr.WaitTimeoutError:
                        pass
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        print(f"[WakeWord] API Error: {e}")
                        
            except Exception as e:
                time.sleep(1)
