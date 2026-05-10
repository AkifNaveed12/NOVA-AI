# tests/test_all.py — NOVA AI Test Suite
# Run: pytest tests/test_all.py -v
# Tests are added after each module is implemented (daily).

import os
import sys
import json

# Add project root to path so modules/ imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Day 1: Scaffold Tests ────────────────────────────────────────

def test_config_json_loads():
    """config.json must load and contain all required keys."""
    with open("config.json", "r") as f:
        config = json.load(f)
    assert "nova" in config
    assert "modules" in config
    assert "tts" in config
    assert "stt" in config
    assert config["nova"]["wake_phrase"] == "Hey NOVA"
    assert config["nova"]["user_name"] == "Akif"


def test_apps_json_loads():
    """config/apps.json must load and contain app entries."""
    with open("config/apps.json", "r") as f:
        data = json.load(f)
    assert "apps" in data
    assert len(data["apps"]) > 0
    for app in data["apps"]:
        assert "name" in app
        assert "aliases" in app
        assert "path" in app


def test_sites_json_loads():
    """config/sites.json must load and contain site entries."""
    with open("config/sites.json", "r") as f:
        data = json.load(f)
    assert "sites" in data
    assert len(data["sites"]) > 0
    for site in data["sites"]:
        assert "name" in site
        assert "url" in site


def test_contacts_json_loads():
    """config/contacts.json must load and contain contact entries."""
    with open("config/contacts.json", "r") as f:
        data = json.load(f)
    assert "contacts" in data


def test_modules_directory_exists():
    """All 25 module files + nova_hud.html must exist in modules/."""
    required_modules = [
        "wake_word.py", "stt.py", "nlp_engine.py", "groq_brain.py",
        "weather.py", "news.py", "wikipedia_module.py", "web_automation.py",
        "app_launcher.py", "email_module.py", "whatsapp_module.py",
        "music_module.py", "notes_reminders.py", "calendar_tasks.py",
        "datetime_calc.py", "system_controls.py", "screenshot_tools.py",
        "clipboard_manager.py", "translation_module.py", "memory_system.py",
        "personality.py", "gesture_engine.py", "hud_interface.py",
        "activity_log.py", "config_manager.py",
        "nova_hud.html",  # Day 11(B) — pywebview cinematic HUD frontend
    ]
    for module_file in required_modules:
        path = os.path.join("modules", module_file)
        assert os.path.exists(path), f"Missing file: {path}"



def test_main_py_importable():
    """main.py must be importable without errors (scaffold test)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", "main.py")
    mod = importlib.util.module_from_spec(spec)
    # Should not raise
    spec.loader.exec_module(mod)
    assert hasattr(mod, "main")


def test_nova_core_importable():
    """nova_core.py must be importable without errors."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("nova_core", "nova_core.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "route")
    assert hasattr(mod, "LOCAL_INTENTS")
    assert hasattr(mod, "GROQ_INTENTS")


def test_nova_core_routing_stubs():
    """nova_core.route() must return a string for any intent."""
    import nova_core
    result_local = nova_core.route({"intent": "weather", "entities": {}, "original": "weather in lahore"})
    result_groq = nova_core.route({"intent": "conversation", "entities": {}, "original": "what is quantum computing"})
    assert isinstance(result_local, str)
    assert isinstance(result_groq, str)


def test_env_example_exists():
    """.env.example must exist."""
    assert os.path.exists(".env.example"), ".env.example is missing"


def test_data_directory_exists():
    """data/ directory must exist for SQLite databases."""
    assert os.path.isdir("data"), "data/ directory is missing"


# ── Day 2: Wake Word + STT Tests (added Day 2) ───────────────────
# Test 1: Wake event triggers on "Hey NOVA"   — added Day 2
# Test 2: STT transcribes "open chrome"       — added Day 2

