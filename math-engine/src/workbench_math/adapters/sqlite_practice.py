"""SQLite practice adapter — attempts, review schedule, assignments (offline).

Same versioning convention as the history store (`PRAGMA user_version`, v1).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ..ports.practice_store import Assignment, PracticeAttempt, PracticeStore, ReviewItem

_SCHEMA_VERSION = 2
_SCHEMA = """
CREATE TABLE IF NOT EXISTS practice_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    topic TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    correct INTEGER NOT NULL,
    hints_used INTEGER NOT NULL,
    mistake TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS reviews (
    prompt TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    next_due TEXT NOT NULL,
    interval_days INTEGER NOT NULL,
    ease REAL NOT NULL,
    updated TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    n INTEGER NOT NULL,
    seed INTEGER NOT NULL,
    created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bkt_state (
    topic TEXT PRIMARY KEY,
    p_mastery REAL NOT NULL,
    n_attempts INTEGER NOT NULL,
    updated TEXT NOT NULL
);
"""


class SqlitePractice(PracticeStore):
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._path) as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version in (0, 1):
                # IF NOT EXISTS makes this idempotent: fresh DBs get everything,
                # v1 DBs gain the bkt_state table.
                conn.executescript(_SCHEMA)
                conn.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")
            elif version != _SCHEMA_VERSION:
                raise RuntimeError(
                    f"Practice database version {version} is not supported "
                    f"(this build reads v{_SCHEMA_VERSION}).")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def record_attempt(self, topic, difficulty, correct, hints_used, mistake="") -> int:
        with sqlite3.connect(self._path) as conn:
            cur = conn.execute(
                "INSERT INTO practice_attempts (ts, topic, difficulty, correct, hints_used, mistake)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (self._now(), topic, difficulty, int(bool(correct)),
                 int(hints_used), mistake or ""),
            )
            return cur.lastrowid

    def recent_attempts(self, limit: int = 200) -> tuple[PracticeAttempt, ...]:
        limit = max(1, min(int(limit), 1000))
        with sqlite3.connect(self._path) as conn:
            rows = conn.execute(
                "SELECT id, ts, topic, difficulty, correct, hints_used, mistake"
                " FROM practice_attempts ORDER BY id DESC LIMIT ?", (limit,),
            ).fetchall()
        return tuple(
            PracticeAttempt(id=r[0], timestamp=r[1], topic=r[2], difficulty=r[3],
                            correct=bool(r[4]), hints_used=r[5], mistake=r[6])
            for r in rows
        )

    def upsert_review(self, prompt, topic, next_due, interval_days, ease) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                "INSERT INTO reviews (prompt, topic, next_due, interval_days, ease, updated)"
                " VALUES (?, ?, ?, ?, ?, ?)"
                " ON CONFLICT(prompt) DO UPDATE SET topic=excluded.topic,"
                " next_due=excluded.next_due, interval_days=excluded.interval_days,"
                " ease=excluded.ease, updated=excluded.updated",
                (prompt, topic, next_due, int(interval_days), float(ease), self._now()),
            )

    def due_reviews(self, today: str, limit: int = 20) -> tuple[ReviewItem, ...]:
        limit = max(1, min(int(limit), 200))
        with sqlite3.connect(self._path) as conn:
            rows = conn.execute(
                "SELECT prompt, topic, next_due, interval_days, ease FROM reviews"
                " WHERE next_due <= ? ORDER BY next_due ASC LIMIT ?", (today, limit),
            ).fetchall()
        return tuple(
            ReviewItem(prompt=r[0], topic=r[1], next_due=r[2], interval_days=r[3], ease=r[4])
            for r in rows
        )

    def create_assignment(self, title, topic, difficulty, n, seed) -> int:
        with sqlite3.connect(self._path) as conn:
            cur = conn.execute(
                "INSERT INTO assignments (title, topic, difficulty, n, seed, created)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (title, topic, difficulty, int(n), int(seed), self._now()),
            )
            return cur.lastrowid

    def list_assignments(self) -> tuple[Assignment, ...]:
        with sqlite3.connect(self._path) as conn:
            rows = conn.execute(
                "SELECT id, title, topic, difficulty, n, seed, created FROM assignments"
                " ORDER BY id DESC").fetchall()
        return tuple(
            Assignment(id=r[0], title=r[1], topic=r[2], difficulty=r[3],
                       n=r[4], seed=r[5], created=r[6])
            for r in rows
        )

    def get_bkt(self, topic: str) -> tuple[float, int]:
        from ..practice.bkt import BKTParams

        with sqlite3.connect(self._path) as conn:
            row = conn.execute(
                "SELECT p_mastery, n_attempts FROM bkt_state WHERE topic = ?",
                (topic,)).fetchone()
        if row is None:
            return BKTParams().p_init, 0
        return float(row[0]), int(row[1])

    def set_bkt(self, topic: str, p_mastery: float, n_attempts: int) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                "INSERT INTO bkt_state (topic, p_mastery, n_attempts, updated)"
                " VALUES (?, ?, ?, ?)"
                " ON CONFLICT(topic) DO UPDATE SET p_mastery=excluded.p_mastery,"
                " n_attempts=excluded.n_attempts, updated=excluded.updated",
                (topic, float(p_mastery), int(n_attempts), self._now()),
            )

    def record_override(self, attempt_id: int, correct: bool) -> bool:
        with sqlite3.connect(self._path) as conn:
            cur = conn.execute(
                "UPDATE practice_attempts SET correct = ? WHERE id = ?",
                (int(bool(correct)), int(attempt_id)),
            )
            return cur.rowcount > 0
