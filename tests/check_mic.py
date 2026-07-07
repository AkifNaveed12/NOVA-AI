"""
Quick mic diagnostic — run this BEFORE running main.py.
It shows the current ambient energy level so you can tune energy_threshold.
"""

import speech_recognition as sr
import time

print("=== NOVA MIC DIAGNOSTIC ===\n")

# List microphones
print("Available microphones:")
for i, name in enumerate(sr.Microphone.list_microphone_names()):
    try:
        print(f"  [{i}] {name}")
    except Exception:
        print(f"  [{i}] [Encoding Error]")
print()

r = sr.Recognizer()
mic = sr.Microphone()

print("Opening mic stream...")
with mic as source:
    print("Measuring ambient noise (2 seconds, stay quiet)...")
    r.adjust_for_ambient_noise(source, duration=2)
    print(f"\n  Calibrated energy_threshold = {r.energy_threshold:.0f}")
    print(f"  (This is the minimum energy level for your room)")
    print(f"\n  Recommended config.json values:")
    suggested = max(300, int(r.energy_threshold * 1.2))
    print(f"    wake_word.energy_threshold = {suggested}")
    print(f"    stt.energy_threshold = {suggested}")

    print("\n\nNow testing wake word detection...")
    print("Say 'hey nova' clearly:\n")
    
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.5

    for attempt in range(5):
        try:
            print(f"  Attempt {attempt+1}/5: Listening...", end=" ", flush=True)
            audio = r.listen(source, timeout=3, phrase_time_limit=4)
            text = r.recognize_google(audio).lower()
            print(f"Heard: '{text}'")
            if "hey nova" in text or "nova" in text:
                print("  ✅ Wake word detected correctly!")
        except sr.WaitTimeoutError:
            print("(timeout — no speech heard)")
        except sr.UnknownValueError:
            print("(could not understand)")
        except sr.RequestError as e:
            print(f"(API error: {e})")

print("\n=== DIAGNOSTIC COMPLETE ===")