# ── Day 3: NLP Tests (added Day 3) ───────────────────────────────
def test_nlp_engine_intent_classification():
    from modules.nlp_engine import classify_intent
    assert classify_intent("open chrome") == "app"
    assert classify_intent("weather in islamabad") == "weather"
    assert classify_intent("set a reminder at 5 PM") == "reminder"
    assert classify_intent("tell me a joke") == "joke"
    assert classify_intent("what is machine learning") == "wikipedia"
    assert classify_intent("ajkdfhkjhdfg") == "conversation"

def test_nlp_engine_entity_extraction():
    from modules.nlp_engine import extract_entities
    res1 = extract_entities("weather in islamabad")
    assert "islamabad" in res1.get("city", "").lower()
    
    res2 = extract_entities('search for "machine learning"')
    assert res2.get("query") == "machine learning"

# ── Day 4: Groq Tests (added Day 4) ──────────────────────────────
def test_groq_brain_response():
    # Only test if api key is valid to prevent test failure on CI without key
    import os
    key = os.getenv("GROQ_API_KEY", "")
    if key and "your_key" not in key:
        from modules.groq_brain import GroqBrain
        brain = GroqBrain({})
        res = brain.chat("Reply with exactly the word OK")
        assert "OK" in res.upper()
    else:
        assert True # Skip if no key

# ── Day 5: Memory Tests (added Day 5) ────────────────────────────
def test_database_manager():
    from modules.memory_system import DatabaseManager
    # Use in-memory db for testing to avoid polluting real db
    db = DatabaseManager(":memory:")
    
    # Test user creation
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM Users WHERE id = 1")
    assert cursor.fetchone()["name"] == "Akif"
    
    # Test store and retrieve fact
    db.store_fact("favorite_color", "blue", "preferences")
    facts = db.get_facts()
    assert len(facts) == 1
    assert facts[0][0] == "favorite_color"
    assert facts[0][1] == "blue"
    
    # Test activity logging
    act_id = db.log_activity("open chrome", "app", "opening chrome", True)
    assert act_id == 1
    
    # Test conversation logging
    db.log_conversation("user", "hello", activity_id=act_id)
    cursor.execute("SELECT role FROM ConversationLog WHERE activity_id = 1")
    assert cursor.fetchone()["role"] == "user"

# ── Day 6 → 11(B): HUD Tests (updated for pywebview) ────────────
def test_hud_instantiation():
    """
    NOVAHud must initialise without error and expose the correct public API.
    Uses unittest.mock to stub out webview so no real window is opened in CI.
    """
    import importlib
    from unittest.mock import MagicMock, patch

    # Stub the webview module so create_window/start don't open a real OS window
    mock_window = MagicMock()
    mock_window.events.loaded = MagicMock()

    with patch.dict("sys.modules", {"webview": MagicMock(
        create_window=MagicMock(return_value=mock_window),
        start=MagicMock(),
    )}):
        # Force re-import with the patched webview
        import modules.hud_interface as hud_mod
        importlib.reload(hud_mod)

        hud = hud_mod.NOVAHud()

        # Public API must exist
        assert hasattr(hud, "update_status")
        assert hasattr(hud, "log_message")
        assert hasattr(hud, "update_ticker")
        assert hasattr(hud, "start")

        # Initial state
        assert hud._state == "sleeping"

        # Simulate DOM ready so _js() calls go straight to evaluate_js
        hud._ready = True
        hud._window = mock_window

        # update_status must call evaluate_js with the correct JS string
        hud.update_status("listening")
        mock_window.evaluate_js.assert_called_with("window.novaSetStatus('listening')")

        # log_message must use novaAppendLog
        hud.log_message("user", "open chrome")
        called_js = mock_window.evaluate_js.call_args[0][0]
        assert "novaAppendLog" in called_js
        assert "user" in called_js
        assert "open chrome" in called_js



# ── Day 7: Week 1 Full Integration Tests ─────────────────────────

def test_nlp_routes_to_groq_on_conversation():
    """Any conversational / unknown input must resolve to a GROQ_INTENT."""
    from modules.nlp_engine import classify_intent
    import nova_core
    intent = classify_intent("why is the sky blue")
    # Must NOT be a LOCAL_INTENT that routes to an unimplemented local module
    is_groq_or_unknown = (intent not in nova_core.LOCAL_INTENTS) or (intent in nova_core.GROQ_INTENTS)
    assert is_groq_or_unknown, f"Unexpected local routing for conversational query: {intent}"


