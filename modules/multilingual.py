from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator
from gtts import gTTS
import os
import tempfile
import time

class MultilingualEngine:
    SUPPORTED = {"en": "English", "ur": "Urdu"}

    def __init__(self):
        # faster-whisper base model — auto language detection
        self.whisper = WhisperModel("base", device="cpu", compute_type="int8")
        self._current_lang = "en"

    def transcribe_with_language(self, audio_path: str) -> tuple[str, str]:
        """Returns (transcribed_text, detected_language_code)."""
        segments, info = self.whisper.transcribe(
            audio_path,
            beam_size=5,
            language=None,       # auto-detect
            task="transcribe"
        )
        text = " ".join(s.text.strip() for s in segments).strip()
        lang = info.language  # "en", "ur", etc.
        self._current_lang = lang if lang in self.SUPPORTED else "en"
        return text, self._current_lang

    def transcribe_audio_data(self, audio) -> tuple[str, str]:
        """Transcribes sr.AudioData by writing it to a temporary wav file first."""
        import wave
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
                with wave.open(tmp_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(audio.sample_rate)
                    wf.writeframes(audio.get_raw_data())

            text, lang = self.transcribe_with_language(tmp_path)
            
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
                
            return text, lang
        except Exception as e:
            print(f"[Multilingual] transcribe_audio_data failed: {e}")
            return "", "en"

    def translate_to_english(self, text: str, source_lang: str = "ur") -> str:
        if source_lang == "en":
            return text
        try:
            return GoogleTranslator(source=source_lang, target="en").translate(text)
        except Exception as e:
            print(f"[Multilingual] Translation to English failed: {e}")
            return text

    def translate_from_english(self, text: str, target_lang: str = "ur") -> str:
        if target_lang == "en":
            return text
        try:
            return GoogleTranslator(source="en", target=target_lang).translate(text)
        except Exception as e:
            print(f"[Multilingual] Translation from English failed: {e}")
            return text

    def speak(self, text: str, lang: str = None, speak_english_func: callable = None):
        """Speak in the given language; falls back to speak_english_func or local pyttsx3."""
        lang = lang or self._current_lang
        if lang == "en":
            if speak_english_func:
                speak_english_func(text)
            else:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
        else:
            # gTTS for Urdu and other languages
            try:
                tts = gTTS(text=text, lang=lang, slow=False)
                temp_path = os.path.join(tempfile.gettempdir(), f"nova_tts_{int(time.time())}.mp3")
                tts.save(temp_path)
                if os.name == 'nt':
                    os.system(f'start "" "{temp_path}"')
            except Exception as e:
                print(f"[Multilingual] gTTS speak failed: {e}")

    @property
    def active_language(self) -> str:
        return self._current_lang

multilingual = MultilingualEngine()
