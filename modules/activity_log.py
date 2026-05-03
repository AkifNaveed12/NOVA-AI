"""
MODULE 24 — Activity Log & History
=====================================
Every command NOVA processes is logged to SQLite with timestamp,
command text, response summary, module triggered, and success status.
Auto-cleanup removes entries older than 30 days on startup.
Voice queryable: "What did I ask you earlier?" / "Show today's log".

Tech: sqlite3 (built-in)
Storage: data/memory.db — ActivityLog table
Output: Logged entry / recent history string -> TTS engine
"""

# TODO: implement ActivityLogger class with log(), get_today(),
#       get_recent(), cleanup_old() methods
