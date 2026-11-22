"""
Database Access Layer for CareerAI.
Provides hybrid persistence:
1. Connects to MongoDB Atlas if MONGODB_URI is provided.
2. Automatically falls back to local SQLite with zero external dependencies,
   ensuring 100% offline, privacy-first local user storage.
3. Implements persistent analysis_history with strict user privacy controls.
"""

import os
import json
import uuid
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from backend.app.core.config import settings
except ModuleNotFoundError:
    from app.core.config import settings


class DatabaseManager:
    """Thread-safe database manager supporting MongoDB and local SQLite fallback."""

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or settings.SQLITE_DB_PATH
        self._lock = threading.Lock()
        self._mongo_client = None
        self._mongo_db = None
        self._use_mongo = False

        # Attempt MongoDB connection if URI is set
        if settings.MONGODB_URI:
            try:
                import pymongo
                self._mongo_client = pymongo.MongoClient(
                    settings.MONGODB_URI,
                    serverSelectionTimeoutMS=2000
                )
                # Quick ping to verify connectivity
                self._mongo_client.admin.command("ping")
                self._mongo_db = self._mongo_client[settings.DATABASE_NAME]
                self._use_mongo = True
            except Exception:
                # Silently fall back to SQLite for local reliability
                self._use_mongo = False
                self._mongo_client = None

        if not self._use_mongo:
            self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite tables and schema."""
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._get_sqlite_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    current_role TEXT,
                    experience_years REAL,
                    target_role TEXT,
                    save_resume_text INTEGER DEFAULT 0,
                    token_version INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_blocklist (
                    token TEXT PRIMARY KEY,
                    invalidated_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    skills_json TEXT NOT NULL,
                    education_summary TEXT,
                    experience_years REAL,
                    top_prediction_json TEXT,
                    latest_match_json TEXT,
                    latest_roadmap_json TEXT,
                    extracted_text TEXT,
                    full_snapshot_json TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_user ON analysis_history (user_id, created_at DESC)
            """)
            conn.commit()

    def _get_sqlite_conn(self) -> sqlite3.Connection:
        """Create a new SQLite connection with dict row access."""
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    # -------------------------------------------------------------------------
    # User Operations
    # -------------------------------------------------------------------------

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile by primary ID."""
        if self._use_mongo:
            doc = self._mongo_db.users.find_one({"_id": user_id})
            if doc:
                doc["id"] = doc.pop("_id")
                return doc
            return None

        with self._get_sqlite_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["save_resume_text"] = bool(d["save_resume_text"])
                return d
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile by email address (case-insensitive)."""
        clean_email = email.strip().lower()
        if self._use_mongo:
            doc = self._mongo_db.users.find_one({"email": clean_email})
            if doc:
                doc["id"] = doc.pop("_id")
                return doc
            return None

        with self._get_sqlite_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE lower(email) = ?", (clean_email,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["save_resume_text"] = bool(d["save_resume_text"])
                return d
            return None

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new user record into the database."""
        now_iso = datetime.now(timezone.utc).isoformat()
        record = {
            "id": user_data["id"],
            "email": user_data["email"].strip().lower(),
            "hashed_password": user_data["hashed_password"],
            "full_name": user_data["full_name"].strip(),
            "current_role": user_data.get("current_role"),
            "experience_years": user_data.get("experience_years"),
            "target_role": user_data.get("target_role"),
            "save_resume_text": bool(user_data.get("save_resume_text", False)),
            "token_version": 1,
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        if self._use_mongo:
            mongo_record = dict(record)
            mongo_record["_id"] = mongo_record.pop("id")
            self._mongo_db.users.insert_one(mongo_record)
            return record

        with self._lock:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (
                        id, email, hashed_password, full_name, current_role,
                        experience_years, target_role, save_resume_text,
                        token_version, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record["id"],
                    record["email"],
                    record["hashed_password"],
                    record["full_name"],
                    record["current_role"],
                    record["experience_years"],
                    record["target_role"],
                    1 if record["save_resume_text"] else 0,
                    record["token_version"],
                    record["created_at"],
                    record["updated_at"],
                ))
                conn.commit()

        return record

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update mutable fields of a user profile."""
        now_iso = datetime.now(timezone.utc).isoformat()
        updates["updated_at"] = now_iso

        if self._use_mongo:
            self._mongo_db.users.update_one({"_id": user_id}, {"$set": updates})
            return self.get_user_by_id(user_id)

        allowed_fields = [
            "full_name", "current_role", "experience_years",
            "target_role", "save_resume_text", "updated_at"
        ]
        set_clauses = []
        values = []

        for field in allowed_fields:
            if field in updates:
                set_clauses.append(f"{field} = ?")
                val = updates[field]
                if field == "save_resume_text":
                    val = 1 if val else 0
                values.append(val)

        if not set_clauses:
            return self.get_user_by_id(user_id)

        values.append(user_id)
        sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"

        with self._lock:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, tuple(values))
                conn.commit()

        return self.get_user_by_id(user_id)

    def delete_user(self, user_id: str) -> bool:
        """Permanently delete a user account and cascade delete all history."""
        if self._use_mongo:
            self._mongo_db.analysis_history.delete_many({"user_id": user_id})
            res = self._mongo_db.users.delete_one({"_id": user_id})
            return res.deleted_count > 0

        with self._lock:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM analysis_history WHERE user_id = ?", (user_id,))
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                return cursor.rowcount > 0

    def increment_token_version(self, user_id: str) -> int:
        """Increment token_version to immediately invalidate all active JWTs."""
        if self._use_mongo:
            res = self._mongo_db.users.find_one_and_update(
                {"_id": user_id},
                {"$inc": {"token_version": 1}},
                return_document=True
            )
            return res.get("token_version", 1) if res else 1

        with self._lock:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET token_version = token_version + 1 WHERE id = ?", (user_id,))
                conn.commit()
                cursor.execute("SELECT token_version FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                return row[0] if row else 1

    # -------------------------------------------------------------------------
    # Token Invalidation & Blocklist
    # -------------------------------------------------------------------------

    def blocklist_token(self, token: str) -> None:
        """Add a specific token string to the blocklist."""
        now_iso = datetime.now(timezone.utc).isoformat()
        if self._use_mongo:
            self._mongo_db.token_blocklist.update_one(
                {"token": token},
                {"$set": {"token": token, "invalidated_at": now_iso}},
                upsert=True
            )
            return

        with self._lock:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO token_blocklist (token, invalidated_at) VALUES (?, ?)",
                    (token, now_iso)
                )
                conn.commit()

    def is_token_blocklisted(self, token: str) -> bool:
        """Check if a token has been blocklisted."""
        if self._use_mongo:
            return self._mongo_db.token_blocklist.find_one({"token": token}) is not None

        with self._get_sqlite_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM token_blocklist WHERE token = ?", (token,))
            return cursor.fetchone() is not None

    # -------------------------------------------------------------------------
    # Analysis History Operations (Feature #2 & #3)
    # -------------------------------------------------------------------------

    def save_history_record(
        self,
        user_id: str,
        data: Dict[str, Any],
        allow_save_text: bool = False
    ) -> Dict[str, Any]:
        """
        Save or update an analysis history record for an authenticated user.
        Strictly enforces the user's save_resume_text privacy preference:
        if allow_save_text is False, extracted_text is stored as None.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        record_id = data.get("record_id") or str(uuid.uuid4())

        # Enforce privacy preference on extracted_text
        sanitized_text = data.get("extracted_text") if allow_save_text else None

        # Clean full_snapshot if present
        full_snapshot = data.get("full_snapshot")
        if full_snapshot and isinstance(full_snapshot, dict):
            snapshot_clean = dict(full_snapshot)
            if not allow_save_text:
                snapshot_clean["extracted_text"] = None
                if "analysisData" in snapshot_clean and isinstance(snapshot_clean["analysisData"], dict):
                    snap_analysis = dict(snapshot_clean["analysisData"])
                    snap_analysis["extracted_text"] = None
                    snapshot_clean["analysisData"] = snap_analysis
        else:
            snapshot_clean = None

        record = {
            "id": record_id,
            "user_id": user_id,
            "filename": data["filename"],
            "created_at": data.get("created_at") or now_iso,
            "updated_at": now_iso,
            "skills": data.get("skills", {}),
            "education_summary": data.get("education_summary"),
            "experience_years": data.get("experience_years"),
            "top_prediction": data.get("top_prediction"),
            "latest_match": data.get("latest_match"),
            "latest_roadmap": data.get("latest_roadmap"),
            "extracted_text": sanitized_text,
            "full_snapshot": snapshot_clean,
        }

        if self._use_mongo:
            mongo_record = dict(record)
            mongo_record["_id"] = mongo_record.pop("id")
            self._mongo_db.analysis_history.replace_one(
                {"_id": record_id, "user_id": user_id},
                mongo_record,
                upsert=True
            )
            return record

        with self._lock:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO analysis_history (
                        id, user_id, filename, created_at, updated_at,
                        skills_json, education_summary, experience_years,
                        top_prediction_json, latest_match_json, latest_roadmap_json,
                        extracted_text, full_snapshot_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        filename = excluded.filename,
                        updated_at = excluded.updated_at,
                        skills_json = excluded.skills_json,
                        education_summary = excluded.education_summary,
                        experience_years = excluded.experience_years,
                        top_prediction_json = excluded.top_prediction_json,
                        latest_match_json = excluded.latest_match_json,
                        latest_roadmap_json = excluded.latest_roadmap_json,
                        extracted_text = excluded.extracted_text,
                        full_snapshot_json = excluded.full_snapshot_json
                """, (
                    record["id"],
                    record["user_id"],
                    record["filename"],
                    record["created_at"],
                    record["updated_at"],
                    json.dumps(record["skills"]),
                    record["education_summary"],
                    record["experience_years"],
                    json.dumps(record["top_prediction"]) if record["top_prediction"] else None,
                    json.dumps(record["latest_match"]) if record["latest_match"] else None,
                    json.dumps(record["latest_roadmap"]) if record["latest_roadmap"] else None,
                    record["extracted_text"],
                    json.dumps(record["full_snapshot"]) if record["full_snapshot"] else None,
                ))
                conn.commit()

        return record

    def list_history_records(self, user_id: str) -> List[Dict[str, Any]]:
        """Return all analysis history records for a user, newest first."""
        if self._use_mongo:
            cursor = self._mongo_db.analysis_history.find(
                {"user_id": user_id}
            ).sort("created_at", -1)
            results = []
            for doc in cursor:
                doc["id"] = doc.pop("_id")
                results.append(doc)
            return results

        with self._get_sqlite_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, filename, created_at, updated_at,
                       skills_json, education_summary, experience_years,
                       top_prediction_json, latest_match_json, latest_roadmap_json,
                       extracted_text
                FROM analysis_history
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["skills"] = json.loads(d.pop("skills_json"))
                d["top_prediction"] = json.loads(d.pop("top_prediction_json")) if d.get("top_prediction_json") else None
                d["latest_match"] = json.loads(d.pop("latest_match_json")) if d.get("latest_match_json") else None
                d["latest_roadmap"] = json.loads(d.pop("latest_roadmap_json")) if d.get("latest_roadmap_json") else None
                results.append(d)
            return results

    def get_history_record_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific history record by its primary ID."""
        if self._use_mongo:
            doc = self._mongo_db.analysis_history.find_one({"_id": record_id})
            if doc:
                doc["id"] = doc.pop("_id")
                return doc
            return None

        with self._get_sqlite_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analysis_history WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["skills"] = json.loads(d.pop("skills_json"))
            d["top_prediction"] = json.loads(d.pop("top_prediction_json")) if d.get("top_prediction_json") else None
            d["latest_match"] = json.loads(d.pop("latest_match_json")) if d.get("latest_match_json") else None
            d["latest_roadmap"] = json.loads(d.pop("latest_roadmap_json")) if d.get("latest_roadmap_json") else None
            d["full_snapshot"] = json.loads(d.pop("full_snapshot_json")) if d.get("full_snapshot_json") else None
            return d

    def delete_history_record(self, record_id: str, user_id: str) -> bool:
        """Delete a single history record owned by user."""
        if self._use_mongo:
            res = self._mongo_db.analysis_history.delete_one({"_id": record_id, "user_id": user_id})
            return res.deleted_count > 0

        with self._lock:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM analysis_history WHERE id = ? AND user_id = ?", (record_id, user_id))
                conn.commit()
                return cursor.rowcount > 0

    def clear_user_history(self, user_id: str) -> int:
        """Delete all history records for a user."""
        if self._use_mongo:
            res = self._mongo_db.analysis_history.delete_many({"user_id": user_id})
            return res.deleted_count

        with self._lock:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM analysis_history WHERE user_id = ?", (user_id,))
                conn.commit()
                return cursor.rowcount

    def reset_database(self) -> None:
        """Purge all rows (used exclusively for clean testing isolation)."""
        if self._use_mongo:
            self._mongo_db.analysis_history.delete_many({})
            self._mongo_db.users.delete_many({})
            self._mongo_db.token_blocklist.delete_many({})
            return

        with self._lock:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM analysis_history")
                cursor.execute("DELETE FROM users")
                cursor.execute("DELETE FROM token_blocklist")
                conn.commit()


# Global database singleton
_db_instance: Optional[DatabaseManager] = None


def get_db(db_path: Optional[str] = None) -> DatabaseManager:
    """Return the application database manager singleton."""
    global _db_instance
    if _db_instance is None or db_path is not None:
        _db_instance = DatabaseManager(db_path=db_path)
    return _db_instance
