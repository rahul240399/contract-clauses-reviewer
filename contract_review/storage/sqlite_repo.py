"""SQLite implementation of the ReviewRepository port.

File-based and zero-config for v1; the whole Report is stored as JSON with a few
queryable columns pulled out. Swapping to Postgres later means writing another
adapter, not changing the core.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..models import Report

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    id              TEXT PRIMARY KEY,
    document_id     TEXT NOT NULL,
    playbook_id     TEXT NOT NULL,
    deviation_score REAL NOT NULL,
    report_json     TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    signoff_status  TEXT NOT NULL DEFAULT 'pending'
)
"""


class SQLiteReviewRepository:
    def __init__(self, db_path: str | Path = "reviews.db") -> None:
        self.db_path = str(db_path)
        with self._connect() as conn:
            conn.execute(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def save(
        self,
        report: Report,
        *,
        review_id: str | None = None,
        created_at: str | None = None,
    ) -> str:
        review_id = review_id or uuid.uuid4().hex
        created_at = created_at or datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO reviews "
                "(id, document_id, playbook_id, deviation_score, report_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    review_id,
                    report.document_id,
                    report.playbook_id,
                    report.deviation_score,
                    report.model_dump_json(),
                    created_at,
                ),
            )
        return review_id

    def get(self, review_id: str) -> Report | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT report_json FROM reviews WHERE id = ?", (review_id,)
            ).fetchone()
        return Report.model_validate_json(row[0]) if row else None

    def list_ids(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id FROM reviews ORDER BY created_at"
            ).fetchall()
        return [row[0] for row in rows]

    def set_signoff(self, review_id: str, status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE reviews SET signoff_status = ? WHERE id = ?",
                (status, review_id),
            )
