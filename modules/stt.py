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

# TODO: implement SpeechToText class
