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

# TODO: implement DatabaseManager class with methods for all 8 tables:
#       store_fact(), get_facts(), log_activity(), log_message() etc.
