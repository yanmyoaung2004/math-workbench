"""Curated worked examples: fixed prompts, engine-proved answers.

Prompts are static content; answers are NEVER hardcoded — each example is
solved and verified live, so content cannot drift from engine truth.
"""

from __future__ import annotations

EXAMPLES: tuple[tuple[str, str, str], ...] = (
    ("linear", "2x + 5 = 17", "solve_linear"),
    ("linear", "3(x - 2) = 15", "solve_linear"),
    ("linear", "x/4 + 1 = 6", "solve_linear"),
    ("quadratic", "x^2 - 5x + 6 = 0", "solve_quadratic"),
    ("quadratic", "x^2 - 2 = 0", "solve_quadratic"),
    ("quadratic", "2x^2 + 8x + 6 = 0", "solve_quadratic"),
    ("linear", "2x + 3 > 9", "solve_inequality"),
    ("linear", "-2x + 3 < 9", "solve_inequality"),
    ("expression", "2x + 3x", "simplify"),
    ("expression", "(x + 1)^2", "expand"),
)


def examples_for(topic: str) -> tuple[tuple[str, str, str], ...]:
    if topic in ("all", ""):
        return EXAMPLES
    return tuple(e for e in EXAMPLES if e[0] == topic)
