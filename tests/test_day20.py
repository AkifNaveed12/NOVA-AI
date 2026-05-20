# tests/test_day20.py — Tests for Config Manager & Activity Logger
import os
import json
import tempfile
import shutil
import pytest
import datetime
from modules.config_manager import ConfigManager, ConfigProxy
from modules.activity_log import ActivityLogger
from modules.memory_system import DatabaseManager
from modules.nlp_engine import classify_intent, extract_entities

@pytest.fixture
def temp_project_dir():
    # Set up temporary project structure with configuration files
    temp_dir = tempfile.mkdtemp()
    
    config_data = {
        "nova": {
            "name": "NOVA",
            "wake_phrase": "Hey NOVA",
            "user_name": "Akif"
        },
        "modules": {
            "weather": True,
            "config_manager": True
        },
        "tts": {
            "rate": 175
        }
    }
    apps_data = {"apps": []}
    sites_data = {"sites": []}
    contacts_data = {"contacts": []}
    
    with open(os.path.join(temp_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config_data, f)
        
    os.makedirs(os.path.join(temp_dir, "config"))
    
    with open(os.path.join(temp_dir, "config", "apps.json"), "w", encoding="utf-8") as f:
        json.dump(apps_data, f)
    with open(os.path.join(temp_dir, "config", "sites.json"), "w", encoding="utf-8") as f:
        json.dump(sites_data, f)
    with open(os.path.join(temp_dir, "config", "contacts.json"), "w", encoding="utf-8") as f:
        json.dump(contacts_data, f)
        
    yield temp_dir
    
    shutil.rmtree(temp_dir)


def test_config_manager_load_and_get(temp_project_dir):
    mgr = ConfigManager(project_root=temp_project_dir)
    assert mgr.get("nova.name") == "NOVA"
    assert mgr.get("tts.rate") == 175
    assert mgr.is_module_enabled("weather") is True
    assert mgr.is_module_enabled("nonexistent") is False


def test_config_manager_set_and_reload(temp_project_dir):
    mgr = ConfigManager(project_root=temp_project_dir)
    mgr.set("tts.rate", 200)
    assert mgr.get("tts.rate") == 200
    
    # Verify file is written
    with open(os.path.join(temp_project_dir, "config.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["tts"]["rate"] == 200

    # Test reload
    mgr.reload()
    assert mgr.get("tts.rate") == 200


def test_config_manager_add_app_site_contact(temp_project_dir):
    mgr = ConfigManager(project_root=temp_project_dir)
    
    # Add app
    mgr.add_app("TestApp", "C:\\test.exe", ["test"])
    assert len(mgr.apps["apps"]) == 1
    assert mgr.apps["apps"][0]["name"] == "TestApp"
    
    # Add duplicate app (should overwrite/update)
    mgr.add_app("TestApp", "C:\\test_new.exe", ["test"])
    assert len(mgr.apps["apps"]) == 1
    assert mgr.apps["apps"][0]["path"] == "C:\\test_new.exe"
    
    # Add site
    mgr.add_site("TestSite", "https://test.com", ["testsite"])
    assert len(mgr.sites["sites"]) == 1
    assert mgr.sites["sites"][0]["url"] == "https://test.com"
    
    # Add contact
    mgr.add_contact("TestContact", "+123456", "test@test.com", "whatsapp")
    assert len(mgr.contacts["contacts"]) == 1
    assert mgr.contacts["contacts"][0]["phone"] == "+123456"


def test_config_proxy(temp_project_dir):
    mgr = ConfigManager(project_root=temp_project_dir)
    proxy = ConfigProxy(mgr)
    
    assert proxy.get("nova.name") == "NOVA"
    assert proxy["nova"]["name"] == "NOVA"
    
    # Modify via set
    mgr.set("nova.name", "SUPER_NOVA")
    # Proxy should immediately reflect the change
    assert proxy.get("nova.name") == "SUPER_NOVA"
    assert proxy["nova"]["name"] == "SUPER_NOVA"


def test_activity_logger():
    # Use in-memory SQLite for testing DatabaseManager
    # DatabaseManager connects to memory.db by default or we can mock/override it
    db = DatabaseManager(db_path=":memory:")
    logger = ActivityLogger(db_manager=db)
    
    # Log some commands
    logger.log("test command 1", "test_intent", "response 1", success=True)
    logger.log("test command 2", "test_intent", "response 2", success=False)
    
    # Retrieve
    today = logger.get_today()
    assert len(today) == 2
    assert today[0]["command_text"] == "test_command 2" or today[0]["command_text"] == "test command 2"
    
    recent = logger.get_recent(n=1)
    assert len(recent) == 1
    assert recent[0]["response_summary"] == "response 2"


def test_nlp_routing_config_and_activity():
    # Test intent classification
    assert classify_intent("reload config") == "config_manager"
    assert classify_intent("refresh settings") == "config_manager"
    assert classify_intent("what did i ask you earlier") == "activity_log"
    assert classify_intent("show today's log") == "activity_log"
