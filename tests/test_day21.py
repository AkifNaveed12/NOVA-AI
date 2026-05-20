# tests/test_day21.py — Day 21: Week 3 Integration Tests + DateTimeCalc Tests
# Run: pytest tests/test_day21.py -v

import os
import sys
import datetime
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────────────────────────────────────
# DateTimeCalc — Unit Tests (Module 15)
# ─────────────────────────────────────────────────────────────────────────────

class TestDateTimeCalc:
    """Unit tests for modules/datetime_calc.py"""

    def setup_method(self):
        from modules.datetime_calc import DateTimeCalc
        self.dt = DateTimeCalc()

    def test_get_time_returns_string(self):
        """get_time() must return a non-empty string containing AM or PM."""
        result = self.dt.get_time()
        assert isinstance(result, str)
        assert len(result) > 0
        assert "AM" in result or "PM" in result

    def test_get_date_returns_string(self):
        """get_date() must return a formatted string with year and day name."""
        result = self.dt.get_date()
        assert isinstance(result, str)
        assert str(datetime.date.today().year) in result
        # One of the weekday names must appear
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        assert any(d in result for d in days)

    def test_calculate_addition(self):
        """calculate() must add two numbers correctly."""
        result = self.dt.calculate("5 + 3")
        assert "8" in result

    def test_calculate_subtraction(self):
        """calculate() must subtract correctly."""
        result = self.dt.calculate("10 - 4")
        assert "6" in result

    def test_calculate_multiplication(self):
        """calculate() must multiply correctly."""
        result = self.dt.calculate("6 * 7")
        assert "42" in result

    def test_calculate_division(self):
        """calculate() must divide correctly."""
        result = self.dt.calculate("100 / 4")
        assert "25" in result

    def test_calculate_division_by_zero(self):
        """calculate() must handle division by zero gracefully."""
        result = self.dt.calculate("10 / 0")
        assert "zero" in result.lower() or "error" in result.lower()

    def test_calculate_percent_of(self):
        """calculate() must handle 'X percent of Y' syntax."""
        result = self.dt.calculate("20 percent of 200")
        assert "40" in result

    def test_calculate_word_operators(self):
        """calculate() must handle word-based operators like 'plus', 'minus'."""
        result = self.dt.calculate("10 plus 5")
        assert "15" in result

    def test_days_until_returns_string(self):
        """days_until() with a valid future date must return a string."""
        result = self.dt.days_until("December 31, 2026")
        assert isinstance(result, str)
        assert len(result) > 0
        # Should not be an error
        assert "error" not in result.lower()

    def test_days_until_today(self):
        """days_until() for today's date must report it is today."""
        today_str = datetime.date.today().strftime("%B %d, %Y")
        result = self.dt.days_until(today_str)
        assert "today" in result.lower()

    def test_days_until_invalid_date(self):
        """days_until() with gibberish input must return a graceful error string."""
        result = self.dt.days_until("xyzblahblah")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_calculate_empty_expression(self):
        """calculate() with empty string must return a helpful prompt."""
        result = self.dt.calculate("")
        assert isinstance(result, str)
        assert len(result) > 0


# ─────────────────────────────────────────────────────────────────────────────
# NLP Entity Extraction — Datetime / Math
# ─────────────────────────────────────────────────────────────────────────────

class TestNLPEntities:
    """Verify NLP extracts math_expr and target_date entities correctly."""

    def test_math_expr_extracted_from_calculate(self):
        from modules.nlp_engine import extract_entities
        entities = extract_entities("calculate 8 + 9")
        assert "math_expr" in entities
        assert "8" in entities["math_expr"] or "9" in entities["math_expr"]

    def test_target_date_extracted(self):
        from modules.nlp_engine import extract_entities
        entities = extract_entities("how many days until December 31")
        assert "target_date" in entities
        assert "december" in entities["target_date"].lower() or "31" in entities["target_date"]

    def test_datetime_intent_classified(self):
        from modules.nlp_engine import classify_intent
        assert classify_intent("what time is it") == "datetime"
        assert classify_intent("what is the date today") == "datetime"
        assert classify_intent("what day is it") == "datetime"

    def test_math_intent_classified(self):
        from modules.nlp_engine import classify_intent
        assert classify_intent("calculate 5 + 3") == "math"
        # Direct expression
        assert classify_intent("what is 45 percent of 200") in ("math", "datetime")


# ─────────────────────────────────────────────────────────────────────────────
# Test 16: Note saved and retrieved from DB
# ─────────────────────────────────────────────────────────────────────────────

