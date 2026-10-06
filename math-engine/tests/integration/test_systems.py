"""Integration: 2x2 linear systems through the real SymPy adapter."""

import pytest

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.solve_system import solve_system
from workbench_math.domain.exceptions import (
    InfiniteSolutionsError,
    NoSolutionError,
    ValidationError,
)
from workbench_math.domain.models import Domain

PARSER = SymPyParser()
SOLVER = SymPySolver()


def solve(eq1, eq2):
    return solve_system([eq1, eq2], PARSER, SOLVER, Domain.REALS)


def test_unique_elimination_flow():
    sol = solve("2x + y = 7", "x - y = 2")
    assert [(b.variable, b.exact) for b in sol.bindings] == [("x", "3"), ("y", "1")]
    ops = [s.operation for s in sol.steps]
    assert "eliminate_variable" in ops and "substitute_back" in ops
    assert sol.steps[-1].after == "x = 3; y = 1"
    assert sol.verification == "verified"


def test_already_aligned_coefficients_skip_scaling():
    sol = solve("x + y = 5", "x - y = 1")
    assert [(b.variable, b.exact) for b in sol.bindings] == [("x", "3"), ("y", "2")]
    assert "scale_equation" not in [s.operation for s in sol.steps]
    assert sol.verification == "verified"


def test_single_variable_equation_shortcut():
    sol = solve("x = 3", "x + y = 5")
    assert [(b.variable, b.exact) for b in sol.bindings] == [("x", "3"), ("y", "2")]
    assert sol.verification == "verified"


def test_fractions_stay_exact():
    sol = solve("x + 2y = 1", "3x - y = 7")
    assert [(b.variable, b.exact) for b in sol.bindings] == [("x", "15/7"), ("y", "-4/7")]
    assert sol.verification == "verified"


def test_parallel_lines_no_solution():
    with pytest.raises(NoSolutionError) as err:
        solve("x + y = 1", "x + y = 2")
    assert err.value.code == "NO_SOLUTION"


def test_same_line_infinite():
    with pytest.raises(InfiniteSolutionsError):
        solve("2x + 2y = 4", "x + y = 2")


def test_wrong_arity_rejected():
    with pytest.raises(ValidationError):
        solve_system(["x = 1"], PARSER, SOLVER)
    with pytest.raises(ValidationError):
        solve_system(["x = 1", "y = 2", "x + y = 3"], PARSER, SOLVER)
