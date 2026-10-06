"""History store: ordering, limits, clearing, migration gate."""

import sqlite3

import pytest

from workbench_math.adapters.sqlite_history import SqliteHistory


def test_save_and_list_newest_first(tmp_path):
    store = SqliteHistory(tmp_path / "h.db")
    store.save("solve_linear", "2x + 5 = 17", "2*x + 5 = 17", ("6",), "verified")
    store.save("simplify", "2x + 3x", "2*x + 3*x", ("5*x",), "verified")
    entries = store.list_recent()
    assert [e.input for e in entries] == ["2x + 3x", "2x + 5 = 17"]
    assert entries[0].id > entries[1].id
    assert entries[0].exact == ("5*x",) and entries[0].verification == "verified"
    assert entries[0].timestamp  # ISO-8601 recorded


def test_limit_clamped(tmp_path):
    store = SqliteHistory(tmp_path / "h.db")
    for i in range(5):
        store.save("parse", f"x + {i}", f"x + {i}", (f"x + {i}",), "verified")
    assert len(store.list_recent(2)) == 2
    assert len(store.list_recent(0)) == 1  # clamped, never empty-page crash
    assert len(store.list_recent(10000)) == 5  # clamped to 200, only 5 stored


def test_clear_returns_count(tmp_path):
    store = SqliteHistory(tmp_path / "h.db")
    store.save("parse", "x", "x", ("x",), "verified")
    assert store.clear() == 1
    assert store.list_recent() == ()
    assert store.clear() == 0


def test_schema_version_gate(tmp_path):
    path = tmp_path / "h.db"
    SqliteHistory(path)  # creates v1
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA user_version = 99")
    with pytest.raises(RuntimeError, match="not supported"):
        SqliteHistory(path)


def test_parent_dirs_created(tmp_path):
    store = SqliteHistory(tmp_path / "deep" / "nested" / "h.db")
    assert store.list_recent() == ()
