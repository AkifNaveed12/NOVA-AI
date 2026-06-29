checks = []

# Python version
import sys
v = sys.version_info
checks.append(('Python 3.11+', v.major == 3 and v.minor >= 11))

# Core packages
try:
    import speech_recognition, groq, fastapi, pyttsx3, spacy
    checks.append(('Core packages', True))
except Exception as e:
    checks.append(('Core packages', False, str(e)))

# faster-whisper
try:
    from faster_whisper import WhisperModel
    checks.append(('faster-whisper', True))
except Exception as e:
    checks.append(('faster-whisper', False, str(e)))

# sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    checks.append(('sentence-transformers', True))
except Exception as e:
    checks.append(('sentence-transformers', False, str(e)))

# Tavily
try:
    from tavily import TavilyClient
    checks.append(('tavily', True))
except Exception as e:
    checks.append(('tavily', False, str(e)))

# DuckDuckGo
try:
    from duckduckgo_search import DDGS
    checks.append(('duckduckgo-search', True))
except Exception as e:
    checks.append(('duckduckgo-search', False, str(e)))

# pygetwindow
try:
    import pygetwindow
    checks.append(('pygetwindow', True))
except Exception as e:
    checks.append(('pygetwindow', False, str(e)))

# webdriver-manager
try:
    from webdriver_manager.chrome import ChromeDriverManager
    checks.append(('webdriver-manager', True))
except Exception as e:
    checks.append(('webdriver-manager', False, str(e)))

# Ollama API
try:
    import requests
    r = requests.get('http://localhost:11434/api/tags', timeout=3)
    checks.append(('Ollama running', r.status_code == 200))
except Exception:
     checks.append(('Ollama running', False, str(e)))

# Tavily API key
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('TAVILY_API_KEY', '')
checks.append(('TAVILY_API_KEY set', bool(key and 'your-actual' not in key and len(key) > 10)))

# Groq API key
gkey = os.getenv('GROQ_API_KEY', '')
checks.append(('GROQ_API_KEY set', bool(gkey and len(gkey) > 10)))

# spaCy model
try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
    checks.append(('spaCy en_core_web_sm', True))
except Exception as e:
    checks.append(('spaCy en_core_web_sm', False, str(e)))

print()
print('=' * 50)
print('NOVA AI — Pre-Flight Check Results')
print('=' * 50)
all_pass = True
for item in checks:
    name = item[0]
    passed = item[1]
    note = item[2] if len(item) > 2 else ''
    status = '✅' if passed else '❌'
    print(f'{status}  {name}' + (f'  →  {note}' if note else ''))
    if not passed:
        all_pass = False
print()
if all_pass:
    print('🎉 ALL CHECKS PASSED — Ready to start final-plan.md')
else:
    print('⚠️  Some checks failed — fix the ❌ items above before starting')
print('=' * 50)
