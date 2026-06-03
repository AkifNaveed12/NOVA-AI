"""
MODULE 20 — Memory System (SQLite)
=====================================
Persistent memory across sessions. Stores user facts, conversation
logs, notes, reminders, events, tasks, contacts, and activity history
in data/memory.db (SQLite). Top-10 facts injected into Groq prompts.
Facts auto-extracted from conversations by Groq after each session.

Tech: sqlite3 (built-in)
Storage: data/memory.db — 8 tables (see architecture.md ERD)
Tables: Users, UserFacts, Notes, Tasks, Events, Reminders,
        Contacts, ActivityLog, ConversationLog
"""

import sqlite3
import os
import datetime

class DatabaseManager:
    def __init__(self, db_path="data/memory.db"):
        self.db_path = db_path
        
        # Ensure data directory exists if not an in-memory DB
        dirname = os.path.dirname(self.db_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # Enable WAL mode for safe concurrent writes from multiple threads
            self.conn.execute("PRAGMA journal_mode=WAL")
            # Enable row access by column name
            self.conn.row_factory = sqlite3.Row
            self._create_tables()
            self._ensure_default_user()
        except sqlite3.DatabaseError as e:
            print(f"[DatabaseManager] DB corrupted ({e}). Recreating schema...")
            # If DB is corrupted, delete and recreate
            if db_path != ":memory:" and os.path.exists(db_path):
                os.remove(db_path)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.row_factory = sqlite3.Row
            self._create_tables()
            self._ensure_default_user()

    def _create_tables(self):
        """Creates the foundational 9 tables for all NOVA modules."""
        cursor = self.conn.cursor()
        
        # 1. Users
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 2. UserFacts
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserFacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Users(id),
            UNIQUE(user_id, key)
        )
        ''')
        
        # 3. Notes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity_id INTEGER,
            content TEXT NOT NULL,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Users(id)
        )
        ''')
        
        # 4. Tasks
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity_id INTEGER,
            title TEXT NOT NULL,
            is_done BOOLEAN DEFAULT 0,
            priority INTEGER DEFAULT 1,
            due_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Users(id)
        )
        ''')
        
        # 5. Events
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity_id INTEGER,
            title TEXT NOT NULL,
            event_dt TIMESTAMP NOT NULL,
            location TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Users(id)
        )
        ''')
        
        # 6. Reminders
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity_id INTEGER,
            title TEXT NOT NULL,
            message TEXT,
            trigger_at TIMESTAMP NOT NULL,
            is_done BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Users(id)
        )
        ''')
        
        # 7. Contacts
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            platform TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Users(id)
        )
        ''')
        
        # 8. ActivityLog
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ActivityLog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            command_text TEXT NOT NULL,
            module_triggered TEXT,
            response_summary TEXT,
            success BOOLEAN DEFAULT 1,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Users(id)
        )
        ''')
        
        # 9. ConversationLog
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ConversationLog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            session_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Users(id),
            FOREIGN KEY(activity_id) REFERENCES ActivityLog(id)
        )
        ''')
        
        self.conn.commit()

    def _ensure_default_user(self):
        """Creates the default user (ID 1) if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM Users WHERE id = 1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Users (name) VALUES (?)", ("Akif",))
            self.conn.commit()

    # ── Memory / Facts ───────────────────────────────────────────────
    
    def store_fact(self, key: str, value: str, category: str = "general", user_id: int = 1):
        """Stores or updates a long-term memory fact about the user."""
        cursor = self.conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        # Upsert logic
        cursor.execute('''
        INSERT INTO UserFacts (user_id, key, value, category, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, key) DO UPDATE SET
            value=excluded.value,
            category=excluded.category,
            updated_at=excluded.updated_at
        ''', (user_id, key, value, category, now, now))
        
        self.conn.commit()

    def get_facts(self, limit: int = 10, user_id: int = 1) -> list:
        """Retrieves the most recently updated facts to inject into the LLM context."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT key, value FROM UserFacts 
            WHERE user_id = ? 
            ORDER BY updated_at DESC LIMIT ?
        ''', (user_id, limit))
        
        return [(row["key"], row["value"]) for row in cursor.fetchall()]

    # ── Logging ──────────────────────────────────────────────────────
    
    def log_activity(self, command: str, module: str, response: str, success: bool = True, user_id: int = 1) -> int:
        """Logs a top-level interaction and returns the activity_id."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO ActivityLog (user_id, command_text, module_triggered, response_summary, success)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, command, module, response, success))
        self.conn.commit()
        return cursor.lastrowid
        
    def log_conversation(self, role: str, content: str, activity_id: int = None, session_id: str = None, user_id: int = 1):
        """Logs individual messages (user or assistant) for conversational context."""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO ConversationLog (user_id, activity_id, role, content, session_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, activity_id, role, content, session_id))
        self.conn.commit()


# Module-level singleton — imported by nova_core and activity_log to share one connection
db_singleton = DatabaseManager()