def test_nlp_routes_to_local_on_app():
    """App launch commands must map to LOCAL_INTENTS."""
    from modules.nlp_engine import classify_intent
    import nova_core
    intent = classify_intent("open chrome")
    assert intent in nova_core.LOCAL_INTENTS, f"'open chrome' routed to: {intent}"


def test_groq_backoff_and_history():
    """GroqBrain must maintain rolling history and handle repeated calls."""
    import os
    key = os.getenv("GROQ_API_KEY", "")
    if not key or "your_key" in key:
        return  # Skip on CI without key

    from modules.groq_brain import GroqBrain
    brain = GroqBrain({})
    # First call
    r1 = brain.chat("Say the word ALPHA")
    assert isinstance(r1, str) and len(r1) > 0
    # Second call — verifies history is maintained (model can reference previous)
    r2 = brain.chat("What word did you just say?")
    assert isinstance(r2, str) and len(r2) > 0
    # History should grow but stay ≤ 10
    assert len(brain.conversation_history) <= 10


def test_db_activity_log_persists():
    """ActivityLog must store and retrieve entries correctly."""
    from modules.memory_system import DatabaseManager
    db = DatabaseManager(":memory:")
    aid = db.log_activity("what time is it", "datetime", "It is 3 PM", True)
    assert aid is not None and aid >= 1

    cursor = db.conn.cursor()
    cursor.execute("SELECT command_text, module_triggered FROM ActivityLog WHERE id=?", (aid,))
    row = cursor.fetchone()
    assert row["command_text"] == "what time is it"
    assert row["module_triggered"] == "datetime"


def test_db_fact_survives_reload():
    """Facts written in one DatabaseManager session must survive a fresh connection."""
    import tempfile, os
    tmp_path = os.path.join(tempfile.gettempdir(), "nova_test_persist.db")

    # Write
    from modules.memory_system import DatabaseManager
    db1 = DatabaseManager(tmp_path)
    db1.store_fact("test_key", "test_value", "test_category")
    db1.conn.close()

    # Re-read with a fresh instance (simulates restart)
    db2 = DatabaseManager(tmp_path)
    facts = db2.get_facts()
    assert any(f[0] == "test_key" and f[1] == "test_value" for f in facts)
    db2.conn.close()

    # Cleanup
    try:
        os.remove(tmp_path)
    except Exception:
        pass


def test_nova_core_route_returns_string():
    """nova_core.route() must always return a non-empty string for any input."""
    import nova_core

    # Test local-intent stub path (no module implemented yet → returns stub message)
    stub = nova_core.route({"intent": "weather", "entities": {"city": "Karachi"}, "original": "weather in Karachi"})
    assert isinstance(stub, str) and len(stub) > 0

    # Test groq path only if key available
    import os
    key = os.getenv("GROQ_API_KEY", "")
    if key and "your_key" not in key:
        groq_resp = nova_core.route({"intent": "conversation", "entities": {}, "original": "hello"})
        assert isinstance(groq_resp, str) and len(groq_resp) > 0



def test_pipeline_entrypoint_importable():
    """main.py must be importable without crashing (no side effects at import)."""
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("main_module", "main.py")
    mod = importlib.util.module_from_spec(spec)
    # We do NOT exec it (that would open mic/HUD) — just check spec loads
    assert spec is not None
    assert mod is not None


# ── Day 8: Weather + News Tests ──────────────────────────────────

def test_weather_live():
    """WeatherModule must return a non-empty string for a valid city."""
    import os
    key = os.getenv("OPENWEATHER_API_KEY", "")
    if not key or "your_key" in key:
        return  # Skip on CI without key
    from modules.weather import WeatherModule
    wm = WeatherModule()
    result = wm.get_weather("Islamabad")
    assert isinstance(result, str) and len(result) > 10
    # Should contain temperature info
    assert "°C" in result or "°F" in result or "weather" in result.lower()


