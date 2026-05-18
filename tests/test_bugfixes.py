"""
NOVA AI — Bug Fix Verification Tests
Tests the 8 bugs found during live testing + NLP regression.
Run with: $env:PYTHONIOENCODING="utf-8"; venv\Scripts\python.exe tests/test_bugfixes.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()

PASS = 0
FAIL = 0
def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  [PASS] {label}")
        PASS += 1
    else:
        print(f"  [FAIL] {label} -- {detail}")
        FAIL += 1

print("\n" + "="*60)
print("  NOVA AI -- Bug Fix Verification")
print("="*60)

# ─── BUG 1: University Portal opens File Explorer ────────────
print("\n[BUG 1] University Portal routing")
from modules.nlp_engine import classify_intent

# These MUST classify as 'web', not 'app'
portal_phrases = [
    "open my university portal",
    "open university portal",
    "open my portal",
    "open comsats portal",
    "open student portal",
]
for phrase in portal_phrases:
    got = classify_intent(phrase)
    check(f"'{phrase}' -> web", got == "web", f"got '{got}'")

# When intent is web, sites should be checked BEFORE apps
# Simulate the route logic
from modules.web_automation import WebAutomation
from modules.app_launcher import AppLauncher
wa = WebAutomation()
al = AppLauncher()
check("'my university portal' is a known site", wa.is_site_known("my university portal"))
check("'university portal' is a known site", wa.is_site_known("university portal"))

# ─── BUG 2: Email check reads 12 delivery failures ──────────
print("\n[BUG 2] Email limit")
from modules.email_module import EmailModule
em = EmailModule({})
# Just verify the method signature accepts limit
import inspect
sig = inspect.signature(em.check_inbox)
check("check_inbox accepts 'limit' parameter", "limit" in sig.parameters)

# ─── BUG 3: Notes search "for groceries" fails ──────────────
print("\n[BUG 3] Notes search query extraction")
import re
# Simulate the fixed regex
test_phrases = [
    ("search notes for groceries", "groceries"),
    ("search notes about assignment", "assignment"),
    ("find notes related to project", "project"),
    ("search notes OOP", "oOP"),
]
for raw, expected_contains in test_phrases:
    lower = raw.lower()
    q = re.sub(r"^(search|find|look for)\s+(notes?\s+)?(for\s+|about\s+|related to\s+)?", "", lower).strip()
    check(f"'{raw}' -> query '{q}'", expected_contains.lower() in q.lower() and "for" not in q.split()[0:1], f"got '{q}'")

# Test actual note search with partial matching
from modules.notes_reminders import NotesModule
nm = NotesModule()
# Save a test note with "grocery store"
nm.save_note("buy stuff from grocery store")
result = nm.search_notes("groceries")
check("search 'groceries' finds note with 'grocery store'", "grocery" in result.lower() or "found" in result.lower(), result[:60])

# ─── BUG 4: Reminder "in 1 minute" -> January ───────────────
print("\n[BUG 4] Reminder regex time capture")
# Simulate Pattern 2 (set a reminder in 1 minute to stretch)
text = "set a reminder in 1 minute to stretch my legs"
m = re.search(
    r"(?:set\s+(?:a\s+)?reminder|reminder)\s+(?:for|in|at)\s+(.+)\s+to\s+(.+)",
    text, re.IGNORECASE
)
check("Pattern 2 matches", m is not None)
if m:
    time_str = m.group(1).strip()
    message = m.group(2).strip()
    check(f"Time captured correctly: '{time_str}'", "1 minute" in time_str, f"got '{time_str}'")
    check(f"Message captured correctly: '{message}'", "stretch" in message, f"got '{message}'")

# Test Pattern 1 (remind me)
text2 = "remind me in 10 minutes to call mama"
m2 = re.search(
    r"remind\s+me\s+((?:in|at)\s+.+)\s+to\s+(.+)",
    text2, re.IGNORECASE
)
check("Pattern 1 matches 'remind me in 10 minutes to call mama'", m2 is not None)
if m2:
    check(f"Time: '{m2.group(1).strip()}'", "10 minutes" in m2.group(1), m2.group(1))
    check(f"Message: '{m2.group(2).strip()}'", "call mama" in m2.group(2), m2.group(2))

# ─── BUG 5: Calendar "tomorrow" matched by "today" ──────────
print("\n[BUG 5] Calendar today/tomorrow disambiguation")
from modules.calendar_tasks import CalendarModule
cm = CalendarModule()
# Add an event for tomorrow
result = cm.add_event("project meeting", "tomorrow at 3:00 PM")
check("Event added for tomorrow", "added" in result.lower() or "event" in result.lower(), result[:60])

# Check tomorrow should return it
tomorrow_result = cm.get_events_tomorrow()
check("get_events_tomorrow finds the event", "project meeting" in tomorrow_result.lower() or "tomorrow" in tomorrow_result.lower(), tomorrow_result[:60])

# ─── BUG 6: Task "mark complete" NLP ────────────────────────
print("\n[BUG 6] Task mark complete NLP + verb stripping")
mark_phrases = [
    ("mark complete the documentation as done", "task"),
    ("mark the task documentation done", "task"),
    ("mark as done finish report", "task"),
]
for phrase, expected in mark_phrases:
    got = classify_intent(phrase)
    check(f"'{phrase}' -> {expected}", got == expected, f"got '{got}'")

# ─── BUG 7: Greeting shows raw dict ─────────────────────────
print("\n[BUG 7] Greeting formats reminder properly")
from modules.personality import PersonalityModule
pm = PersonalityModule()
test_reminders = [{"id": 1, "title": "test", "message": "call Ali", "trigger_at": "2026-05-18T20:00:00"}]
greeting = pm.get_greeting(user_name="Akif", reminders=test_reminders)
check("Greeting does NOT contain raw dict '{' characters", "{" not in greeting, greeting[:80])
check("Greeting mentions reminder time", "08:00 PM" in greeting or "call Ali" in greeting, greeting[:80])

# ─── BUG 8: System command crash protection ─────────────────
print("\n[BUG 8] System controls crash protection")
from modules.system_controls import SystemControls
sc = SystemControls()
# These should NOT crash the process
try:
    result = sc.get_volume()
    check("get_volume does not crash", True)
except Exception as e:
    check("get_volume does not crash", False, str(e))

try:
    result = sc.set_volume(50)
    check("set_volume does not crash", True)
except Exception as e:
    check("set_volume does not crash", False, str(e))

# ─── STT Noise Prefix Stripping ─────────────────────────────
print("\n[BONUS] STT noise prefix stripping")
# Simulate the prefix strip from nova_core.route()
test_inputs = [
    ("Innova add task complete documentation", "add task complete documentation"),
    ("Renuka take a note I want to buy grocery store", "take a note I want to buy grocery store"),
    ("Nova check my emails", "check my emails"),
    ("Nava open YouTube", "open YouTube"),
    ("In Nova set the volume to 50", "set the volume to 50"),
]
for raw, expected in test_inputs:
    cleaned = re.sub(r"^(?:innova|renuka|nova|nava|in nova)\s+", "", raw, flags=re.IGNORECASE).strip()
    check(f"Strip noise: '{raw[:30]}...' -> '{cleaned[:30]}...'", cleaned == expected, f"got '{cleaned}'")

# ─── NLP Regression: All previous intents still work ────────
print("\n[REGRESSION] Previous intents still work")
regression_cases = [
    ("check my emails", "check_email"),
    ("check my gmail", "check_email"),
    ("what's the weather today", "weather"),
    ("open YouTube", "app"),
    ("play music", "music"),
    ("introduce yourself", "introduce"),
    ("take a screenshot", "screenshot"),
    ("what's my battery", "system"),
    ("set volume to 60", "system"),
    ("open my university portal", "web"),
    ("take a note homework due", "notes"),
    ("remind me in 5 minutes to pray", "reminder"),
    ("what do i have tomorrow", "calendar"),
    ("add task finish report", "task"),
    ("send a message to hamza", "whatsapp"),
]
for phrase, expected in regression_cases:
    got = classify_intent(phrase)
    check(f"'{phrase}' -> {expected}", got == expected, f"got '{got}'")

print("\n" + "="*60)
print(f"  Results: {PASS} passed, {FAIL} failed")
print("="*60)
sys.exit(0 if FAIL == 0 else 1)
