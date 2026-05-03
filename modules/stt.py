"""
MODULE 2 — Speech-to-Text (STT)
=================================
Converts spoken voice commands to text after the wake word fires.
Primary engine: Google Web Speech API (free, no key for basic use).
Offline fallback: openai-whisper running locally (base model).
Configurable energy_threshold and pause_threshold from config.json.

Tech: SpeechRecognition, openai-whisper
Config: energy_threshold, pause_threshold
Output: Plain text string → passed to NLP Engine (Module 3)
"""

import speech_recognition as sr
import numpy as np


class SpeechToText:
    def __init__(self, config: dict):
        self.config = config
        self.recognizer = sr.Recognizer()
        
        # Load config
        stt_config = self.config.get("stt", {})
        self.recognizer.energy_threshold = stt_config.get("energy_threshold", 300)
        self.recognizer.pause_threshold = stt_config.get("pause_threshold", 0.8)
        self.timeout = stt_config.get("timeout", 5)
        
        self.whisper_model = None

    def listen(self) -> sr.AudioData | None:
        """Captures audio from the microphone after the wake word is triggered."""
        print("[STT] Listening for your command...")
        try:
            with sr.Microphone() as source:
                # Brief calibration
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                # Listen with configured limits
                audio = self.recognizer.listen(source, timeout=self.timeout, phrase_time_limit=15)
                return audio
        except sr.WaitTimeoutError:
            print("[STT] Timeout: No speech detected.")
            return None
        except Exception as e:
            print(f"[STT] Error capturing audio: {e}")
            return None

    def transcribe(self, audio: sr.AudioData) -> str | None:
        """Transcribes the captured AudioData to text."""
        if not audio:
            return None
            
        print("[STT] Transcribing...")
        try:
            # Primary: Google Web Speech API
            text = self.recognizer.recognize_google(audio)
            return text.strip()
            
        except sr.UnknownValueError:
            print("[STT] Could not understand the audio.")
            return None
        except sr.RequestError as e:
            print(f"[STT] Google API unreachable: {e}. Falling back to Whisper...")
            return self._transcribe_whisper(audio)
            
    def _transcribe_whisper(self, audio: sr.AudioData) -> str | None:
        """Offline fallback using OpenAI Whisper."""
        try:
            import whisper
            
            if self.whisper_model is None:
                print("[STT] Loading Whisper base model (one-time load)...")
                # Load base model, suppress fp16 warning if running on CPU
                self.whisper_model = whisper.load_model("base")
                
            # Convert sr.AudioData to numpy array for Whisper
            audio_data = np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0
            
            # Transcribe
            result = self.whisper_model.transcribe(audio_data, fp16=False)
            return result["text"].strip()
            
        except ImportError:
            print("[STT] openai-whisper not installed. Cannot use offline fallback.")
            return None
        except Exception as e:
            print(f"[STT] Whisper fallback failed: {e}")
            return None

