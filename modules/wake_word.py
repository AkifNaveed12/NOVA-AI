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

# TODO: implement WakeWordDetector class
