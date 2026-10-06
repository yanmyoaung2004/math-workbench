"""Mistake classifier: student step vs expected transform, minimal correction.

Compares the student's `after` against the expected step's `after` through an
injected identity check (SymPy-backed in production, fakeable in tests) and
classifies by operation family: brackets, signs, arithmetic, or unknown. Never
says just "wrong" — always shows the smallest useful correction with the
reason (product.md §15).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..domain.exceptions import ValidationError
from ..domain.models import Step


@dataclass(frozen=True)
class Mistake:
    category: str  # bracket_distribution | sign | arithmetic | unparseable | unknown_step
    explanation: str
    correction: str  # the expected `after`


_FAMILY = {
    "distribute": "bracket_distribution",
    "subtract_both_sides": "sign",
    "add_both_sides": "sign",
    "divide_both_sides": "arithmetic",
    "multiply_both_sides": "arithmetic",
}

_WHY = {
    "bracket_distribution": (
        "The multiplier must reach every term inside the bracket, not just the first."
    ),
    "sign": (
        "Check the sign of the term you moved — adding and subtracting are easy to mix up."
    ),
    "arithmetic": "Check the division or multiplication itself — the method was right.",
    "unknown_step": "Compare each part of your line with the line above it.",
}


def classify(expected: Step, student_after: str,
             identical: Callable[[str, str], bool]) -> Mistake | None:
    """None when the student step is correct; otherwise a classified Mistake.

    `identical(a, b)` answers whether two expressions are mathematically equal
    (production: solver.check_identity).
    """
    if not student_after or not student_after.strip():
        raise ValidationError("Show your working line so it can be checked.")
    try:
        if bool(identical(student_after.strip(), expected.after)):
            return None
    except Exception:
        return Mistake(
            category="unparseable",
            explanation="I couldn't read that line — check brackets and operators.",
            correction=expected.after,
        )
    category = _FAMILY.get(expected.operation, "unknown_step")
    return Mistake(
        category=category,
        explanation=f"{_WHY[category]} It should be: {expected.after}.",
        correction=expected.after,
    )
