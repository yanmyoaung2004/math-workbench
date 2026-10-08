"""Transparent mastery scoring — deterministic, no ML (product.md §18).

Per-attempt score: correct with no hints 1.0; correct with 1–2 hints 0.7;
correct with 3+ hints 0.4; incorrect 0.0. Topic mastery is the mean as a
percentage. Recommendation points at the weakest topic under 70%.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Attempt:
    topic: str
    correct: bool
    hints_used: int = 0
    difficulty: str = ""


DIFFICULTY_ORDER = ("beginner", "basic", "intermediate", "advanced", "exam")
UNLOCK_THRESHOLD = 80.0
BKT_MASTERY = 0.95
BKT_MIN_ATTEMPTS = 3


def attempt_score(attempt: Attempt) -> float:
    if not attempt.correct:
        return 0.0
    if attempt.hints_used <= 0:
        return 1.0
    if attempt.hints_used <= 2:
        return 0.7
    return 0.4


def topic_mastery(attempts: tuple[Attempt, ...]) -> dict[str, float]:
    totals: dict[str, list[float]] = {}
    for attempt in attempts:
        totals.setdefault(attempt.topic, []).append(attempt_score(attempt))
    return {topic: round(sum(scores) / len(scores) * 100, 1)
            for topic, scores in totals.items()}


def recommend(mastery: dict[str, float]) -> str:
    if not mastery:
        return "Attempt some practice first — try beginner linear equations."
    weak = [(score, topic) for topic, score in mastery.items() if score < 70.0]
    if not weak:
        return "Balanced across topics — try exam-style questions."
    _, topic = min(weak)
    return f"Recommended practice: {topic} ({mastery[topic]}% mastery)."


def _mastery_by_topic_difficulty(attempts: tuple[Attempt, ...]) -> dict[tuple[str, str], float]:
    groups: dict[tuple[str, str], list[float]] = {}
    for attempt in attempts:
        if attempt.difficulty:
            groups.setdefault((attempt.topic, attempt.difficulty), []).append(
                attempt_score(attempt))
    return {k: round(sum(v) / len(v) * 100, 1) for k, v in groups.items()}


def unlocked_difficulties(topic: str, attempts: tuple[Attempt, ...],
                          threshold: float = UNLOCK_THRESHOLD) -> list[str]:
    """Mastery-gated progression: each level unlocks at >= threshold on all easier ones.

    Beginner is always open; untried easier levels count as passed (don't trap
    new students), but once attempted they must reach threshold.
    """
    by_level = _mastery_by_topic_difficulty(tuple(a for a in attempts if a.topic == topic))
    if not by_level:
        return [DIFFICULTY_ORDER[0]]  # fresh start (or untagged legacy data)
    open_levels = [DIFFICULTY_ORDER[0]]
    for level in DIFFICULTY_ORDER[1:]:
        prev = DIFFICULTY_ORDER[:DIFFICULTY_ORDER.index(level)]
        if all(by_level.get((topic, p), 100.0) >= threshold for p in prev):
            open_levels.append(level)
        else:
            break
    return open_levels


def bkt_gated_levels(bkt_p: float, n_attempts: int) -> list[str]:
    """BKT-driven gates: with enough evidence, P(mastery) >= 0.95 opens everything
    past beginner; otherwise fall back to one-step-ahead exploration."""
    if n_attempts >= BKT_MIN_ATTEMPTS and bkt_p >= BKT_MASTERY:
        return list(DIFFICULTY_ORDER)
    return [DIFFICULTY_ORDER[0], DIFFICULTY_ORDER[1]]
