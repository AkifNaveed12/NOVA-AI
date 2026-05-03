"""
MODULE 25 — Plugin / Config Manager
======================================
Central control panel for NOVA's behavior. Loads and provides
hot-reload of config.json, apps.json, sites.json, contacts.json.
All module settings come from this manager — no direct JSON reads.
Voice command "reload config" re-reads all files live without restart.

Tech: json (built-in), threading (for file-watch)
Storage: config.json, config/apps.json, config/sites.json,
         config/contacts.json
"""

# TODO: implement ConfigManager class with get(), set(), reload(),
#       is_module_enabled(), add_app(), add_site(), add_contact()
