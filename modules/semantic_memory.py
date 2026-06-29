import sqlite3
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple

class SemanticMemory:
    """SQLite + in-process sentence embeddings. No external vector DB."""

    MODEL_NAME = "all-MiniLM-L6-v2"  # 22MB, runs in ~50ms on CPU

    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        
        # Ensure directories exist
        dirname = os.path.dirname(self.db_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
            
        self.model = SentenceTransformer(self.MODEL_NAME)
        self._ensure_schema()
        self._migrate_legacy_facts()

    def _ensure_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP,
                    UNIQUE(key)
                )
            """)
            conn.commit()

    def _migrate_legacy_facts(self):
        """Migrates facts from legacy UserFacts table to semantic_facts if not already present."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='UserFacts'")
                if not cursor.fetchone():
                    return
                
                cursor.execute("SELECT key, value, category FROM UserFacts")
                legacy_rows = cursor.fetchall()
                if not legacy_rows:
                    return
                
                # Check if we have entries already
                cursor.execute("SELECT COUNT(*) FROM semantic_facts")
                if cursor.fetchone()[0] > 0:
                    return
                
                print(f"[SemanticMemory] Migrating {len(legacy_rows)} legacy user facts...")
                for row in legacy_rows:
                    key = row["key"]
                    value = row["value"]
                    cat = row["category"] or "general"
                    self.store(key, value, cat)
        except Exception as e:
            print(f"[SemanticMemory] Migration error (non-fatal): {e}")

    def store(self, key: str, value: str, category: str = "general"):
        text = f"{key}: {value}"
        embedding = self.model.encode(text).astype(np.float32).tobytes()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO semantic_facts (key, value, category, embedding)
                VALUES (?, ?, ?, ?)
            """, (key, value, category, embedding))
            conn.commit()

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
        """Returns top_k (key, value, similarity_score) tuples for a query."""
        query_embedding = self.model.encode(query).astype(np.float32)

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, key, value, embedding FROM semantic_facts"
            ).fetchall()

        scored = []
        for row_id, key, value, emb_bytes in rows:
            if not emb_bytes:
                continue
            fact_emb = np.frombuffer(emb_bytes, dtype=np.float32)
            # Cosine similarity
            sim = float(np.dot(query_embedding, fact_emb) /
                       (np.linalg.norm(query_embedding) * np.linalg.norm(fact_emb) + 1e-8))
            scored.append((key, value, sim, row_id))

        scored.sort(key=lambda x: x[2], reverse=True)

        # Update access counts for retrieved facts
        if scored:
            top_ids = [r[3] for r in scored[:top_k]]
            with sqlite3.connect(self.db_path) as conn:
                for rid in top_ids:
                    conn.execute(
                        "UPDATE semantic_facts SET access_count = access_count + 1, "
                        "last_accessed = CURRENT_TIMESTAMP WHERE id = ?", (rid,)
                    )
                conn.commit()

        return [(k, v, s) for k, v, s, _ in scored[:top_k]]

    def inject_for_prompt(self, query: str, top_k: int = 8) -> str:
        """Returns formatted memory string for Groq system prompt injection."""
        facts = self.search(query, top_k)
        if not facts:
            return ""
        lines = [f"  - {k}: {v}" for k, v, _ in facts if _ > 0.3]  # threshold 0.3
        return "\n\nKnown facts about the user:\n" + "\n".join(lines) if lines else ""

# Singleton — pre-loaded at startup
semantic_memory = SemanticMemory()
