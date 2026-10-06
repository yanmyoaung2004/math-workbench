"""Grounded tutor: prompts carry verified truth; failures degrade honestly.

The provider receives interpretation + exact answers + steps + student context,
so explanations describe real mathematics. If the provider fails, the reply
falls back to a deterministic step summary flagged provider="fallback" — the
math stays visible either way, and AI never blocks the UI (it runs after solve).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..domain.models import Solution
from .provider import AIProviderError, ProviderPort, StubProvider

_SYSTEM = (
    "You are a GCSE/O-Level maths tutor. Explain using ONLY the verified "
    "solution given. Never invent answers, never override the steps, and use "
    "simple language without advanced terminology. If unsure, say so."
)


@dataclass(frozen=True)
class TutorReply:
    explanation: str
    provider: str


def _grounding(solution: Solution, question: str, attempt: str,
               mistake: str, hints_shown: int) -> str:
    steps = "\n".join(
        f"- {s.explanation} ({s.before} -> {s.after})" for s in solution.steps)
    answers = ", ".join(solution.exact) if solution.exact else solution.interpretation
    context = [f"Verified interpretation: {solution.interpretation}",
               f"Verified answer: {answers}", f"Verified steps:\n{steps}"]
    if attempt:
        context.append(f"Student attempt: {attempt}")
    if mistake:
        context.append(f"Detected mistake: {mistake}")
    context.append(f"Hints already shown: {hints_shown}")
    context.append(f"Student question: {question}")
    return "\n".join(context)


def _fallback_summary(solution: Solution) -> str:
    answers = ", ".join(solution.exact) if solution.exact else solution.interpretation
    first = solution.steps[0].explanation if solution.steps else "No steps recorded."
    return (f"[offline tutor] The verified answer is {answers}. "
            f"Start here: {first}")


class TutorService:
    def __init__(self, provider: ProviderPort | None = None):
        self.provider = provider or StubProvider()

    def explain(self, solution: Solution, question: str, attempt: str = "",
               mistake: str = "", hints_shown: int = 0,
               level: str = "gcse") -> TutorReply:
        prompt = _grounding(solution, question, attempt, mistake, hints_shown)
        if level != "gcse":
            prompt += f"\nStudent level: {level}."
        try:
            text = self.provider.complete(prompt, system=_SYSTEM)
            return TutorReply(explanation=text, provider=self.provider.name)
        except AIProviderError:
            return TutorReply(explanation=_fallback_summary(solution), provider="fallback")
