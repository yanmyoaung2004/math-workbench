"""Integration: quadratics through the real SymPy adapter (all three paths)."""

import pytest

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.solve_quadratic import solve_quadratic
from workbench_math.domain.exceptions import (
    NoSolutionError,
    UnsolvableError,
    ValidationError,
)
from workbench_math.domain.models import Domain

PARSER = SymPyParser()
SOLVER = SymPySolver()


def solve(raw, domain=Domain.REALS, method="auto"):
    return solve_quadratic(raw, PARSER, SOLVER, domain, method)


def test_factor_path_auto():
    sol = solve("x^2 - 5x + 6 = 0")
    assert sol.exact == ("2", "3")
    assert [s.operation for s in sol.steps] == [
        "factorise_equation", "apply_zero_product", "apply_zero_product"]
    assert sol.verification == "verified"
    assert sol.steps[-1].after == "x = 2; x = 3"


def test_double_root_single_zero_product_step():
    sol = solve("x^2 - 2x + 1 = 0")
    assert sol.exact == ("1",)
    assert [s.operation for s in sol.steps] == ["factorise_equation", "apply_zero_product"]
    assert sol.verification == "verified"


def test_formula_path_explicit():
    sol = solve("x^2 - 5x + 6 = 0", method="formula")
    assert sol.exact == ("2", "3")
    assert [s.operation for s in sol.steps] == [
        "identify_coefficients", "compute_discriminant", "apply_quadratic_formula"]
    assert "1" in sol.steps[1].operand  # D = 1 shown
    assert sol.verification == "verified"


def test_nonstandard_form_gets_rewrite_first():
    sol = solve("x^2 = 4x - 3")
    assert sol.exact == ("1", "3")
    assert sol.steps[0].operation == "rewrite"
    assert sol.verification == "verified"


def test_complete_square_path():
    sol = solve("x^2 + 6x + 5 = 0", method="complete_square")
    assert sol.exact == ("-1", "-5")  # deterministic string order
    assert [s.operation for s in sol.steps] == [
        "complete_the_square", "take_square_root_pm", "subtract_both_sides"]
    assert sol.verification == "verified"


def test_complete_square_with_leading_coefficient():
    sol = solve("2x^2 + 8x + 6 = 0", method="complete_square")
    assert sol.exact == ("-1", "-3")  # deterministic string order
    assert sol.steps[0].operation == "divide_both_sides"
    assert sol.verification == "verified"


def test_no_real_roots_honest():
    with pytest.raises(NoSolutionError) as err:
        solve("x^2 + 1 = 0")
    assert err.value.code == "NO_SOLUTION"
    assert "discriminant" in str(err.value).lower()


def test_complex_opt_in():
    sol = solve("x^2 + 1 = 0", Domain.COMPLEX)
    assert sol.exact == ("-I", "I")
    assert sol.verification == "verified"


def test_unfactorable_explicit_factorise_refused():
    with pytest.raises(UnsolvableError):
        solve("x^2 + x + 1 = 0", method="factorise")


def test_wrong_degree_routing():
    with pytest.raises(ValidationError):
        solve("2x + 5 = 17", method="auto")  # linear → solve_linear
    with pytest.raises(UnsolvableError):
        solve("x^3 - 1 = 0")  # cubics out of V1 scope


def test_irrational_roots_exact():
    sol = solve("x^2 - 2 = 0")
    assert sol.exact == ("-sqrt(2)", "sqrt(2)")
    assert float(sol.approximate[1]) == pytest.approx(1.4142135623730951)
    assert sol.verification == "verified"
