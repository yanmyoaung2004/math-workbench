"""GCSE spec-point map: curriculum codes → generator topics.

Neutral codes (not board-specific prose) keep this offline and stable; labels
use plain GCSE vocabulary. Worksheets and practice browsing resolve through here.
"""

from __future__ import annotations

SPEC_POINTS: dict[str, dict[str, str]] = {
    "ALG-LIN-1": {"topic": "linear", "difficulty": "beginner",
                  "label": "One-step linear equations"},
    "ALG-LIN-2": {"topic": "linear", "difficulty": "basic",
                  "label": "Two-step linear equations"},
    "ALG-LIN-3": {"topic": "linear", "difficulty": "intermediate",
                  "label": "Equations with brackets"},
    "ALG-LIN-4": {"topic": "linear", "difficulty": "advanced",
                  "label": "Equations with fractions"},
    "ALG-LIN-5": {"topic": "linear", "difficulty": "exam",
                  "label": "Equations with unknowns both sides"},
    "ALG-QUAD-1": {"topic": "quadratic", "difficulty": "basic",
                   "label": "Factorising monic quadratics"},
    "ALG-QUAD-2": {"topic": "quadratic", "difficulty": "intermediate",
                   "label": "Factorising non-monic quadratics"},
    "ALG-QUAD-3": {"topic": "quadratic", "difficulty": "advanced",
                   "label": "Quadratic formula and surd answers"},
    "ALG-QUAD-4": {"topic": "quadratic", "difficulty": "exam",
                   "label": "Completing the square"},
    "ALG-INEQ-1": {"topic": "linear", "difficulty": "intermediate",
                   "label": "Linear inequalities"},
    "ALG-SYS-1": {"topic": "linear", "difficulty": "exam",
                  "label": "Simultaneous equations"},
    "GRF-QUAD-1": {"topic": "quadratic", "difficulty": "intermediate",
                   "label": "Plotting quadratics and finding roots"},
}


def resolve_spec(code: str) -> tuple[str, str, str]:
    """Return (topic, difficulty, label); raises KeyError on unknown codes."""
    entry = SPEC_POINTS[code.strip().upper()]
    return entry["topic"], entry["difficulty"], entry["label"]
