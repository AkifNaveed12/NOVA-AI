"""
MODULE — Face Authentication
Registration: capture N face samples → average embedding → store in DB as BLOB
Verification: capture frame → compare vs stored embedding → cosine similarity
No cloud, no API, fully local using deepface.
"""

import cv2
import numpy as np
import pickle
import os
import secrets
from datetime import datetime, timedelta
from deepface import DeepFace


class FaceAuth:

    MODEL = "Facenet"              # Free, offline, ~90MB model download on first use
    SIMILARITY_THRESHOLD = 0.6    # Cosine similarity — > 0.6 = same person
    REGISTRATION_SAMPLES = 5      # Capture 5 frames, average embeddings
    SESSION_HOURS = 24

    def __init__(self, db_manager, camera_index: int = 0):
        self.db = db_manager
        self.cam_index = camera_index

    # ── Embedding utilities ──────────────────────────────────────

    def _get_embedding(self, frame: np.ndarray) -> np.ndarray | None:
        """Extract face embedding from a single frame. Returns None if no face found."""
        try:
            result = DeepFace.represent(
                img_path=frame,
                model_name=self.MODEL,
                enforce_detection=True,
                detector_backend="opencv"
            )
            return np.array(result[0]["embedding"])
        except Exception:
            return None

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    # ── DB utilities ─────────────────────────────────────────────

    def _store_embedding(self, user_name: str, embedding: np.ndarray):
        blob = pickle.dumps(embedding)
        self.db.conn.execute(
            "INSERT INTO face_identities (user_name, embedding, model) VALUES (?, ?, ?)",
            (user_name, blob, self.MODEL)
        )
        self.db.conn.commit()

    def _load_embedding(self, user_name: str) -> np.ndarray | None:
        row = self.db.conn.execute(
            "SELECT embedding FROM face_identities WHERE user_name = ? ORDER BY created_at DESC LIMIT 1",
            (user_name,)
        ).fetchone()
        if not row:
            return None
        return pickle.loads(row["embedding"])

    def is_registered(self, user_name: str) -> bool:
        row = self.db.conn.execute(
            "SELECT id FROM face_identities WHERE user_name = ?", (user_name,)
        ).fetchone()
        return row is not None

    # ── Registration ─────────────────────────────────────────────

    def register_from_webcam(self, user_name: str,
                              progress_callback=None) -> dict:
        """
        Opens webcam, captures REGISTRATION_SAMPLES frames with a face,
        averages the embeddings, stores in DB.
        """
        cap = cv2.VideoCapture(self.cam_index)
        if not cap.isOpened():
            return {"success": False, "error": "Camera not accessible."}

        embeddings = []
        attempts = 0
        max_attempts = 50  # try up to 50 frames to collect 5 good ones

        if progress_callback:
            progress_callback(f"Look at the camera. Collecting {self.REGISTRATION_SAMPLES} samples...")

        while len(embeddings) < self.REGISTRATION_SAMPLES and attempts < max_attempts:
            ret, frame = cap.read()
            if not ret:
                attempts += 1
                continue
            emb = self._get_embedding(frame)
            if emb is not None:
                embeddings.append(emb)
                if progress_callback:
                    progress_callback(f"Sample {len(embeddings)}/{self.REGISTRATION_SAMPLES} captured.")
            attempts += 1

        cap.release()

        if len(embeddings) < 3:
            return {"success": False,
                    "error": "Could not capture enough clear face samples. Ensure good lighting."}

        mean_embedding = np.mean(embeddings, axis=0)
        self._store_embedding(user_name, mean_embedding)
        return {"success": True,
                "message": f"Face registered for {user_name} ({len(embeddings)} samples)."}

    def register_from_frame(self, user_name: str, frame: np.ndarray) -> dict:
        """Register from a single frame (e.g., from phone camera via API)."""
        emb = self._get_embedding(frame)
        if emb is None:
            return {"success": False, "error": "No face detected in frame."}
        self._store_embedding(user_name, emb)
        return {"success": True, "message": f"Face registered for {user_name}."}

    # ── Verification ─────────────────────────────────────────────

    def verify_from_webcam(self, user_name: str) -> dict:
        """Verify identity from a single webcam capture."""
        cap = cv2.VideoCapture(self.cam_index)
        if not cap.isOpened():
            return {"authenticated": False, "error": "Camera not accessible."}

        for _ in range(20):  # try 20 frames
            ret, frame = cap.read()
            if not ret:
                continue
            emb = self._get_embedding(frame)
            if emb is not None:
                cap.release()
                return self._compare(user_name, emb)

        cap.release()
        return {"authenticated": False, "error": "Could not detect a face."}

    def verify_from_frame(self, user_name: str, frame: np.ndarray) -> dict:
        """Verify from a numpy frame (from API upload)."""
        emb = self._get_embedding(frame)
        if emb is None:
            return {"authenticated": False, "error": "No face detected."}
        return self._compare(user_name, emb)

    def _compare(self, user_name: str, new_embedding: np.ndarray) -> dict:
        stored = self._load_embedding(user_name)
        if stored is None:
            return {"authenticated": False,
                    "error": f"No face registered for '{user_name}'. Please register first."}
        similarity = self._cosine_similarity(stored, new_embedding)
        authenticated = similarity >= self.SIMILARITY_THRESHOLD
        return {
            "authenticated": authenticated,
            "similarity": round(similarity, 4),
            "threshold": self.SIMILARITY_THRESHOLD,
            "user_name": user_name if authenticated else None
        }

    # ── Session tokens ────────────────────────────────────────────

    def create_session(self, user_name: str) -> str:
        token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(hours=self.SESSION_HOURS)
        self.db.conn.execute(
            "INSERT INTO face_sessions (token, user_name, expires_at) VALUES (?, ?, ?)",
            (token, user_name, expires.isoformat())
        )
        self.db.conn.commit()
        return token

    def validate_session(self, token: str) -> dict:
        row = self.db.conn.execute(
            "SELECT user_name, expires_at FROM face_sessions WHERE token = ?",
            (token,)
        ).fetchone()
        if not row:
            return {"valid": False}
        if datetime.fromisoformat(row["expires_at"]) < datetime.now():
            return {"valid": False, "reason": "expired"}
        return {"valid": True, "user_name": row["user_name"]}
