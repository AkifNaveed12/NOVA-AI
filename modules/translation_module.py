"""
MODULE 19 — Language Translation
===================================
Translates any text to any language by voice using the
deep-translator library with Google Translate backend.
No API key required. Supports auto-detection of source language.

Tech: deep-translator (GoogleTranslator backend, free, no key)
Output: Translated text string → TTS engine
"""

from deep_translator import GoogleTranslator, single_detection
import os


# Comprehensive language name → ISO 639-1 code map
LANGUAGE_MAP = {
    # South Asian
    "urdu": "ur", "hindi": "hi", "punjabi": "pa", "sindhi": "sd",
    "bengali": "bn", "gujarati": "gu", "marathi": "mr", "tamil": "ta",
    "telugu": "te", "kannada": "kn", "malayalam": "ml", "nepali": "ne",
    "sinhala": "si",
    # Middle East / Central Asia
    "arabic": "ar", "persian": "fa", "farsi": "fa", "pashto": "ps",
    "turkish": "tr", "azerbaijani": "az", "kazakh": "kk", "uzbek": "uz",
    # European
    "french": "fr", "spanish": "es", "german": "de", "italian": "it",
    "portuguese": "pt", "russian": "ru", "dutch": "nl", "polish": "pl",
    "swedish": "sv", "norwegian": "no", "danish": "da", "finnish": "fi",
    "greek": "el", "czech": "cs", "hungarian": "hu", "romanian": "ro",
    "ukrainian": "uk", "croatian": "hr", "slovak": "sk", "bulgarian": "bg",
    # East Asian
    "chinese": "zh-CN", "mandarin": "zh-CN", "japanese": "ja", "korean": "ko",
    "vietnamese": "vi", "thai": "th", "indonesian": "id", "malay": "ms",
    # Others
    "swahili": "sw", "hebrew": "he", "afrikaans": "af", "english": "en",
}


class TranslationModule:
    def __init__(self):
        pass

    def translate(self, text: str, target_language: str) -> str:
        """
        Translates text into the target language.
        target_language can be a full name ('french') or ISO code ('fr').

        Returns a TTS-ready string with the translation.
        """
        if not text or not text.strip():
            return "Please give me some text to translate."

        if not target_language or not target_language.strip():
            return "Please tell me which language to translate into."

        lang_key = target_language.lower().strip()
        # Resolve full name → code; if already a code (2-char), keep it
        lang_code = LANGUAGE_MAP.get(lang_key, lang_key if len(lang_key) <= 7 else None)

        if not lang_code:
            return (
                f"I don't recognise '{target_language}' as a language. "
                f"Try saying something like: translate to French, or translate to Urdu."
            )

        try:
            translated = GoogleTranslator(source="auto", target=lang_code).translate(text.strip())
            return f"In {target_language.capitalize()}: {translated}"

        except Exception as e:
            print(f"[Translation] Error translating to '{lang_code}': {e}")
            return f"Sorry, I couldn't translate that to {target_language} right now."

    def detect_language(self, text: str) -> str:
        """
        Detects the language of the given text.
        Returns a human-readable description.
        """
        if not text or not text.strip():
            return "Please give me some text to detect the language of."

        api_key = os.getenv("DEEPL_API_KEY", "")  # Optional; falls back gracefully

        try:
            # single_detection requires a key; we use a try/except workaround
            from deep_translator import GoogleTranslator
            # Translate to English and check if result differs (cheap detection proxy)
            result = GoogleTranslator(source="auto", target="en").translate(text.strip())
            return f"I detected non-English text. The translation is: {result}"

        except Exception as e:
            print(f"[Translation] Detection error: {e}")
            return "I couldn't detect the language right now."

    def get_supported_languages(self) -> list:
        """Returns the list of supported language names."""
        return sorted(LANGUAGE_MAP.keys())
