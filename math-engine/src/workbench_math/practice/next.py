"""Adaptive selection: IRT-flavored difficulty calibration, no fitting library.

Each (topic, difficulty) family carries an empirical solve-rate from logged
attempts. Selection picks, among BKT-unlocked difficulties, the family with the
lowest solve-rate (at least 2 attempts) — i.e. the easiest unmastered material
first. Cold start (no data) walks the ladder in order. Deterministic given data.
"""

from __future__ import annotations

from .mastery import DIFFICULTY_ORDER


def solve_rates(attempt_counts: dict[tuple[str, str], tuple[int, int]]) -> dict[str, dict[str, float]]:
    """{(topic, difficulty): (correct, total)} -> {topic: {difficulty: rate}}."""
    rates: dict[str, dict[str, float]] = {}
    for (topic, difficulty), (correct, total) in attempt_counts.items():
        if total > 0:
            rates.setdefault(topic, {})[difficulty] = round(correct / total, 3)
    return rates


def choose_difficulty(topic: str, unlocked: list[str],
                      rates: dict[str, dict[str, float]],
                      min_attempts: int = 2,
                      counts: dict[str, dict[str, int]] | None = None) -> str:
    """Easiest unmastered unlocked difficulty; falls back to ladder order."""
    topic_rates = rates.get(topic, {})
    topic_counts = (counts or {}).get(topic, {})
    candidates = [d for d in DIFFICULTY_ORDER if d in unlocked]
    if not candidates:
        return DIFFICULTY_ORDER[0]
    weak = [(rate, d) for d, rate in topic_rates.items()
            if d in unlocked and rate < 0.8
            and topic_counts.get(d, min_attempts) >= min_attempts]
    if weak:
        return min(weak)[1]
    tried = [d for d in candidates if d in topic_rates]
    if tried:
        # Everything tried is solid — push to the next unlocked level.
        idx = max(DIFFICULTY_ORDER.index(d) for d in tried)
        if idx + 1 < len(DIFFICULTY_ORDER) and DIFFICULTY_ORDER[idx + 1] in unlocked:
            return DIFFICULTY_ORDER[idx + 1]
    return candidates[0]
