"""
NOVA AI - Groq API Live Test
Run: python tests/check_groq.py
Makes a real API call to Groq to verify the key is valid.
"""
import os
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

print("\n" + "="*55)
print("  NOVA AI - Groq API Live Test")
print("="*55)

api_key = os.getenv("GROQ_API_KEY", "")
if not api_key or api_key in ("gsk_your_key_here", "your_groq_key", ""):
    print("\n  [!!] GROQ_API_KEY is not set in .env")
    print("  Get your free key at: https://console.groq.com")
    sys.exit(1)

print("\n  Key found: {}...{}".format(api_key[:8], api_key[-4:]))

print("\n  Checking groq package...")
try:
    import groq
    print("  groq package: installed [OK]")
except ImportError:
    print("  MISSING - run: pip install groq")
    sys.exit(1)

print("\n  Making live API call to Groq (llama3-70b-8192)...")
print("  Prompt: 'Reply with exactly: NOVA ONLINE'")
print("  Waiting...", end="", flush=True)

try:
    start = time.time()
    client = groq.Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You are a test assistant. Follow instructions exactly."},
            {"role": "user",   "content": "Reply with exactly this text and nothing else: NOVA ONLINE"}
        ],
        max_tokens=10,
        temperature=0.0,
    )
    elapsed = time.time() - start
    response = completion.choices[0].message.content.strip()
    print(" Done ({:.2f}s)".format(elapsed))
    print("\n  Model response: '{}'".format(response))

    if "NOVA" in response.upper() or "ONLINE" in response.upper():
        print("\n  [OK] Groq API is working correctly")
        print("  [OK] Response time: {:.2f}s".format(elapsed))
    else:
        print("\n  [OK] Response unexpected but API is reachable")
        print("  Key works, model responded")

except Exception as e:
    etype = type(e).__name__
    print("\n  [!!] Error: {}: {}".format(etype, e))
    if "authentication" in str(e).lower() or "401" in str(e):
        print("  Your GROQ_API_KEY appears to be invalid.")
        print("  Go to https://console.groq.com and check your key.")
    sys.exit(1)

print("\n" + "="*55)
print("  RESULT: Groq API is fully operational [OK]")
print("  Ready for Module 4 (Day 4) implementation.")
print("="*55 + "\n")
