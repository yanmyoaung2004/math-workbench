"""SQLite history adapter — stdlib sqlite3, versioned schema, local file only.

Schema v1 (fresh DBs get it; user_version gates future migrations):
  history(id, ts, op, input, interpretation, exact_json, verification)
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ..ports.history_port import HistoryEntry, HistoryPort

_SCHEMA_VERSION = 1
_SCHEMA = """
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    op TEXT NOT NULL,
    input TEXT NOT NULL,
    interpretation TEXT NOT NULL,
    exact_json TEXT NOT NULL,
    verification TEXT NOT NULL
);
"""


class SqliteHistory(HistoryPort):
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._path) as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version == 0:
                conn.executescript(_SCHEMA)
                conn.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")
            elif version != _SCHEMA_VERSION:
                raise RuntimeError(
                    f"History database version {version} is not supported "
                    f"(this build reads v{_SCHEMA_VERSION})."
                )

    def save(self, op, input, interpretation, exact, verification) -> int:
        with sqlite3.connect(self._path) as conn:
            cur = conn.execute(
                "INSERT INTO history (ts, op, input, interpretation, exact_json, verification)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), op, input, interpretation,
                 json.dumps(list(exact)), verification),
            )
            return cur.lastrowid

    def list_recent(self, limit: int = 50) -> tuple[HistoryEntry, ...]:
        limit = max(1, min(int(limit), 200))
        with sqlite3.connect(self._path) as conn:
            rows = conn.execute(
                "SELECT id, ts, op, input, interpretation, exact_json, verification"
                " FROM history ORDER BY id DESC LIMIT ?", (limit,),
            ).fetchall()
        return tuple(
            HistoryEntry(id=r[0], timestamp=r[1], op=r[2], input=r[3],
                         interpretation=r[4], exact=tuple(json.loads(r[5])),
                         verification=r[6])
            for r in rows
        )

    def clear(self) -> int:
        with sqlite3.connect(self._path) as conn:
            cur = conn.execute("DELETE FROM history")
            return cur.rowcount
