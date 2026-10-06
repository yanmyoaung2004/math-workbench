"""Integration: parse → solve → verify → steps through the real SymPy adapter."""

import pytest

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.solve_linear import solve_linear
from workbench_math.application.transform import transform_expression
from workbench_math.domain.exceptions import (
    InfiniteSolutionsError,
    NoSolutionError,
    ParseError,
    UnsolvableError,
    ValidationError,
)
from workbench_math.domain.models import Domain

PARSER = SymPyParser()
SOLVER = SymPySolver()


def solve(raw, domain=Domain.REALS):
    return solve_linear(raw, PARSER, SOLVER, domain)


@pytest.mark.parametrize(
    "raw, exact, ops",
    [
        ("2x + 5 = 17", "6", ["subtract_both_sides", "divide_both_sides"]),
        ("x - 4 = 9", "13", ["add_both_sides"]),
        ("x/3 = 4", "12", ["multiply_both_sides"]),
        ("2(x + 3) = 14", "4", ["distribute", "subtract_both_sides", "divide_both_sides"]),
        ("3x + 2 = x + 8", "3", ["collect_like_terms", "divide_both_sides"]),
        ("x = 6", "6", []),
        ("-3x = 9", "-3", ["divide_both_sides"]),
        ("x/2 + 1/3 = 5/6", "1", ["subtract_both_sides", "multiply_both_sides"]),
    ],
)
def test_linear_cases(raw, exact, ops):
    sol = solve(raw)
    assert sol.exact == (exact,)
    assert [s.operation for s in sol.steps] == ops
    assert sol.verification == "verified"
    assert float(sol.approximate[0]) == pytest.approx(float(exact))


def test_implicit_multiplication_and_caret():
    sol = solve("2x+5=17")
    assert sol.exact == ("6",)
    assert solve("2*x + 5 = 17").exact == ("6",)


def test_irrational_exact_kept_separate_from_approx():
    sol = solve("sqrt(2)*x = 2")
    assert sol.exact == ("sqrt(2)",)
    assert float(sol.approximate[0]) == pytest.approx(1.4142135623730951)
    assert sol.verification == "verified"


def test_error_taxonomy():
    with pytest.raises(NoSolutionError) as e:
        solve("0*x + 5 = 17")
    assert e.value.code == "NO_SOLUTION"
    with pytest.raises(InfiniteSolutionsError):
        solve("x + 2 = x + 2")
    with pytest.raises(InfiniteSolutionsError):
        solve("5 = 5")
    with pytest.raises(NoSolutionError):
        solve("5 = 6")
    with pytest.raises(ParseError) as e:
        solve("2x + = 17")
    assert e.value.code == "PARSE_ERROR"
    with pytest.raises(UnsolvableError):
        solve("x^2 = 4")  # quadratics → Phase 1b, honest refusal
    with pytest.raises(UnsolvableError):
        solve("y = 2x + 1")  # two variables → Phase 1b
    with pytest.raises(ParseError):
        solve("__import__('os') = 1")  # untrusted input rejected


def test_transforms():
    assert transform_expression("2x + 3x", "simplify", PARSER, SOLVER).exact == ("5*x",)
    assert transform_expression("(x + 1)^2", "expand", PARSER, SOLVER).exact == (
        "x**2 + 2*x + 1",)
    assert transform_expression("x^2 + 2*x + 1", "factorise", PARSER, SOLVER).exact == (
        "(x + 1)**2",)
    with pytest.raises(ValidationError):
        transform_expression("2x + 5 = 17", "simplify", PARSER, SOLVER)


def test_complex_domain_opt_in():
    sol = solve("x + 1 = 2", Domain.COMPLEX)
    assert sol.exact == ("1",)
