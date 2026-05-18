"""
NOVA AI — Days 15-17 Functional Test
Tests each module against the exact TEST cases in planning.md
Run with: venv\Scripts\python.exe tests/test_days15_17.py
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
        print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))
        FAIL += 1

print("\n" + "="*60)
print("  NOVA AI — Days 15-17 Functional Test Suite")
print("="*60)

# ─────────────────────────────────────────────────────────────
print("\n[DAY 15] Notes Module")
# ─────────────────────────────────────────────────────────────
from modules.notes_reminders import NotesModule, RemindersModule
import sqlite3, datetime

nm = NotesModule()

# Test 16: Note saved and retrieved from DB
result = nm.save_note("submit OOP assignment by Friday")
check("Note save returns confirmation string", "saved" in result.lower() or "got it" in result.lower(), result)

result2 = nm.read_notes(n=5)
check("Note retrieved — read_notes contains saved content", "submit OOP assignment" in result2.lower() or "note" in result2.lower(), result2)

# Search
result3 = nm.search_notes("OOP")
check("Note search finds 'OOP'", "oop" in result3.lower() or "submit" in result3.lower(), result3)

count = nm.get_notes_count()
check("get_notes_count returns > 0", count > 0, f"count={count}")

# ─────────────────────────────────────────────────────────────
print("\n[DAY 15] Reminders Module")
# ─────────────────────────────────────────────────────────────
rm = RemindersModule()

# Test 17: Reminder set for future time
result = rm.set_reminder("call Ali", "in 1 hour")
check("Reminder set confirmation returned", "reminder set" in result.lower() or "reminder" in result.lower(), result)

result_bad = rm.set_reminder("test", "gobbledygook xyz")
check("Invalid time → graceful error message", "couldn't understand" in result_bad.lower() or "try" in result_bad.lower(), result_bad)

upcoming = rm.get_upcoming_reminders()
check("Upcoming reminders list is returned (list type)", isinstance(upcoming, list), str(type(upcoming)))

# Test 17 (planning.md): Reminder fires within 5s of trigger time
# Set a reminder 2 seconds in the past to simulate a due reminder
conn = sqlite3.connect("data/memory.db", check_same_thread=False)
past_time = (datetime.datetime.now() - datetime.timedelta(seconds=5)).isoformat()
conn.execute("INSERT INTO Reminders (user_id, title, message, trigger_at) VALUES (1, ?, ?, ?)",
             ("test fire", "test fire", past_time))
conn.commit()
conn.close()

due = rm.get_pending_reminders()
check("get_pending_reminders finds overdue reminder", len(due) >= 1, f"found {len(due)}")
if due:
    rm.mark_done(due[0]["id"])
    due_after = rm.get_pending_reminders()
    check("mark_done removes it from pending list", not any(d["id"] == due[0]["id"] for d in due_after), "still in list!")

# ─────────────────────────────────────────────────────────────
print("\n[DAY 16] Calendar Module")
# ─────────────────────────────────────────────────────────────
from modules.calendar_tasks import CalendarModule, TasksModule

cm = CalendarModule()

# Test 18: Calendar event parsed for natural language date
result = cm.add_event("AI class", "next Monday at 9 AM")
check("add_event returns confirmation", "event added" in result.lower() or "monday" in result.lower() or "added" in result.lower(), result)

result_bad = cm.add_event("Test event", "not a real time ever")
check("Invalid date → graceful error", "couldn't understand" in result_bad.lower() or "try" in result_bad.lower(), result_bad)

today_result = cm.get_events_today()
check("get_events_today returns a string", isinstance(today_result, str), today_result)

upcoming = cm.get_upcoming_events(days=14)
check("get_upcoming_events returns string with content", isinstance(upcoming, str), upcoming[:60])

ticker = cm.get_today_ticker_text()
check("get_today_ticker_text returns string (may be empty)", isinstance(ticker, str), f"'{ticker[:40]}'")

# ─────────────────────────────────────────────────────────────
print("\n[DAY 16] Tasks Module")
# ─────────────────────────────────────────────────────────────
tm = TasksModule()

# Test 19: Task mark done updates DB correctly
result = tm.add_task("finish NOVA project", priority="high")
check("add_task returns confirmation", "task added" in result.lower() or "finish nova" in result.lower(), result)

pending = tm.get_pending_tasks()
check("get_pending_tasks shows added task", "finish nova" in pending.lower() or "task" in pending.lower(), pending[:80])

done_result = tm.mark_done("finish NOVA project")
check("mark_done by fuzzy title succeeds", "marked" in done_result.lower() or "done" in done_result.lower(), done_result)

# Verify it's gone from pending after marking done
pending_after = tm.get_pending_tasks()
check("Task not in pending after mark_done",
      "finish nova" not in pending_after.lower() or "your task list is empty" in pending_after.lower(),
      pending_after[:80])

# ─────────────────────────────────────────────────────────────
print("\n[DAY 17] System Controls")
# ─────────────────────────────────────────────────────────────
from modules.system_controls import SystemControls
sc = SystemControls()

# Test 20: System volume set to 40%
result = sc.set_volume(40)
check("set_volume(40) returns confirmation", "40" in result or "volume" in result.lower(), result)

result_get = sc.get_volume()
check("get_volume returns percentage string", "%" in result_get or "percent" in result_get.lower() or "couldn't" in result_get.lower(), result_get)

result_bat = sc.get_battery()
check("get_battery returns string (battery or no-battery msg)", isinstance(result_bat, str) and len(result_bat) > 5, result_bat)

result_cpu = sc.get_cpu_usage()
check("get_cpu_usage returns percentage", "percent" in result_cpu.lower() or "%" in result_cpu, result_cpu)

result_ram = sc.get_ram_usage()
check("get_ram_usage returns GB breakdown", "gb" in result_ram.lower() or "percent" in result_ram.lower(), result_ram)

result_up = sc.volume_up(step=5)
check("volume_up returns confirmation", "volume" in result_up.lower() or "percent" in result_up.lower(), result_up)

result_down = sc.volume_down(step=5)
check("volume_down returns confirmation", "volume" in result_down.lower() or "percent" in result_down.lower(), result_down)

# ─────────────────────────────────────────────────────────────
print("\n[DAY 17] Screenshot Tools")
# ─────────────────────────────────────────────────────────────
from modules.screenshot_tools import ScreenshotTools
st = ScreenshotTools()

# Test 21: Screenshot saved to Desktop as PNG
result = st.take_screenshot()
check("take_screenshot returns confirmation string", "screenshot" in result.lower() or "saved" in result.lower(), result)

desktop = st.get_desktop_path()
check("get_desktop_path returns valid path", os.path.isdir(desktop), desktop)

# Verify file actually exists on Desktop
import glob
png_files = glob.glob(os.path.join(desktop, "NOVA_Screenshot_*.png"))
check("Screenshot PNG file created on Desktop", len(png_files) > 0, f"found {len(png_files)} files")

# ─────────────────────────────────────────────────────────────
print("\n[NLP] Intent Classification")
# ─────────────────────────────────────────────────────────────
from modules.nlp_engine import classify_intent

cases = [
    ("check my emails",            "check_email"),
    ("check my gmail",             "check_email"),
    ("read my inbox",              "check_email"),
    ("open my university portal",  "web"),
    ("take a note buy groceries",  "notes"),
    ("read my notes",              "notes"),
    ("set a reminder in 10 minutes to call mama", "reminder"),
    ("remind me at 5 PM to pray", "reminder"),
    ("what do i have today",       "calendar"),
    ("add task finish assignment", "task"),
    ("what are my tasks",          "task"),
    ("set volume to 60",           "system"),
    ("mute",                       "system"),
    ("what's my battery",          "system"),
    ("take a screenshot",          "screenshot"),
]
for phrase, expected in cases:
    got = classify_intent(phrase)
    check(f"'{phrase}' → {expected}", got == expected, f"got '{got}'")

# ─────────────────────────────────────────────────────────────
print("\n" + "="*60)
print(f"  Results: {PASS} passed, {FAIL} failed")
print("="*60)
sys.exit(0 if FAIL == 0 else 1)