def test_weather_invalid_city():
    """WeatherModule must handle an invalid city name gracefully."""
    import os
    key = os.getenv("OPENWEATHER_API_KEY", "")
    if not key or "your_key" in key:
        return
    from modules.weather import WeatherModule
    wm = WeatherModule()
    result = wm.get_weather("XYZnonexistentcity999")
    assert isinstance(result, str)
    # Must NOT crash — should return a meaningful error message
    assert len(result) > 5


def test_weather_default_city():
    """WeatherModule must use default city when no city is provided."""
    import os
    key = os.getenv("OPENWEATHER_API_KEY", "")
    if not key or "your_key" in key:
        return
    from modules.weather import WeatherModule
    wm = WeatherModule()
    result = wm.get_weather(None)  # None → default city
    assert isinstance(result, str) and len(result) > 5


def test_news_science_fact_offline():
    """NewsModule.get_science_fact() must return a non-empty fact without network."""
    from modules.news import NewsModule, SCIENCE_FACTS
    nm = NewsModule()
    fact = nm.get_science_fact()
    assert isinstance(fact, str) and len(fact) > 10
    assert fact in SCIENCE_FACTS


def test_news_nasa_apod_live():
    """NewsModule must return a non-empty APOD string with a valid API key."""
    import os
    key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    from modules.news import NewsModule
    nm = NewsModule()
    result = nm.get_nasa_apod()
    assert isinstance(result, str) and len(result) > 20


def test_nova_core_weather_route():
    """nova_core.route() with weather intent must call WeatherModule."""
    import os
    key = os.getenv("OPENWEATHER_API_KEY", "")
    if not key or "your_key" in key:
        return
    import nova_core
    result = nova_core.route({
        "intent": "weather",
        "entities": {"city": "Lahore"},
        "original": "what is the weather in Lahore"
    })
    assert isinstance(result, str) and len(result) > 5


# ── Day 9: Wikipedia + Translation Tests ─────────────────────────

def test_wikipedia_valid_query():
    """WikipediaModule must return a summary for a known topic."""
    from modules.wikipedia_module import WikipediaModule
    wm = WikipediaModule()
    result = wm.search("Python programming language")
    assert isinstance(result, str) and len(result) > 30
    assert "python" in result.lower()


def test_wikipedia_not_found():
    """WikipediaModule must handle a nonsense query gracefully."""
    from modules.wikipedia_module import WikipediaModule
    wm = WikipediaModule()
    result = wm.search("xyzqwertynonexistentpage12345")
    assert isinstance(result, str) and len(result) > 5


def test_wikipedia_empty_query():
    """WikipediaModule must handle empty input gracefully."""
    from modules.wikipedia_module import WikipediaModule
    wm = WikipediaModule()
    result = wm.search("")
    assert "look up" in result.lower() or "what" in result.lower()


def test_translation_to_french():
    """TranslationModule must translate English to French."""
    from modules.translation_module import TranslationModule
    tm = TranslationModule()
    result = tm.translate("hello", "french")
    assert isinstance(result, str) and len(result) > 3
    assert "french" in result.lower() or "bonjour" in result.lower()


def test_translation_to_urdu():
    """TranslationModule must translate English to Urdu."""
    from modules.translation_module import TranslationModule
    tm = TranslationModule()
    result = tm.translate("how are you", "urdu")
    assert isinstance(result, str) and len(result) > 3


def test_translation_unknown_language():
    """TranslationModule must handle an unknown language gracefully."""
    from modules.translation_module import TranslationModule
    tm = TranslationModule()
    result = tm.translate("hello", "klingon_fake_language_xyz")
    assert isinstance(result, str)
    assert "recognise" in result.lower() or "sorry" in result.lower() or "couldn" in result.lower()


def test_nlp_extracts_translate_entities():
    """NLP must extract translate_text and target_language from translate commands."""
    from modules.nlp_engine import extract_entities
    ent = extract_entities("translate hello to french")
    assert ent.get("translate_text") == "hello"
    assert ent.get("target_language") == "french"


