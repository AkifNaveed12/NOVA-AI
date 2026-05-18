"""
MODULE 14 — Calendar & Task Scheduling
========================================
Voice-driven calendar event management and to-do task list.
Parses natural language dates/times using dateparser.
Upcoming events displayed in the HUD reminders ticker on startup.

Tech: sqlite3, dateparser, rapidfuzz
Storage: data/memory.db — Events and Tasks tables
Output: Event/task confirmation or query results → TTS engine
"""

import sqlite3
import datetime
from typing import Optional


class CalendarModule:
    """Manages voice-driven calendar events stored in SQLite."""

    def __init__(self, db_path: str = "data/memory.db", user_id: int = 1):
        self.db_path = db_path
        self.user_id = user_id

    def _conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def add_event(self, title: str, event_dt_str: str, location: str = "", notes: str = "") -> str:
        """Parses natural language date/time and saves event to Events table."""
        if not title or not event_dt_str:
            return "Please tell me both the event title and when it is."

        try:
            import dateparser
        except ImportError:
            return "The dateparser library is required. Please run: pip install dateparser"

        event_dt = dateparser.parse(
            event_dt_str,
            settings={"PREFER_DATES_FROM": "future", "RETURN_AS_TIMEZONE_AWARE": False}
        )
        if not event_dt:
            return f"I couldn't understand '{event_dt_str}' as a date or time. Try something like 'Monday at 9 AM'."

        with self._conn() as conn:
            conn.execute(
                "INSERT INTO Events (user_id, title, event_dt, location, notes) VALUES (?, ?, ?, ?, ?)",
                (self.user_id, title, event_dt.isoformat(), location, notes)
            )
            conn.commit()

        formatted = event_dt.strftime("%A, %B %d at %I:%M %p")
        print(f"[Calendar] Added event: '{title}' at {event_dt.isoformat()}")
        return f"Event added: {title} on {formatted}."

    def get_events_today(self) -> str:
        """Returns today's events as a spoken string."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT title, event_dt, location FROM Events WHERE user_id = ? AND date(event_dt) = date('now') ORDER BY event_dt ASC",
                (self.user_id,)
            ).fetchall()

        if not rows:
            return "You have no events scheduled for today."

        parts = []
        for row in rows:
            dt = datetime.datetime.fromisoformat(row["event_dt"])
            time_str = dt.strftime("%I:%M %p")
            loc = f" at {row['location']}" if row["location"] else ""
            parts.append(f"{row['title']} at {time_str}{loc}")

        return f"Today you have {len(parts)} event{'s' if len(parts) > 1 else ''}: " + ". ".join(parts) + "."

    def get_events_tomorrow(self) -> str:
        """Returns tomorrow's events as a spoken string."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT title, event_dt, location FROM Events WHERE user_id = ? AND date(event_dt) = date('now', '+1 day') ORDER BY event_dt ASC",
                (self.user_id,)
            ).fetchall()

        if not rows:
            return "You have nothing scheduled for tomorrow."

        parts = []
        for row in rows:
            dt = datetime.datetime.fromisoformat(row["event_dt"])
            time_str = dt.strftime("%I:%M %p")
            loc = f" at {row['location']}" if row["location"] else ""
            parts.append(f"{row['title']} at {time_str}{loc}")

        return f"Tomorrow you have {len(parts)} event{'s' if len(parts) > 1 else ''}: " + ". ".join(parts) + "."

    def get_upcoming_events(self, days: int = 7) -> str:
        """Returns events in the next N days as a spoken string."""
        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT title, event_dt, location FROM Events WHERE user_id = ? AND event_dt >= datetime('now') AND event_dt <= datetime('now', '+{days} days') ORDER BY event_dt ASC",
                (self.user_id,)
            ).fetchall()

        if not rows:
            return f"You have no upcoming events in the next {days} days."

        parts = []
        for row in rows:
            dt = datetime.datetime.fromisoformat(row["event_dt"])
            date_str = dt.strftime("%A, %B %d at %I:%M %p")
            parts.append(f"{row['title']} on {date_str}")

        return f"Upcoming events: " + ". ".join(parts) + "."

    def get_today_ticker_text(self) -> str:
        """Returns a short ticker string for the HUD showing today's events."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT title, event_dt FROM Events WHERE user_id = ? AND date(event_dt) = date('now') ORDER BY event_dt ASC LIMIT 3",
                (self.user_id,)
            ).fetchall()

        if not rows:
            return ""

        parts = []
        for row in rows:
            dt = datetime.datetime.fromisoformat(row["event_dt"])
            parts.append(f"📅 {dt.strftime('%I:%M %p')} — {row['title']}")

        return "  •  ".join(parts)

    def delete_event(self, event_id: int) -> str:
        with self._conn() as conn:
            conn.execute("DELETE FROM Events WHERE id = ? AND user_id = ?", (event_id, self.user_id))
            conn.commit()
        return f"Event {event_id} deleted."


class TasksModule:
    """Manages a voice-driven to-do task list in SQLite."""

    PRIORITY_MAP = {"high": 3, "medium": 2, "normal": 2, "low": 1}

    def __init__(self, db_path: str = "data/memory.db", user_id: int = 1):
        self.db_path = db_path
        self.user_id = user_id

    def _conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def add_task(self, title: str, priority: str = "medium", due_date_str: Optional[str] = None) -> str:
        """Adds a task to the Tasks table."""
        if not title or not title.strip():
            return "What task would you like to add?"

        priority_val = self.PRIORITY_MAP.get(priority.lower(), 2)
        due_dt = None

        if due_date_str:
            try:
                import dateparser
                parsed = dateparser.parse(due_date_str, settings={"PREFER_DATES_FROM": "future"})
                if parsed:
                    due_dt = parsed.isoformat()
            except Exception:
                pass

        with self._conn() as conn:
            conn.execute(
                "INSERT INTO Tasks (user_id, title, priority, due_date) VALUES (?, ?, ?, ?)",
                (self.user_id, title.strip(), priority_val, due_dt)
            )
            conn.commit()

        due_str = f" Due: {due_date_str}." if due_date_str else ""
        print(f"[Tasks] Added: '{title}' priority={priority_val}")
        return f"Task added: {title}.{due_str}"

    def get_pending_tasks(self) -> str:
        """Returns all pending (not done) tasks as a spoken list."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, title, priority FROM Tasks WHERE user_id = ? AND is_done = 0 ORDER BY priority DESC, created_at ASC",
                (self.user_id,)
            ).fetchall()

        if not rows:
            return "Your task list is empty. Well done!"

        priority_labels = {3: "high", 2: "medium", 1: "low"}
        parts = [f"Task {i+1}: {row['title']} ({priority_labels.get(row['priority'], 'medium')} priority)"
                 for i, row in enumerate(rows)]
        return f"You have {len(parts)} pending task{'s' if len(parts) > 1 else ''}: " + ". ".join(parts) + "."

    def mark_done(self, task_id_or_title: str) -> str:
        """Marks a task done by ID or fuzzy title match."""
        # Try direct numeric ID
        if task_id_or_title.isdigit():
            task_id = int(task_id_or_title)
            with self._conn() as conn:
                conn.execute("UPDATE Tasks SET is_done = 1 WHERE id = ? AND user_id = ?", (task_id, self.user_id))
                conn.commit()
            return f"Task {task_id} marked as done."

        # Fuzzy title match
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, title FROM Tasks WHERE user_id = ? AND is_done = 0",
                (self.user_id,)
            ).fetchall()

        if not rows:
            return "You have no pending tasks."

        try:
            from rapidfuzz import process, fuzz
            titles = [row["title"] for row in rows]
            match = process.extractOne(task_id_or_title, titles, scorer=fuzz.WRatio, score_cutoff=60)
            if match:
                matched_title, score, idx = match
                task_id = rows[idx]["id"]
                with self._conn() as conn:
                    conn.execute("UPDATE Tasks SET is_done = 1 WHERE id = ? AND user_id = ?", (task_id, self.user_id))
                    conn.commit()
                return f"Marked '{matched_title}' as done."
        except ImportError:
            pass

        return f"I couldn't find a task matching '{task_id_or_title}'."

    def delete_task(self, task_id: int) -> str:
        with self._conn() as conn:
            conn.execute("DELETE FROM Tasks WHERE id = ? AND user_id = ?", (task_id, self.user_id))
            conn.commit()
        return f"Task {task_id} deleted."
