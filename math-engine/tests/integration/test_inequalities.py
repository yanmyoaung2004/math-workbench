"""Integration: linear inequalities incl. the sign-flip teaching moment."""

import pytest

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.solve_inequality import solve_inequality
from workbench_math.domain.exceptions import (
    InfiniteSolutionsError,
    NoSolutionError,
    ParseError,
    UnsolvableError,
)
from workbench_math.domain.models import Domain

PARSER = SymPyParser()
SOLVER = SymPySolver()


def solve(raw):
    return solve_inequality(raw, PARSER, SOLVER, Domain.REALS)


def test_basic_gt():
    sol = solve("2x + 3 > 9")
    assert sol.exact == ("x > 3",)
    assert [s.operation for s in sol.steps] == ["subtract_both_sides", "divide_both_sides"]
    assert sol.verification == "verified"


def test_negative_division_flips_with_teaching_note():
    sol = solve("-2x + 3 < 9")
    assert sol.exact == ("x > -3",)
    ops = [s.operation for s in sol.steps]
    assert "flip_inequality_sign" in ops
    flip = next(s for s in sol.steps if s.operation == "flip_inequality_sign")
    assert "reverse the inequality sign" in flip.explanation
    assert sol.verification == "verified"


def test_gte_and_lte_forms():
    assert solve("x - 4 >= 9").exact == ("x >= 13",)
    assert solve("5 - x <= 2").exact == ("x >= 3",)
    assert solve("3x <= 12").exact == ("x <= 4",)


def test_reversed_comparison():
    assert solve("9 < 2x + 3").exact == ("x > 3",)  # normalized x-first


def test_two_sided_collect():
    sol = solve("3x + 2 > x + 8")
    assert sol.exact == ("x > 3",)
    assert sol.steps[0].operation == "collect_like_terms"
    assert sol.verification == "verified"


def test_brackets_distribute():
    sol = solve("2(x + 3) >= 14")
    assert sol.exact == ("x >= 4",)
    assert sol.steps[0].operation == "distribute"
    assert sol.verification == "verified"


def test_empty_and_universal_sets():
    with pytest.raises(NoSolutionError):
        solve("x + 1 > x + 2")
    with pytest.raises(InfiniteSolutionsError):
        solve("x + 2 > x + 1")


def test_nonlinear_and_chained_rejected():
    with pytest.raises(UnsolvableError):
        solve("x^2 > 4")
    with pytest.raises(ParseError):
        solve("1 < x < 5")