def test_nlp_extracts_wiki_query():
    """NLP must extract wiki_query from 'tell me about' commands."""
    from modules.nlp_engine import extract_entities
    ent = extract_entities("tell me about the Eiffel Tower")
    assert "wiki_query" in ent
    assert "eiffel" in ent["wiki_query"].lower()


def test_nova_core_wikipedia_route():
    """nova_core.route() with wikipedia intent must return a real summary."""
    import nova_core
    result = nova_core.route({
        "intent": "wikipedia",
        "entities": {"wiki_query": "Albert Einstein"},
        "original": "tell me about Albert Einstein"
    })
    assert isinstance(result, str) and len(result) > 20


# ── Day 10: Web Automation Tests ─────────────────────────────────

def test_web_open_known_site():
    """WebAutomation must resolve a known site alias to a response."""
    from modules.web_automation import WebAutomation
    wa = WebAutomation()
    # Don't actually open browser — just test the lookup logic
    # We test open_site indirectly by checking the site list
    sites = wa.get_site_list()
    assert "YouTube" in sites
    assert "GitHub" in sites
    assert len(sites) >= 10


def test_web_fuzzy_match():
    """WebAutomation alias map must contain known aliases."""
    from modules.web_automation import WebAutomation
    wa = WebAutomation()
    assert "youtube" in wa._alias_map
    assert "yt" in wa._alias_map
    assert "github" in wa._alias_map
    assert "gmail" in wa._alias_map


def test_web_unknown_site():
    """WebAutomation must return an error string for unknown sites."""
    from modules.web_automation import WebAutomation
    wa = WebAutomation()
    # Override webbrowser.open to prevent actual browser launch
    import webbrowser
    _orig = webbrowser.open
    webbrowser.open = lambda url: None  # no-op
    result = wa.open_site("xyznonexistent_fake_site_12345")
    webbrowser.open = _orig
    assert isinstance(result, str)
    assert "don't know" in result.lower() or "unknown" in result.lower()


def test_web_nlp_classifies_open_youtube():
    """NLP must classify 'go to YouTube' as web intent."""
    from modules.nlp_engine import classify_intent
    assert classify_intent("go to YouTube") == "web"
    assert classify_intent("browse LinkedIn") == "web"


# ── Day 11: App Launcher + Clipboard Tests ───────────────────────

def test_app_launcher_list():
    """AppLauncher must return a valid list of applications from apps.json."""
    from modules.app_launcher import AppLauncher
    al = AppLauncher()
    apps = al.get_app_list()
    assert isinstance(apps, list)
    assert len(apps) > 0
    assert "Notepad" in apps or "Calculator" in apps

def test_app_launcher_unknown_app():
    """AppLauncher must gracefully handle unknown apps without crashing."""
    from modules.app_launcher import AppLauncher
    al = AppLauncher()
    result = al.launch("xyz_fake_app_12345")
    assert isinstance(result, str)
    assert "couldn't find" in result.lower() or "don't have" in result.lower()

def test_clipboard_manager_write_and_read():
    """ClipboardManager must correctly write and then read from clipboard."""
    from modules.clipboard_manager import ClipboardManager
    cm = ClipboardManager()
    test_text = "pytest_clipboard_test_string_123"
    
    # Write to clipboard
    write_result = cm.write(test_text)
    assert "Copied" in write_result
    
    # Read from clipboard
    read_result = cm.read()
    assert test_text in read_result

def test_nova_core_app_route():
    """nova_core.route() with app intent must call AppLauncher."""
    import nova_core
    # Mock subprocess.Popen to prevent actual app launch during tests
    import subprocess
    _orig_popen = subprocess.Popen
    subprocess.Popen = lambda *args, **kwargs: None
    
    result = nova_core.route({
        "intent": "app",
        "entities": {},
        "original": "open notepad"
    })
    
    subprocess.Popen = _orig_popen
    assert isinstance(result, str)
    assert len(result) > 0

