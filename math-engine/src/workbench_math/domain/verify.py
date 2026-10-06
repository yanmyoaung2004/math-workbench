"""Verification helpers — domain-pure checks over DTO strings.

The *mathematical* equality test needs symbolic power, so it is injected as a
callable by the adapter layer. Everything else here is stdlib string logic,
keeping `import sympy` out of the domain (ADR-0001) while keeping the check
independent of the solver that produced the candidate (FR-VER-1).
"""

from __future__ import annotations

from collections.abc import Callable

from .models import Solution
from .steps import check_chain

# (lhs, rhs, symbol, candidate) -> True iff substituting candidate for symbol
# makes both sides equal under exact semantics.
EqualityFn = Callable[[str, str, str, str], bool]


def solution_holds(
    equation_canonical: str,
    symbol: str,
    candidate_canonical: str,
    equality: EqualityFn,
) -> bool:
    """True iff substituting the candidate makes both sides equal.

    Malformed input returns False (never raises) — the caller decides the code.
    """
    try:
        lhs, rhs = equation_canonical.split("=", 1)
    except ValueError:
        return False
    lhs, rhs = lhs.strip(), rhs.strip()
    if not lhs or not rhs or not symbol or not candidate_canonical:
        return False
    try:
        return bool(equality(lhs, rhs, symbol, candidate_canonical))
    except Exception:
        return False


def solution_self_consistent(solution: Solution, final_form: str) -> bool:
    """Steps chain from interpretation to final form (structure, not math)."""
    return check_chain(solution.interpretation, solution.steps, final_form)
