"""
MODULE 25 — Central Config Manager
======================================
Central control panel for NOVA's behavior. Loads and provides
hot-reload of config.json, apps.json, sites.json, contacts.json.
All module settings come from this manager — no direct JSON reads.
Voice command "reload config" re-reads all files live without restart.

Tech: json (built-in), threading (for locks)
Storage: config.json, config/apps.json, config/sites.json,
         config/contacts.json
"""

import os
import json
import threading

class ConfigManager:
    def __init__(self, project_root=None):
        if project_root is None:
            # Assumes config_manager.py is in modules/, so project root is one level up
            self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.project_root = os.path.abspath(project_root)
            
        self.config_path = os.path.join(self.project_root, "config.json")
        self.apps_path = os.path.join(self.project_root, "config", "apps.json")
        self.sites_path = os.path.join(self.project_root, "config", "sites.json")
        self.contacts_path = os.path.join(self.project_root, "config", "contacts.json")
        
        self._lock = threading.Lock()
        self.reload()

    def reload(self):
        """Thread-safe loading of all configuration files from disk."""
        with self._lock:
            # 1. Load config.json
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"[ConfigManager] Error loading config.json: {e}")
                self.config = {}

            # 2. Load apps.json
            try:
                with open(self.apps_path, "r", encoding="utf-8") as f:
                    self.apps = json.load(f)
            except Exception as e:
                print(f"[ConfigManager] Error loading apps.json: {e}")
                self.apps = {"apps": []}

            # 3. Load sites.json
            try:
                with open(self.sites_path, "r", encoding="utf-8") as f:
                    self.sites = json.load(f)
            except Exception as e:
                print(f"[ConfigManager] Error loading sites.json: {e}")
                self.sites = {"sites": []}

            # 4. Load contacts.json
            try:
                with open(self.contacts_path, "r", encoding="utf-8") as f:
                    self.contacts = json.load(f)
            except Exception as e:
                print(f"[ConfigManager] Error loading contacts.json: {e}")
                self.contacts = {"contacts": []}

    def get(self, dot_path, default=None):
        """Gets a configuration setting using a dot-separated path (e.g. 'tts.rate')."""
        with self._lock:
            parts = dot_path.split(".")
            val = self.config
            for part in parts:
                if isinstance(val, dict) and part in val:
                    val = val[part]
                else:
                    return default
            return val

    def set(self, dot_path, value):
        """Sets a configuration setting in memory and saves the main config to disk."""
        with self._lock:
            parts = dot_path.split(".")
            val = self.config
            for part in parts[:-1]:
                if part not in val or not isinstance(val[part], dict):
                    val[part] = {}
                val = val[part]
            val[parts[-1]] = value
            self._save_config()

    def is_module_enabled(self, name):
        """Checks if a specific module is enabled in configuration."""
        return bool(self.get(f"modules.{name}", False))

    def _save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"[ConfigManager] Error saving config.json: {e}")

    def add_app(self, name, path, aliases=None):
        """Adds or updates an application entry in apps.json."""
        if aliases is None:
            aliases = [name.lower()]
        with self._lock:
            apps_list = self.apps.setdefault("apps", [])
            # Filter out duplicates
            apps_list = [a for a in apps_list if a.get("name", "").lower() != name.lower()]
            apps_list.append({
                "name": name,
                "aliases": aliases,
                "path": path
            })
            self.apps["apps"] = apps_list
            self._save_apps()

    def _save_apps(self):
        try:
            with open(self.apps_path, "w", encoding="utf-8") as f:
                json.dump(self.apps, f, indent=2)
        except Exception as e:
            print(f"[ConfigManager] Error saving apps.json: {e}")

    def add_site(self, name, url, aliases=None):
        """Adds or updates a website entry in sites.json."""
        if aliases is None:
            aliases = [name.lower()]
        with self._lock:
            sites_list = self.sites.setdefault("sites", [])
            # Filter out duplicates
            sites_list = [s for s in sites_list if s.get("name", "").lower() != name.lower()]
            sites_list.append({
                "name": name,
                "aliases": aliases,
                "url": url
            })
            self.sites["sites"] = sites_list
            self._save_sites()

    def _save_sites(self):
        try:
            with open(self.sites_path, "w", encoding="utf-8") as f:
                json.dump(self.sites, f, indent=2)
        except Exception as e:
            print(f"[ConfigManager] Error saving sites.json: {e}")

    def add_contact(self, name, phone=None, email=None, platform="whatsapp", aliases=None):
        """Adds or updates a contact entry in contacts.json."""
        if aliases is None:
            aliases = [name.lower()]
        with self._lock:
            contacts_list = self.contacts.setdefault("contacts", [])
            # Filter out duplicates
            contacts_list = [c for c in contacts_list if c.get("name", "").lower() != name.lower()]
            contacts_list.append({
                "name": name,
                "aliases": aliases,
                "phone": phone,
                "email": email,
                "platform": platform
            })
            self.contacts["contacts"] = contacts_list
            self._save_contacts()

    def _save_contacts(self):
        try:
            with open(self.contacts_path, "w", encoding="utf-8") as f:
                json.dump(self.contacts, f, indent=2)
        except Exception as e:
            print(f"[ConfigManager] Error saving contacts.json: {e}")

# Global singleton instance for import across all modules
config_manager = ConfigManager()

class ConfigProxy(dict):
    def __init__(self, manager):
        self._manager = manager
    def __getitem__(self, key):
        return self._manager.config[key]
    def __setitem__(self, key, value):
        self._manager.config[key] = value
    def __contains__(self, key):
        return key in self._manager.config
    def get(self, key, default=None):
        return self._manager.get(key, default)
    def __len__(self):
        return len(self._manager.config)
    def __iter__(self):
        return iter(self._manager.config)
    def keys(self):
        return self._manager.config.keys()
    def values(self):
        return self._manager.config.values()
    def items(self):
        return self._manager.config.items()

config_proxy = ConfigProxy(config_manager)
