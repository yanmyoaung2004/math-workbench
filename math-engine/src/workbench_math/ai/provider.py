"""AI provider seam — the LLM explains verified mathematics, never invents it.

Grounding rule (product.md §21): every tutor call carries the verified result +
steps + student context; provider output is an explanation aid only. Offline
default: StubProvider. Cloud providers need user keys at runtime and are never
required for core math.
"""

from __future__ import annotations

import abc


class AIProviderError(Exception):
    pass


class ProviderPort(abc.ABC):
    name: str = "provider"

    @abc.abstractmethod
    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 500) -> str:
        """Return model text for the prompt. Raises AIProviderError on failure."""
        raise NotImplementedError


class StubProvider(ProviderPort):
    """Deterministic offline provider: templates the verified facts, no network."""

    name = "stub"

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 500) -> str:
        body = prompt.strip().splitlines()
        first = next((line.strip() for line in body if line.strip()), "")
        return (
            "[offline tutor] " + first[: max_tokens - 16]
            if len(first) > max_tokens - 16
            else "[offline tutor] " + first
        )
