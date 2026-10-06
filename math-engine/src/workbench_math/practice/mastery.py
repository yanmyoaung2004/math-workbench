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
