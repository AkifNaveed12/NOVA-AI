"""
NOVA AI - Environment Variable Diagnostic
Run: python tests/check_env.py
Checks that .env loads correctly and all required API keys are present.
"""
import os
import sys
import io

# Force UTF-8 output on Windows to avoid cp1252 issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

loaded = load_dotenv()

print("\n" + "="*55)
print("  NOVA AI - Environment Check")
print("="*55)
print("  .env loaded: {} \n".format("YES [OK]" if loaded else "NO - .env file not found!"))

# Placeholder values that count as "not set"
PLACEHOLDERS = {
    "your_groq_key", "your_owm_key", "your@gmail.com",
    "your_app_password", "gsk_your_key_here", "your_key_here",
    "your_gmail@gmail.com", "xxxx xxxx xxxx xxxx",
    "your_porcupine_key_here", "", "your_groq_api_key_here",
    "your_openweather_key_here", "DEMO_KEY",
}

# NASA is special - DEMO_KEY is actually valid for dev
NASA_OK_VALUES = {"DEMO_KEY"}

REQUIRED_KEYS = [
    ("GROQ_API_KEY",        "Groq LLM (Module 4 - Brain)"),
    ("OPENWEATHER_API_KEY", "OpenWeatherMap (Module 5 - Weather)"),
    ("NASA_API_KEY",        "NASA APOD (Module 6 - News)"),
    ("GMAIL_ADDRESS",       "Gmail sender (Module 10 - Email)"),
    ("GMAIL_APP_PASSWORD",  "Gmail App Password (Module 10 - Email)"),
]

OPTIONAL_KEYS = [
    ("PORCUPINE_ACCESS_KEY", "Porcupine wake word (Module 1 - skipped, energy-threshold fallback active)"),
]

all_ok = True

print("  REQUIRED KEYS:")
print("  " + "-"*51)
for key, desc in REQUIRED_KEYS:
    value = os.getenv(key, "")
    # NASA_API_KEY: DEMO_KEY is acceptable
    if key == "NASA_API_KEY":
        is_set = bool(value)
    else:
        is_set = bool(value) and value not in PLACEHOLDERS

    status = "[OK] SET    " if is_set else "[!!] MISSING"

    hint = ""
    if is_set and len(value) > 6:
        hint = "  [{0}...{1}]".format(value[:6], value[-3:])
    elif is_set:
        hint = "  [{}]".format(value)

    print("  {}  {}".format(status, key))
    print("         -> {}{}".format(desc, hint))
    if not is_set:
        all_ok = False
    print()

print("  OPTIONAL KEYS:")
print("  " + "-"*51)
for key, desc in OPTIONAL_KEYS:
    value = os.getenv(key, "")
    is_set = bool(value) and value not in PLACEHOLDERS
    status = "[OK] SET    " if is_set else "[-]  NOT SET"
    print("  {}  {}".format(status, key))
    print("         -> {}".format(desc))
    print()

print("="*55)
if all_ok:
    print("  RESULT: All required keys loaded correctly [OK]")
    print("  Ready for Day 2 development.")
else:
    print("  RESULT: Some required keys are MISSING.")
    print("  Open .env and fill in the missing values.")
print("="*55 + "\n")