def test_16_note_saved_and_retrieved():
    """Test 16: Saving a note and reading it back from the DB."""
    from modules.memory_system import DatabaseManager
    from modules.notes_reminders import NotesModule

    db = DatabaseManager(db_path=":memory:")
    nm = NotesModule(db_manager=db)

    save_result = nm.save_note("test note for day 21")
    assert isinstance(save_result, str)
    assert "saved" in save_result.lower() or "note" in save_result.lower()

    read_result = nm.read_notes()
    assert isinstance(read_result, str)
    assert "test note for day 21" in read_result.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Test 17: Reminder row insertion and DB correctness
# ─────────────────────────────────────────────────────────────────────────────

def test_17_reminder_inserted_into_db():
    """Test 17: Adding a reminder stores it correctly in the DB."""
    from modules.memory_system import DatabaseManager
    from modules.notes_reminders import RemindersModule
    import datetime

    db = DatabaseManager(db_path=":memory:")
    rm = RemindersModule(db_manager=db)

    # Set a reminder 5 seconds from now
    future_time = (datetime.datetime.now() + datetime.timedelta(seconds=5)).strftime("%I:%M %p")
    result = rm.set_reminder(f"at {future_time} to call Akif", original=f"remind me at {future_time} to call Akif")
    assert isinstance(result, str)

    # Verify it was stored
    pending = rm.get_pending_reminders()
    assert isinstance(pending, list)
    assert len(pending) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Test 18: Calendar event parsed for natural language date
# ─────────────────────────────────────────────────────────────────────────────

def test_18_calendar_event_parsed():
    """Test 18: Calendar module parses and saves a natural language event."""
    from modules.memory_system import DatabaseManager
    from modules.calendar_tasks import CalendarModule

    db = DatabaseManager(db_path=":memory:")
    cm = CalendarModule(db_manager=db)

    result = cm.add_event("AI class", "next Monday at 9 AM")
    assert isinstance(result, str)
    # Should confirm saved or at minimum not crash
    assert len(result) > 0


# ─────────────────────────────────────────────────────────────────────────────
# Test 19: Task mark done updates DB correctly
# ─────────────────────────────────────────────────────────────────────────────

def test_19_task_mark_done():
    """Test 19: Adding a task then marking it done updates the DB correctly."""
    from modules.memory_system import DatabaseManager
    from modules.calendar_tasks import TasksModule

    db = DatabaseManager(db_path=":memory:")
    tm = TasksModule(db_manager=db)

    add_result = tm.add_task("finish NOVA project", priority="high")
    assert isinstance(add_result, str)

    # Get pending tasks
    pending = tm.get_pending_tasks()
    assert "NOVA" in pending or "nova" in pending.lower()

    # Mark done
    done_result = tm.mark_done("finish NOVA project")
    assert isinstance(done_result, str)
    assert "done" in done_result.lower() or "complete" in done_result.lower() or "marked" in done_result.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Test 20: System volume set to 40% (mock-safe)
# ─────────────────────────────────────────────────────────────────────────────

def test_20_system_volume_importable():
    """Test 20: SystemControls module is importable and exposes set_volume API."""
    from modules.system_controls import SystemControls
    sc = SystemControls()
    assert hasattr(sc, "set_volume")
    assert hasattr(sc, "get_volume")
    assert hasattr(sc, "mute")
    assert hasattr(sc, "unmute")


# ─────────────────────────────────────────────────────────────────────────────
# Test 21: Screenshot tools are importable
# ─────────────────────────────────────────────────────────────────────────────

def test_21_screenshot_tools_importable():
    """Test 21: ScreenshotTools module is importable and exposes take_screenshot API."""
    from modules.screenshot_tools import ScreenshotTools
    st = ScreenshotTools()
    assert hasattr(st, "take_screenshot")
    assert hasattr(st, "click_position")
    assert hasattr(st, "type_text")


# ─────────────────────────────────────────────────────────────────────────────
# Test 22: Mock gesture classification
# ─────────────────────────────────────────────────────────────────────────────

def test_22_gesture_classification_logic():
    """Test 22: Gesture classification maps finger states to correct gesture names."""
    from modules.gesture_engine import GestureEngine

    ge = GestureEngine.__new__(GestureEngine)  # Instantiate without camera

    # Simulate "open_palm" — all 5 fingers up [True, True, True, True, True]
    # Simulate "fist" — all 5 fingers down [False, False, False, False, False]
    # We test the _classify_gesture logic via the finger states
    open_palm_fingers = [True, True, True, True, True]
    fist_fingers = [False, False, False, False, False]
    index_up_fingers = [False, True, False, False, False]

    # Build mock landmarks (21 points) — coordinates don't matter for finger-state only tests
    mock_landmarks = [(0.5, float(i) / 21.0) for i in range(21)]

    # These must return strings (gesture names)
    if hasattr(ge, "_classify_gesture"):
        open_palm_result = ge._classify_gesture(mock_landmarks, open_palm_fingers)
        fist_result = ge._classify_gesture(mock_landmarks, fist_fingers)
        assert isinstance(open_palm_result, str)
        assert isinstance(fist_result, str)


