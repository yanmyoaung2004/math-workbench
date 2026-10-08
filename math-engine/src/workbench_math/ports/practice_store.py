"""Practice persistence seam — attempts, review schedule, assignments (offline)."""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass(frozen=True)
class PracticeAttempt:
    id: int
    timestamp: str
    topic: str
    difficulty: str
    correct: bool
    hints_used: int
    mistake: str = ""


@dataclass(frozen=True)
class ReviewItem:
    prompt: str
    topic: str
    next_due: str  # ISO date
    interval_days: int
    ease: float


@dataclass(frozen=True)
class Assignment:
    id: int
    title: str
    topic: str
    difficulty: str
    n: int
    seed: int
    created: str


class PracticeStore(abc.ABC):
    @abc.abstractmethod
    def record_attempt(self, topic: str, difficulty: str, correct: bool,
                       hints_used: int, mistake: str = "") -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def recent_attempts(self, limit: int = 200) -> tuple[PracticeAttempt, ...]:
        raise NotImplementedError

    @abc.abstractmethod
    def upsert_review(self, prompt: str, topic: str, next_due: str,
                      interval_days: int, ease: float) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def due_reviews(self, today: str, limit: int = 20) -> tuple[ReviewItem, ...]:
        raise NotImplementedError

    @abc.abstractmethod
    def create_assignment(self, title: str, topic: str, difficulty: str,
                          n: int, seed: int) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def list_assignments(self) -> tuple[Assignment, ...]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_bkt(self, topic: str) -> tuple[float, int]:
        """Return (P(mastery), n_attempts) for a topic; (default P(L0), 0) if new."""
        raise NotImplementedError

    @abc.abstractmethod
    def set_bkt(self, topic: str, p_mastery: float, n_attempts: int) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def record_override(self, attempt_id: int, correct: bool) -> bool:
        """Teacher override of an auto-mark; returns True if the row existed."""
        raise NotImplementedError
