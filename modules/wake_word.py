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
    def __init__(self, wake_event: threading.Event, config: dict):
        self.wake_event = wake_event
        self.config = config
        self.running = False
        self.recognizer = sr.Recognizer()
        
        # Load config
        self.wake_phrase = self.config.get("nova", {}).get("wake_phrase", "Hey NOVA").lower()
        self.energy_threshold = self.config.get("stt", {}).get("energy_threshold", 300)
        self.recognizer.energy_threshold = self.energy_threshold
        
    def start(self):
        """Starts the wake word detector in a daemon thread."""
        self.running = True
        thread = threading.Thread(target=self._listen_loop, daemon=True, name="WakeWordThread")
        thread.start()
        print("[WakeWord] Detector started in background. Listening for:", self.wake_phrase)
        
    def stop(self):
        """Stops the wake word detector."""
        self.running = False
        
    def _listen_loop(self):
        import time
        
        while self.running:
            # 1. Wait while the main pipeline is busy (TTS/STT running)
            while self.wake_event.is_set() and self.running:
                time.sleep(0.5)
                
            if not self.running:
                break
                
            # 2. Main pipeline is idle. Open a fresh microphone stream.
            try:
                with sr.Microphone() as source:
                    # Calibrate once per session
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # 3. Fast continuous listening loop (no dropped frames)
                    while self.running and not self.wake_event.is_set():
                        try:
                            audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                            
                            text = self.recognizer.recognize_google(audio).lower()
                            text = text.replace(",", "").replace(".", "").replace("!", "").replace("?", "")
                            
                            if self.wake_phrase in text:
                                print(f"\n[WakeWord] Wake phrase '{self.wake_phrase}' detected!")
                                self.wake_event.set()
                                # BREAK out of the inner loop to EXIT the 'with' block!
                                # This completely closes our microphone stream so STT can use it!
                                break 
                                
                        except sr.WaitTimeoutError:
                            pass
                        except sr.UnknownValueError:
                            pass
                        except sr.RequestError as e:
                            print(f"[WakeWord] API Error: {e}")
                            
            except Exception as e:
                # Ignore random audio device errors and retry
                time.sleep(1)

