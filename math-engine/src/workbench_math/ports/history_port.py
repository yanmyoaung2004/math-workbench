"""History port — persistence seam for calculation history (offline-first)."""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass(frozen=True)
class HistoryEntry:
    id: int
    timestamp: str  # ISO-8601 UTC
    op: str
    input: str
    interpretation: str
    exact: tuple[str, ...]
    verification: str


class HistoryPort(abc.ABC):
    @abc.abstractmethod
    def save(self, op: str, input: str, interpretation: str,
             exact: tuple[str, ...], verification: str) -> int:
        """Persist one verified computation; returns its row id."""
        raise NotImplementedError

    @abc.abstractmethod
    def list_recent(self, limit: int = 50) -> tuple[HistoryEntry, ...]:
        """Newest-first entries (limit clamped to 1–200)."""
        raise NotImplementedError

    @abc.abstractmethod
    def clear(self) -> int:
        """Delete all entries; returns the count removed."""
        raise NotImplementedError
