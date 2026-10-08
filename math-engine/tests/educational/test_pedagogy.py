"""Educational tests: correct answer alone is NOT passing (docs/testing.md).

Covers operation choice, step order, rule vocabulary, GCSE wording, and the
inequality sign-flip teaching note. Runs without SymPy (templates + one
reference solve each for order checks).
"""

import pytest

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.solve_inequality import solve_inequality
from workbench_math.application.solve_linear import solve_linear
from workbench_math.application.solve_quadratic import solve_quadratic
from workbench_math.domain.models import Domain
from workbench_math.domain.steps import EXPLANATIONS

PARSER = SymPyParser()
SOLVER = SymPySolver()

# Terms no GCSE/O-Level student should meet in a step explanation.
BANNED_TERMS = [
    "homomorphism", "isomorphism", "eigen", "manifold", "topolog", "lemma",
    "corollary", "trivial", "obviously", "clearly", "simply", "just ",
    "kernel", "image", "codomain", "surjective", "injective", "bijective",
]


def test_all_explanations_gcse_worded_and_punctuated():
    for op, (rule, template) in EXPLANATIONS.items():
        rendered = template.format(operand="2", symbol="x")
        assert rendered.endswith("."), op
        lowered = rendered.lower()
        for term in BANNED_TERMS:
            assert term not in lowered, f"{op} uses banned term {term!r}"
        assert "{" not in rendered and "}" not in rendered, op


def test_every_rule_from_approved_vocabulary():
    approved = {
        "subtraction_property_of_equality", "addition_property_of_equality",
        "division_property_of_equality", "multiplication_property_of_equality",
        "distributive_property", "combining_like_terms", "equivalent_form",
        "simplification", "expansion", "factorisation", "zero_product_property",
        "standard_quadratic_form", "discriminant", "quadratic_formula",
        "completing_the_square", "square_root_property", "elimination_method",
        "substitution_method", "inequality_sign_reversal",
        "power_rule", "constant_rule", "trig_derivative",
        "exponential_derivative", "chain_rule", "differentiation",
        "power_rule_reversed", "constant_integral", "integration",
        "integration_constant", "fundamental_theorem",
    }
    for op, (rule, _) in EXPLANATIONS.items():
        assert rule in approved, f"{op} uses unknown rule {rule!r}"


def test_linear_operation_order():
    sol = solve_linear("2x + 5 = 17", PARSER, SOLVER, Domain.REALS)
    assert [s.operation for s in sol.steps] == ["subtract_both_sides", "divide_both_sides"]
    assert sol.steps[0].rule == "subtraction_property_of_equality"
    assert sol.steps[1].rule == "division_property_of_equality"


def test_quadratic_factor_order_and_zero_product_names_factor():
    sol = solve_quadratic("x^2 - 5x + 6 = 0", PARSER, SOLVER, Domain.REALS)
    ops = [s.operation for s in sol.steps]
    assert ops[0] == "factorise_equation"
    assert ops[1:] == ["apply_zero_product", "apply_zero_product"]
    assert "x - 2" in sol.steps[1].explanation
    assert "x - 3" in sol.steps[2].explanation


def test_discriminant_step_shows_arithmetic():
    sol = solve_quadratic("x^2 - 5x + 6 = 0", PARSER, SOLVER, Domain.REALS, "formula")
    disc = next(s for s in sol.steps if s.operation == "compute_discriminant")
    assert "=" in disc.operand and "1" in disc.operand  # 25 - 24 = 1
    formula = next(s for s in sol.steps if s.operation == "apply_quadratic_formula")
    assert "+/-" in formula.operand and "sqrt" in formula.operand


def test_flip_step_carries_teaching_note():
    sol = solve_inequality("-2x + 3 < 9", PARSER, SOLVER, Domain.REALS)
    flip = next(s for s in sol.steps if s.operation == "flip_inequality_sign")
    assert "reverse the inequality sign" in flip.explanation
    assert flip.rule == "inequality_sign_reversal"
    assert flip.operand.lstrip("-").isdigit()  # names the negative multiplier


def test_explanations_reference_their_operands():
    sol = solve_linear("2x + 5 = 17", PARSER, SOLVER, Domain.REALS)
    assert "5" in sol.steps[0].explanation
    assert "2" in sol.steps[1].explanation
