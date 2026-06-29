"""
MODULE 2 — Speech-to-Text (STT)
=================================
Converts spoken voice commands to text after the wake word fires.
Primary engine: Google Web Speech API (free, no key for basic use).
Offline fallback: faster-whisper (base model, pre-loaded at startup).

Key design: Uses the shared microphone stream opened by main.py.
The recognizer is configured from config.json stt section.

Sprint 0 change: faster-whisper pre-loaded at __init__ to eliminate
cold-start latency (was 3-8s, now 0ms for fallback invocations).

Tech: SpeechRecognition, faster-whisper
Config: energy_threshold, pause_threshold, phrase_time_limit, timeout
Output: Plain text string → passed to NLP Engine (Module 3)
"""

import speech_recognition as sr
import numpy as np


class SpeechToText:
    def __init__(self, config: dict, shared_mic=None):
        # Read from the correct config section
        stt_cfg = config.get("stt", {})
        self.engine = stt_cfg.get("engine", "google")
        self.timeout = stt_cfg.get("timeout", 7)
        self.phrase_time_limit = stt_cfg.get("phrase_time_limit", 12)

        self.recognizer = sr.Recognizer()
        # Set ALL relevant thresholds from config
        self.recognizer.energy_threshold = stt_cfg.get("energy_threshold", 400)
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.pause_threshold = stt_cfg.get("pause_threshold", 0.6)
        self.recognizer.phrase_threshold = stt_cfg.get("phrase_threshold", 0.3)
        self.recognizer.non_speaking_duration = 0.3

        self.shared_mic = shared_mic
        self.whisper_model = None  # faster-whisper model (pre-loaded below)

        # ── Sprint 0: Pre-load faster-whisper at startup ──────────────────
        # This eliminates the 3–8s cold-start penalty on the first offline
        # transcription.  We do this in a try/except so that a missing
        # package never crashes the whole application.
        self._fw_model = None
        try:
            from faster_whisper import WhisperModel
            self._fw_model = WhisperModel("base", device="cpu", compute_type="int8")
            print("[STT] faster-whisper base model pre-loaded (offline fallback ready).")
        except Exception as _fw_err:
            print(f"[STT] faster-whisper not available ({_fw_err}). Will use openai-whisper if needed.")

    def listen(self, retries=1) -> sr.AudioData | None:
        """
        Listens on the shared mic stream and returns captured AudioData.
        The wake word detector must be paused before calling this.
        """
        print("[STT] Listening for your command...")
        for attempt in range(retries + 1):
            try:
                audio = self.recognizer.listen(
                    self.shared_mic,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_time_limit
                )
                return audio
            except sr.WaitTimeoutError:
                print("[STT] Timeout — no speech detected.")
                return None
            except Exception as e:
                print(f"[STT] Error capturing audio: {e}")
                err_str = str(e).lower()
                if "unanticipated host error" in err_str or "-9999" in err_str or "overflow" in err_str:
                    if attempt < retries:
                        print("[STT] Restarting microphone stream and retrying...")
                        try:
                            if getattr(self.shared_mic, 'stream', None) is not None:
                                self.shared_mic.__exit__(None, None, None)
                            
                            # Fully rebuild PyAudio instance to clear Errno -9988 (Stream closed)
                            if getattr(self.shared_mic, 'audio', None) is not None:
                                self.shared_mic.audio.terminate()
                            self.shared_mic.audio = self.shared_mic.pyaudio_module.PyAudio()
                            
                            self.shared_mic.__enter__()
                        except Exception as ex:
                            print(f"[STT] Mic restart failed: {ex}")
                        continue
                return None

    def transcribe(self, audio: sr.AudioData) -> str | None:
        """Transcribes the captured AudioData to text using Google, falls back to Whisper."""
        if not audio:
            return None

        print("[STT] Transcribing...")
        try:
            text = self.recognizer.recognize_google(audio)
            return text.strip()

        except sr.UnknownValueError:
            print("[STT] Could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"[STT] Google API unreachable: {e}. Trying Whisper fallback...")
            return self._transcribe_whisper(audio)

    def _transcribe_whisper(self, audio: sr.AudioData) -> str | None:
        """
        Offline fallback transcription.
        Uses pre-loaded faster-whisper model (Sprint 0) if available;
        falls back to openai-whisper as a last resort.
        """
        # ── Tier 1: faster-whisper (pre-loaded, ~250ms on CPU) ───────────
        if self._fw_model is not None:
            try:
                import tempfile, wave
                audio_data = np.frombuffer(
                    audio.get_raw_data(), np.int16
                ).flatten().astype(np.float32) / 32768.0

                # faster-whisper needs a file path, not raw numpy array
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name
                    with wave.open(tmp_path, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)  # 16-bit
                        wf.setframerate(audio.sample_rate)
                        wf.writeframes(audio.get_raw_data())

                segments, _info = self._fw_model.transcribe(
                    tmp_path, beam_size=5, language="en"
                )
                text = " ".join(s.text.strip() for s in segments).strip()

                import os
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

                if text:
                    print(f"[STT] faster-whisper transcribed: {text!r}")
                    return text
            except Exception as fw_err:
                print(f"[STT] faster-whisper fallback error: {fw_err}")

        # ── Tier 2: openai-whisper (lazy-load, legacy fallback) ──────────
        try:
            import whisper

            if self.whisper_model is None:
                print("[STT] Loading openai-whisper base model (one-time)...")
                self.whisper_model = whisper.load_model("base")

            audio_data = np.frombuffer(
                audio.get_raw_data(), np.int16
            ).flatten().astype(np.float32) / 32768.0
            result = self.whisper_model.transcribe(audio_data, fp16=False)
            return result["text"].strip()

        except ImportError:
            print("[STT] openai-whisper not installed either — offline STT unavailable.")
            return None
        except Exception as e:
            print(f"[STT] All offline fallbacks failed: {e}")
            return None
