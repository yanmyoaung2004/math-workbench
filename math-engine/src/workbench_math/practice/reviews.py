"""Spaced-repetition scheduling (SM-2 lite) — pure, deterministic, stdlib only.

Quality 0..5 maps from attempt outcome: correct first-try 5, correct with
hints 3, incorrect 0. Intervals grow 1 → 6 → ease-scaled days.
"""

from __future__ import annotations

from datetime import date, timedelta


def quality_for(correct: bool, hints_used: int) -> int:
    if not correct:
        return 0
    return 5 if hints_used <= 0 else 3


def next_review(ease: float, interval_days: int, quality: int,
                today: str) -> tuple[str, int, float]:
    """Return (next_due_iso, interval_days, ease). Never raises on sane input."""
    ease = max(1.3, ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    if quality < 3:
        interval = 1
    elif interval_days <= 1:
        interval = 6 if interval_days == 1 else 1
    else:
        interval = max(1, round(interval_days * ease))
    base = date.fromisoformat(today)
    due = base + timedelta(days=interval)
    return due.isoformat(), interval, round(ease, 2)


def streak_days(active_dates: tuple[str, ...], today: str) -> tuple[int, bool]:
    """Consecutive-day streak ending today (or yesterday); active_today flag."""
    days = sorted({d[:10] for d in active_dates}, reverse=True)
    if not days:
        return 0, False
    base = date.fromisoformat(today[:10])
    active_today = days[0] == base.isoformat()
    start = base if active_today else base - timedelta(days=1)
    streak = 0
    expected = start
    for day in days:
        if day == expected.isoformat():
            streak += 1
            expected -= timedelta(days=1)
        elif day < expected.isoformat():
            break
    return streak, active_today
