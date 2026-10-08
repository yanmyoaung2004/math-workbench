"""Calculus: term-wise steps, independent numeric verification."""

import pytest

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.calculus import (
    differentiate_expression,
    integrate_expression,
)
from workbench_math.domain.exceptions import UnsolvableError, ValidationError
from workbench_math.domain.models import Domain  # noqa: F401 (signature parity)

PARSER = SymPyParser()
SOLVER = SymPySolver()


def test_differentiate_polynomial_steps():
    sol = differentiate_expression("3x^2 + 2x + 5", PARSER, SOLVER)
    assert sol.exact == ("6*x + 2",)
    ops = [s.operation for s in sol.steps]
    assert ops == ["apply_power_rule", "apply_power_rule", "apply_constant_rule"]
    assert sol.verification == "verified"


def test_differentiate_trig_and_chain():
    sol = differentiate_expression("sin(x)", PARSER, SOLVER)
    assert sol.exact == ("cos(x)",)
    assert sol.steps[0].operation == "apply_trig_rule"
    assert sol.verification == "verified"
    sol = differentiate_expression("sin(x^2)", PARSER, SOLVER)
    assert sol.steps[0].operation == "apply_chain_rule"
    assert sol.verification == "verified"


def test_indefinite_integral_with_constant():
    sol = integrate_expression("3x^2 + 2x", PARSER, SOLVER)
    assert sol.exact == ("x**3 + x**2 + C",)
    assert sol.steps[-1].operation == "add_integration_constant"
    assert sol.verification == "verified"


def test_definite_integral_fundamental_theorem():
    sol = integrate_expression("2x", PARSER, SOLVER, "0", "3")
    assert sol.exact == ("9",)
    assert sol.steps[-1].operation == "evaluate_bounds"
    assert sol.verification == "verified"


def test_nonintegrable_and_equations_rejected():
    with pytest.raises(UnsolvableError):
        integrate_expression("x^x", PARSER, SOLVER)  # no elementary antiderivative
    with pytest.raises(ValidationError):
        differentiate_expression("2x + 5 = 17", PARSER, SOLVER)
    with pytest.raises(ValidationError):
        integrate_expression("2x", PARSER, SOLVER, "0", "")