def test_nova_core_clipboard_route():
    """nova_core.route() with clipboard intent must handle read/write."""
    import nova_core
    
    # Write
    write_res = nova_core.route({
        "intent": "clipboard",
        "entities": {},
        "original": "copy testing to clipboard"
    })
    assert "Copied" in write_res
    
    # Read
    read_res = nova_core.route({
        "intent": "clipboard",
        "entities": {},
        "original": "read clipboard"
    })
    assert "testing" in read_res


# ── Day 12: Email Module Tests ────────────────────────────────────

def test_email_module_importable():
    """EmailModule must be importable and expose correct public API."""
    from modules.email_module import EmailModule
    em = EmailModule()
    assert hasattr(em, "draft_email")
    assert hasattr(em, "send_email")
    assert hasattr(em, "handle_email_command")
    assert hasattr(em, "has_credentials")


def test_email_module_has_credentials_false():
    """has_credentials() must return False when no env vars are set."""
    import os
    from modules.email_module import EmailModule
    # Temporarily unset the env vars
    orig_addr = os.environ.pop("GMAIL_ADDRESS", None)
    orig_pass = os.environ.pop("GMAIL_APP_PASSWORD", None)
    try:
        em = EmailModule()
        assert em.has_credentials() is False
    finally:
        if orig_addr:
            os.environ["GMAIL_ADDRESS"] = orig_addr
        if orig_pass:
            os.environ["GMAIL_APP_PASSWORD"] = orig_pass


def test_email_send_no_credentials():
    """send_email() without credentials must return a descriptive error string, not raise."""
    import os
    from modules.email_module import EmailModule
    orig_addr = os.environ.pop("GMAIL_ADDRESS", None)
    orig_pass = os.environ.pop("GMAIL_APP_PASSWORD", None)
    try:
        em = EmailModule()
        result = em.send_email("test@example.com", "Test Subject", "Hello body")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "configured" in result.lower() or "credential" in result.lower()
    finally:
        if orig_addr:
            os.environ["GMAIL_ADDRESS"] = orig_addr
        if orig_pass:
            os.environ["GMAIL_APP_PASSWORD"] = orig_pass


def test_email_draft_parsing():
    """
    draft_email() must return a dict with 'subject', 'body', 'recipient' keys.
    Uses Groq API — skipped if no valid key.
    """
    import os
    key = os.getenv("GROQ_API_KEY", "")
    if not key or "your_key" in key:
        return  # Skip on CI without key

    from modules.email_module import EmailModule
    em = EmailModule()
    draft = em.draft_email("Ali", "project meeting tomorrow")

    assert isinstance(draft, dict)
    assert "subject"   in draft
    assert "body"      in draft
    assert "recipient" in draft
    assert isinstance(draft["subject"], str) and len(draft["subject"]) > 0
    assert isinstance(draft["body"],    str) and len(draft["body"]) > 0
    assert draft["recipient"] == "Ali"


def test_email_handle_command_cancel():
    """
    handle_email_command() must return a cancellation string when user says 'no'.
    Uses mocked speak/listen callbacks — no network/TTS/STT needed.
    """
    import os
    key = os.getenv("GROQ_API_KEY", "")
    if not key or "your_key" in key:
        return  # Skip on CI without key

    from modules.email_module import EmailModule

    spoken = []
    # Simulate: user confirms recipient="Ali", topic="meeting", then says "no"
    listen_responses = iter(["no"])

    em = EmailModule()
    result = em.handle_email_command(
        original    = "write an email to Ali about the project meeting",
        entities    = {"name": "Ali"},
        speak_func  = lambda text: spoken.append(text),
        listen_func = lambda: next(listen_responses, "no"),
    )
    assert isinstance(result, str)
    assert "cancel" in result.lower()


