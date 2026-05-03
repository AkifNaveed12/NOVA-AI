"""
MODULE 13 — Notes & Reminders
===============================
Saves voice notes to SQLite and fires timed reminder alerts via TTS.
Reminder engine runs as a background daemon thread that polls the
reminders table every 30 seconds for due alerts.

Tech: sqlite3, dateparser, threading
Storage: data/memory.db — notes and reminders tables
Output: Saved note / reminder confirmation → TTS engine
        Reminder alerts fired automatically at trigger time
"""

# TODO: implement NotesModule, RemindersModule, ReminderEngine classes
