"""
MODULE 9 — Application Launcher
==================================
Opens any installed Windows application by voice using fuzzy name
matching against the app registry in config/apps.json.
Uses subprocess.Popen for non-blocking app launch.

Tech: subprocess, os, rapidfuzz, apps.json
Config: apps.json (name → executable path mappings)
Output: Confirmation string → TTS engine
"""

import os
import json
import subprocess
from rapidfuzz import process, fuzz


class AppLauncher:
    def __init__(self, config: dict = None):
        # Load apps registry
        apps_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "apps.json")
        try:
            with open(apps_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.apps = data.get("apps", [])
        except Exception as e:
            print(f"[AppLauncher] Error loading apps.json: {e}")
            self.apps = []

        # Build a flat lookup: alias -> {name, path}
        self._alias_map = {}
        for app in self.apps:
            name = app["name"]
            path = app["path"]
            self._alias_map[name.lower()] = {"name": name, "path": path}
            for alias in app.get("aliases", []):
                self._alias_map[alias.lower()] = {"name": name, "path": path}

    def launch(self, app_name: str) -> str:
        """
        Launches an application by fuzzy matching its name.
        """
        if not app_name or not app_name.strip():
            return "Which application would you like me to open?"

        query = app_name.lower().strip()

        # Direct match first
        if query in self._alias_map:
            entry = self._alias_map[query]
        else:
            # Fuzzy match against all aliases
            all_aliases = list(self._alias_map.keys())
            if not all_aliases:
                return "I don't have any apps configured yet."
                
            match = process.extractOne(query, all_aliases, scorer=fuzz.WRatio, score_cutoff=65)
            if match:
                matched_alias, score, _ = match
                entry = self._alias_map[matched_alias]
            else:
                return f"I couldn't find an app called '{app_name}'. You can add it to apps.json."

        try:
            # Expand environment variables like %APPDATA%
            expanded_path = os.path.expandvars(entry["path"])
            
            # Non-blocking launch
            subprocess.Popen([expanded_path], shell=False)
            return f"Opening {entry['name']}."
        except Exception as e:
            print(f"[AppLauncher] Error launching {entry['name']} at {expanded_path}: {e}")
            return f"I tried to open {entry['name']}, but encountered an error."

    def is_app_known(self, app_name: str) -> bool:
        """Helper to check if an app name matches known apps above the threshold."""
        if not app_name or not app_name.strip():
            return False
        query = app_name.lower().strip()
        if query in self._alias_map:
            return True
        all_aliases = list(self._alias_map.keys())
        if not all_aliases:
            return False
        match = process.extractOne(query, all_aliases, scorer=fuzz.WRatio, score_cutoff=65)
        return bool(match)

    def get_app_list(self) -> list:
        """Returns a list of all configured application names."""
        return [app["name"] for app in self.apps]