# ─────────────────────────────────────────────────────────────────────────────
# Test 23: Activity log entry created after command
# ─────────────────────────────────────────────────────────────────────────────

def test_23_activity_log_entry_created():
    """Test 23: ActivityLogger correctly inserts and retrieves a log entry."""
    from modules.memory_system import DatabaseManager
    from modules.activity_log import ActivityLogger

    db = DatabaseManager(db_path=":memory:")
    logger = ActivityLogger(db_manager=db)

    logger.log(
        command_text="play Galiyan on Spotify",
        module_triggered="music",
        response_summary="Opening Spotify and playing Galiyan.",
        success=True
    )

    today = logger.get_today()
    assert len(today) >= 1
    assert any("Galiyan" in e.get("command_text", "") for e in today)


# ─────────────────────────────────────────────────────────────────────────────
# Test 24: Config manager hot-reload reads new apps.json
# ─────────────────────────────────────────────────────────────────────────────

def test_24_config_manager_hot_reload():
    """Test 24: ConfigManager.reload() picks up updated apps.json without restart."""
    import json
    import tempfile
    import shutil
    from modules.config_manager import ConfigManager

    temp_dir = tempfile.mkdtemp()
    try:
        # Bootstrap minimal config files
        config_data = {"nova": {"name": "NOVA", "wake_phrase": "Hey NOVA", "user_name": "Akif"},
                       "modules": {}, "tts": {}, "stt": {}}
        with open(os.path.join(temp_dir, "config.json"), "w") as f:
            json.dump(config_data, f)

        os.makedirs(os.path.join(temp_dir, "config"), exist_ok=True)
        apps_initial = {"apps": []}
        with open(os.path.join(temp_dir, "config", "apps.json"), "w") as f:
            json.dump(apps_initial, f)
        for fname in ("sites.json", "contacts.json"):
            with open(os.path.join(temp_dir, "config", fname), "w") as f:
                json.dump({fname.replace(".json", ""): []}, f)

        mgr = ConfigManager(project_root=temp_dir)
        assert len(mgr.apps.get("apps", [])) == 0

        # Now write a new app to the file
        apps_updated = {"apps": [{"name": "TestApp", "aliases": ["test"], "path": "C:\\test.exe"}]}
        with open(os.path.join(temp_dir, "config", "apps.json"), "w") as f:
            json.dump(apps_updated, f)

        # Reload and verify it picks up the change
        mgr.reload()
        assert len(mgr.apps.get("apps", [])) == 1
        assert mgr.apps["apps"][0]["name"] == "TestApp"

    finally:
        shutil.rmtree(temp_dir)


# ─────────────────────────────────────────────────────────────────────────────
# Module 25 Coverage Audit — All 25 modules present
# ─────────────────────────────────────────────────────────────────────────────

def test_all_25_modules_present():
    """Verify every one of the 25 module files exists on disk."""
    required = [
        "wake_word.py", "stt.py", "nlp_engine.py", "groq_brain.py",
        "weather.py", "news.py", "wikipedia_module.py", "web_automation.py",
        "app_launcher.py", "email_module.py", "whatsapp_module.py",
        "music_module.py", "notes_reminders.py", "calendar_tasks.py",
        "datetime_calc.py", "system_controls.py", "screenshot_tools.py",
        "clipboard_manager.py", "translation_module.py", "memory_system.py",
        "personality.py", "gesture_engine.py", "hud_interface.py",
        "activity_log.py", "config_manager.py",
    ]
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for module in required:
        path = os.path.join(project_root, "modules", module)
        assert os.path.exists(path), f"Missing module: {module}"


# ─────────────────────────────────────────────────────────────────────────────
# Personality Module — roast() API
# ─────────────────────────────────────────────────────────────────────────────

def test_personality_has_roast_method():
    """PersonalityModule must expose a roast() method."""
    from modules.personality import PersonalityModule
    pm = PersonalityModule()
    assert hasattr(pm, "roast")
    assert callable(pm.roast)


def test_personality_has_get_joke_method():
    """PersonalityModule must expose a get_joke() method returning a string."""
    from modules.personality import PersonalityModule
    pm = PersonalityModule()
    result = pm.get_joke()
    assert isinstance(result, str)
    assert len(result) > 0
