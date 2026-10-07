"""Practice store: attempts, review scheduling, assignments, streaks."""

from workbench_math.adapters.sqlite_practice import SqlitePractice
from workbench_math.practice.reviews import (
    next_review,
    quality_for,
    streak_days,
)


def test_attempt_round_trip(tmp_path):
    store = SqlitePractice(tmp_path / "p.db")
    row = store.record_attempt("linear", "basic", True, 0, "")
    assert row == 1
    store.record_attempt("linear", "basic", False, 2, "sign")
    attempts = store.recent_attempts()
    assert [a.topic for a in attempts] == ["linear", "linear"]
    assert attempts[0].mistake == "sign" and attempts[0].correct is False


def test_review_schedule_flow(tmp_path):
    store = SqlitePractice(tmp_path / "p.db")
    assert store.due_reviews("2026-10-07") == ()
    store.upsert_review("2x + 5 = 17", "linear", "2026-10-07", 1, 2.5)
    due = store.due_reviews("2026-10-07")
    assert len(due) == 1 and due[0].prompt == "2x + 5 = 17"
    assert store.due_reviews("2026-10-06") == ()


def test_sm2_intervals():
    assert quality_for(True, 0) == 5
    assert quality_for(True, 2) == 3
    assert quality_for(False, 0) == 0
    due, interval, ease = next_review(2.5, 0, 5, "2026-10-07")
    assert (due, interval) == ("2026-10-08", 1)
    due, interval, ease = next_review(2.5, 1, 5, "2026-10-07")
    assert interval == 6 and ease >= 2.5
    due, interval, _ = next_review(2.5, 6, 0, "2026-10-07")
    assert (due, interval) == ("2026-10-08", 1)  # lapse resets


def test_streak_counts_consecutive_days():
    assert streak_days((), "2026-10-07") == (0, False)
    assert streak_days(("2026-10-07T10:00:00", "2026-10-06T10:00:00"), "2026-10-07") == (2, True)
    assert streak_days(("2026-10-06T10:00:00",), "2026-10-07") == (1, False)
    assert streak_days(("2026-10-05T10:00:00", "2026-10-03T10:00:00"), "2026-10-07") == (0, False)


def test_assignments(tmp_path):
    store = SqlitePractice(tmp_path / "p.db")
    row = store.create_assignment("Friday set", "linear", "basic", 5, 11)
    assert row == 1
    listed = store.list_assignments()
    assert len(listed) == 1 and listed[0].title == "Friday set"
    assert listed[0].seed == 11
