"""
MODULE 19 — Translation
========================
Translates text between languages using deep-translator.
"""

from deep_translator import GoogleTranslator

class TranslationModule:
    def __init__(self, config: dict = None):
        self._config = config or {}
        
        # Simple map of spoken languages to codes
        self.lang_map = {
            "english": "en",
            "french": "fr",
            "spanish": "es",
            "german": "de",
            "arabic": "ar",
            "urdu": "ur",
            "hindi": "hi",
            "chinese": "zh-CN",
            "japanese": "ja",
            "italian": "it",
            "russian": "ru"
        }

    def translate(self, text: str, target_language: str) -> str:
        """Translates text to the target language name."""
        lang_code = self.lang_map.get(target_language.lower().strip())
        if not lang_code:
            return f"I don't know the language code for {target_language}."
            
        try:
            translator = GoogleTranslator(source="auto", target=lang_code)
            translated = translator.translate(text)
            return translated
        except Exception as e:
            print(f"[Translation] Error: {e}")
            return "Failed to translate the text."

    def detect_language(self, text: str) -> str:
        """Detects the language of the text."""
        try:
            from deep_translator.detection import single_detection
            # deep-translator detection can be tricky, simple fallback logic
            return "Language detection not fully supported yet."
        except Exception:
            return "Could not detect language."
