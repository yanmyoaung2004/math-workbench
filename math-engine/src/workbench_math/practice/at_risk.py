"""At-risk flags: deterministic early warnings teachers can audit.

Every flag carries its reason and the numbers behind it — no black box.
Thresholds are constants so they can be tuned per school and tested exactly.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskFlag:
    topic: str
    flag: str
    reason: str


MIN_ATTEMPTS_STEM = 3
HINT_RATE_LIMIT = 0.6
HINT_MIN_ATTEMPTS = 5
MISTAKE_SPIKE_COUNT = 3
MISTAKE_WINDOW = 10


def detect(attempts: tuple, now_iso: str = "") -> tuple[RiskFlag, ...]:
    """Newest-first attempts (topic, correct, hints_used, mistake, timestamp attrs)."""
    flags: list[RiskFlag] = []
    by_topic: dict[str, list] = {}
    for attempt in attempts:
        by_topic.setdefault(attempt.topic, []).append(attempt)
    for topic, items in by_topic.items():
        if len(items) >= MIN_ATTEMPTS_STEM:
            recent = items[:MIN_ATTEMPTS_STEM]
            if not any(a.correct for a in recent):
                flags.append(RiskFlag(
                    topic, "struggling",
                    f"No correct answers in the last {MIN_ATTEMPTS_STEM} {topic} attempts."))
        if len(items) >= HINT_MIN_ATTEMPTS:
            hinted = sum(1 for a in items if a.hints_used > 0)
            if hinted / len(items) > HINT_RATE_LIMIT:
                flags.append(RiskFlag(
                    topic, "hint-dependent",
                    f"{hinted}/{len(items)} recent {topic} attempts used hints."))
        window = items[:MISTAKE_WINDOW]
        counts: dict[str, int] = {}
        for a in window:
            if a.mistake:
                counts[a.mistake] = counts.get(a.mistake, 0) + 1
        for kind, count in sorted(counts.items()):
            if count >= MISTAKE_SPIKE_COUNT:
                flags.append(RiskFlag(
                    topic, f"repeated-{kind}",
                    f"{count} recent {topic} errors classified as {kind.replace('_', ' ')}."))
    return tuple(flags)
