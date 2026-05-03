"""
NOVA AI - Microphone Diagnostic
Run: python tests/check_mic.py
Tests microphone detection, audio capture, and energy levels.
"""
import os
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("\n" + "="*55)
print("  NOVA AI - Microphone Check")
print("="*55)

# Step 1: Check SpeechRecognition
print("\n  [1/5] Checking SpeechRecognition install...")
try:
    import speech_recognition as sr
    print("       speech_recognition v{} [OK]".format(sr.__version__))
except ImportError:
    print("       MISSING - run: pip install SpeechRecognition")
    sys.exit(1)

# Step 2: Check PyAudio
print("\n  [2/5] Checking PyAudio install...")
try:
    import pyaudio
    pa = pyaudio.PyAudio()
    print("       PyAudio [OK]")
    pa.terminate()
except ImportError:
    print("       MISSING - run: pip install pyaudio")
    print("       If pip fails, download .whl from:")
    print("       https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
    sys.exit(1)
except Exception as e:
    print("       PyAudio error: {}".format(e))
    sys.exit(1)

# Step 3: List microphones
print("\n  [3/5] Listing available microphones...")
try:
    mic_names = sr.Microphone.list_microphone_names()
    if not mic_names:
        print("       NO MICROPHONES FOUND - check your mic connection")
        sys.exit(1)
    for i, name in enumerate(mic_names):
        marker = "  <-- will be used by NOVA" if i == 0 else ""
        print("       [{}] {}{}".format(i, name, marker))
    print("\n       {} microphone(s) detected [OK]".format(len(mic_names)))
except Exception as e:
    print("       Error listing microphones: {}".format(e))
    sys.exit(1)

# Step 4: Capture audio
print("\n  [4/5] Testing microphone capture (3 seconds)...")
print("       >>> Speak or make noise now <<<")
print("       Listening for up to 5 seconds...", end="", flush=True)

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.pause_threshold = 0.8

captured_energy = None
try:
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        ambient = recognizer.energy_threshold
        print("\n       Ambient noise calibrated: {:.0f}".format(ambient))
        print("       Capturing now - speak something...", end="", flush=True)
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
        print(" Captured [OK]")
        captured_energy = ambient
except sr.WaitTimeoutError:
    print("\n       TIMEOUT - no audio detected in 5 seconds")
    print("       Is your microphone plugged in and not muted?")
    sys.exit(1)
except Exception as e:
    print("\n       Capture error: {}".format(e))
    sys.exit(1)

# Step 5: Energy analysis
print("\n  [5/5] Energy level analysis...")
nova_threshold = 300
print("       NOVA config threshold:    {}".format(nova_threshold))
print("       Your ambient energy:      {:.0f}".format(captured_energy))

if captured_energy < nova_threshold * 0.7:
    print("\n  [OK] Quiet environment - NOVA will detect your voice reliably")
    print("       Keep energy_threshold at {} in config.json".format(nova_threshold))
elif captured_energy < nova_threshold:
    print("\n  [OK] Acceptable noise level")
    print("       energy_threshold of {} in config.json is fine".format(nova_threshold))
elif captured_energy < nova_threshold * 2:
    suggested = int(captured_energy * 1.3)
    print("\n  [!!] Somewhat noisy environment")
    print("       Consider increasing energy_threshold to {} in config.json".format(suggested))
else:
    suggested = int(captured_energy * 1.5)
    print("\n  [!!] Very noisy - NOVA may trigger falsely")
    print("       Set energy_threshold to {} in config.json".format(suggested))

print("\n" + "="*55)
print("  RESULT: Microphone is working [OK]")
print("  You can proceed to Day 2 (Module 1 - Wake Word)")
print("="*55 + "\n")