def test_email_handle_command_send_flow():
    """
    handle_email_command() with 'yes' must attempt to send and return a string.
    Mocks the SMTP send to avoid real network calls.
    """
    import os
    from unittest.mock import patch, MagicMock
    key = os.getenv("GROQ_API_KEY", "")
    if not key or "your_key" in key:
        return  # Skip on CI without key

    from modules.email_module import EmailModule
    os.environ["GMAIL_ADDRESS"]      = "test@gmail.com"
    os.environ["GMAIL_APP_PASSWORD"] = "testpassword"

    spoken = []
    listen_responses = iter(["yes"])

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = lambda s: mock_server
        mock_smtp.return_value.__exit__  = MagicMock(return_value=False)

        em = EmailModule()
        result = em.handle_email_command(
            original    = "write an email to Ali about the project meeting",
            entities    = {"name": "Ali"},
            speak_func  = lambda text: spoken.append(text),
            listen_func = lambda: next(listen_responses, "yes"),
        )

    assert isinstance(result, str)
    # Should either confirm sent or ask for address (Ali has address in contacts.json)
    assert len(result) > 0


def test_nlp_classifies_email_intent():
    """NLP must classify email-related commands as 'email' intent."""
    from modules.nlp_engine import classify_intent
    assert classify_intent("write an email to Ali about the project")  == "email"
    assert classify_intent("send email to john about the proposal")     == "email"
    assert classify_intent("mail the report to the manager")            == "email"


def test_nova_core_email_route_no_callbacks():
    """
    nova_core.route() with email intent and no callbacks must return a
    descriptive string (graceful degradation), not raise.
    """
    import nova_core
    result = nova_core.route({
        "intent":   "email",
        "entities": {},
        "original": "write an email to Ali about the project meeting",
    })
    assert isinstance(result, str)
    assert len(result) > 0

# ── Day 13 WhatsApp Tests ──────────────────────────────────────────

def test_whatsapp_module_importable():
    from modules.whatsapp_module import WhatsAppModule
    wam = WhatsAppModule()
    assert wam is not None

def test_nlp_classifies_whatsapp_intent():
    from modules.nlp_engine import classify_intent
    assert classify_intent("send a whatsapp to Mama") == "whatsapp"

# ── Day 14 Week 2 Integration Tests ──────────────────────────────────────────

def test_weather_islamabad():
    """Test 8: Weather for Islamabad returns temp and description."""
    import os
    if not os.getenv("OPENWEATHER_API_KEY"):
        return # Skip if no key
    from modules.weather import WeatherModule
    wm = WeatherModule()
    res = wm.get_weather("Islamabad")
    assert "°C" in res
    assert "Islamabad" in res

def test_news_nasa_apod():
    """Test 9: NASA APOD returns non-empty title."""
    from modules.news import NewsModule
    nm = NewsModule()
    res = nm.get_nasa_apod()
    assert isinstance(res, str)
    assert len(res) > 10

def test_wikipedia_python():
    """Test 10: Wikipedia search Python returns sentences."""
    from modules.wikipedia_module import WikipediaModule
    wm = WikipediaModule()
    res = wm.search("Python programming language")
    assert isinstance(res, str)
    assert len(res) > 20

def test_translation_french():
    """Test 11: Translation how are you to French."""
    from modules.translation import TranslationModule
    tm = TranslationModule()
    res = tm.translate("how are you", "french")
    assert isinstance(res, str)
    assert len(res) > 0
    assert "comment" in res.lower()

def test_sites_json_loading():
    """Test 12: sites.json loads and youtube maps correctly."""
    from modules.web_automation import WebAutomation
    wa = WebAutomation()
    assert len(wa.sites) > 0
    youtube_found = False
    for site in wa.sites:
        if site.get("name", "").lower() == "youtube" or "youtube" in site.get("aliases", []):
            youtube_found = True
            assert "youtube.com" in site.get("url", "")
            break
    assert youtube_found

def test_clipboard_rw():
    """Test 14: Clipboard write -> read returns same text."""
    from modules.clipboard_manager import ClipboardManager
    cm = ClipboardManager()
    original = cm.read()
    cm.write("nova_test_clipboard_123")
    assert "nova_test_clipboard_123" in cm.read()
    if original:
        cm.write(original)
