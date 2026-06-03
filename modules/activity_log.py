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

import datetime
from modules.memory_system import DatabaseManager

class ActivityLogger:
    def __init__(self, db_manager=None):
        if db_manager is None:
            self.db = DatabaseManager()
        else:
            self.db = db_manager
        # Run cleanup once at startup, not on every log call
        self.cleanup_old(30)

    def log(self, command_text, module_triggered, response_summary, success=True, user_id=1):
        """Logs a voice command and its outcome."""
        return self.db.log_activity(
            command=command_text,
            module=module_triggered,
            response=response_summary,
            success=success,
            user_id=user_id
        )

    def get_today(self, user_id=1):
        """Retrieves today's commands logged by the user, ordered by id desc."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT command_text, module_triggered, response_summary, success, timestamp
            FROM ActivityLog
            WHERE user_id = ? AND date(timestamp) = date('now')
            ORDER BY id DESC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_recent(self, n=10, user_id=1):
        """Retrieves the last n commands logged by the user, ordered by id desc."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT command_text, module_triggered, response_summary, success, timestamp
            FROM ActivityLog
            WHERE user_id = ?
            ORDER BY id DESC LIMIT ?
        """, (user_id, n))
        return [dict(row) for row in cursor.fetchall()]

    def cleanup_old(self, days=30):
        """Deletes activity log entries older than the specified number of days."""
        cursor = self.db.conn.cursor()
        # CURRENT_TIMESTAMP is stored in UTC by SQLite
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            DELETE FROM ActivityLog
            WHERE timestamp < ?
        """, (cutoff,))
        self.db.conn.commit()
