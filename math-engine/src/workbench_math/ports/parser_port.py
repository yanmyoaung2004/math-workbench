"""Parser port — implemented by adapters, faked in unit tests."""

from __future__ import annotations

import abc

from ..domain.models import Expression


class ParserPort(abc.ABC):
    @abc.abstractmethod
    def parse(self, raw: str) -> Expression:
        """Parse a user string into a normalized Expression (FR-IN-1/2)."""
        raise NotImplementedError
