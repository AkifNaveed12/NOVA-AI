"""
MODULE 13 — Notes & Reminders
==============================
Saves voice notes to SQLite and fires timed reminder alerts.
Reminder engine runs as a background daemon thread polling every 30s.

Tech: sqlite3, dateparser, threading
Storage: data/memory.db — Notes and Reminders tables
Output: Confirmation strings → TTS engine via announcement_queue
"""

import sqlite3
import datetime
import threading
import os
from typing import Optional


class NotesModule:
    """Handles voice note creation, reading, searching, and deletion."""

    def __init__(self, db_path: str = "data/memory.db", user_id: int = 1):
        self.db_path = db_path
        self.user_id = user_id

    def _conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def save_note(self, content: str, tags: str = "") -> str:
        """Saves a new note to the Notes table."""
        if not content or not content.strip():
            return "What would you like me to note down?"
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO Notes (user_id, content, tags) VALUES (?, ?, ?)",
                (self.user_id, content.strip(), tags)
            )
            conn.commit()
        print(f"[Notes] Saved: {content[:60]}")
        return f"Got it. I've saved your note: {content[:80]}."

    def read_notes(self, n: int = 5) -> str:
        """Returns the last n notes as a spoken list."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, content, created_at FROM Notes WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (self.user_id, n)
            ).fetchall()
        if not rows:
            return "You have no saved notes yet."
        parts = [f"Note {i+1}: {row['content']}" for i, row in enumerate(rows)]
        return f"Here are your last {len(parts)} notes. " + ". ".join(parts) + "."

    def search_notes(self, query: str) -> str:
        """Searches notes for a keyword."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT content FROM Notes WHERE user_id = ? AND content LIKE ? ORDER BY created_at DESC LIMIT 5",
                (self.user_id, f"%{query}%")
            ).fetchall()
        if not rows:
            return f"I couldn't find any notes containing '{query}'."
        parts = [row["content"] for row in rows]
        return f"Found {len(parts)} notes matching '{query}': " + ". ".join(parts) + "."

    def delete_note(self, note_id: int) -> str:
        """Deletes a note by its ID."""
        with self._conn() as conn:
            conn.execute("DELETE FROM Notes WHERE id = ? AND user_id = ?", (note_id, self.user_id))
            conn.commit()
        return f"Note {note_id} deleted."

    def get_notes_count(self) -> int:
        """Returns total number of saved notes."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM Notes WHERE user_id = ?", (self.user_id,)
            ).fetchone()
        return row["cnt"] if row else 0


class RemindersModule:
    """Handles setting, querying, and managing voice-triggered reminders."""

    def __init__(self, db_path: str = "data/memory.db", user_id: int = 1):
        self.db_path = db_path
        self.user_id = user_id

    def _conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def set_reminder(self, message: str, trigger_time_str: str) -> str:
        """
        Parses trigger_time_str with dateparser and saves reminder.
        Returns a confirmation string for TTS.
        """
        try:
            import dateparser
        except ImportError:
            return "The dateparser library is required. Please run: pip install dateparser"

        if not message or not trigger_time_str:
            return "Please tell me both the message and when to remind you."

        trigger_dt = dateparser.parse(
            trigger_time_str,
            settings={"PREFER_DATES_FROM": "future", "RETURN_AS_TIMEZONE_AWARE": False}
        )
        if not trigger_dt:
            return f"I couldn't understand the time '{trigger_time_str}'. Try saying something like 'in 10 minutes' or 'at 5 PM'."

        with self._conn() as conn:
            conn.execute(
                "INSERT INTO Reminders (user_id, title, message, trigger_at) VALUES (?, ?, ?, ?)",
                (self.user_id, message, message, trigger_dt.isoformat())
            )
            conn.commit()

        formatted_time = trigger_dt.strftime("%I:%M %p")
        print(f"[Reminders] Set: '{message}' at {trigger_dt.isoformat()}")
        return f"Reminder set for {formatted_time} — {message}."

    def get_pending_reminders(self) -> list:
        """Returns all reminders that are due (trigger_at <= now) and not done."""
        now = datetime.datetime.now().isoformat()
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM Reminders WHERE user_id = ? AND is_done = 0 AND trigger_at <= ?",
                (self.user_id, now)
            ).fetchall()
        return [dict(row) for row in rows]

    def get_upcoming_reminders(self) -> list:
        """Returns all future pending reminders for display."""
        now = datetime.datetime.now().isoformat()
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM Reminders WHERE user_id = ? AND is_done = 0 AND trigger_at > ? ORDER BY trigger_at ASC LIMIT 5",
                (self.user_id, now)
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_done(self, reminder_id: int):
        """Marks a reminder as fired/done so it doesn't repeat."""
        with self._conn() as conn:
            conn.execute(
                "UPDATE Reminders SET is_done = 1 WHERE id = ?", (reminder_id,)
            )
            conn.commit()


class ReminderEngine:
    """
    Background daemon thread that polls every 30 seconds for due reminders.
    Puts alert strings into the announcement_queue (drained by main.py).
    Never calls HUD or TTS directly — always goes through the queue.
    """

    def __init__(self, reminders_module: RemindersModule, announcement_queue, hud_ticker_queue=None):
        self._module = reminders_module
        self._queue = announcement_queue
        self._ticker_queue = hud_ticker_queue
        self._stop_event = threading.Event()

    def _check_loop(self):
        while not self._stop_event.is_set():
            try:
                due = self._module.get_pending_reminders()
                for reminder in due:
                    msg = reminder.get("message") or reminder.get("title", "Reminder")
                    alert_text = f"Reminder alert: {msg}"
                    self._queue.put(alert_text)
                    if self._ticker_queue:
                        self._ticker_queue.put(f"⏰ {datetime.datetime.now().strftime('%I:%M %p')} — {msg}")
                    self._module.mark_done(reminder["id"])
                    print(f"[ReminderEngine] Fired: {msg}")
            except Exception as e:
                print(f"[ReminderEngine] Error: {e}")
            self._stop_event.wait(timeout=30)

    def start(self):
        t = threading.Thread(target=self._check_loop, daemon=True, name="ReminderEngineThread")
        t.start()
        print("[ReminderEngine] Started — polling every 30s.")

    def stop(self):
        self._stop_event.set()
