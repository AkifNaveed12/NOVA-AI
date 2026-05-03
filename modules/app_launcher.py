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

# TODO: implement AppLauncher class with launch(app_name),
#       get_app_list() methods
