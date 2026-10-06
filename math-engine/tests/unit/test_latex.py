"""Presentation LaTeX: SymPy renders, nothing is hand-parsed, never breaks math."""

from workbench_math.adapters.latexing import latex_of, latex_solution
from workbench_math.domain.models import Solution
from workbench_math.domain.steps import make_step


def test_powers_fractions_roots():
    assert latex_of("2*x**2 - 7*x + 3") == "2 x^{2} - 7 x + 3"
    assert latex_of("x = 1/2") == "x = \\frac{1}{2}"
    assert latex_of("sqrt(2)") == "\\sqrt{2}"
    assert latex_of("-sqrt(2)") == "- \\sqrt{2}"


def test_equations_joined_sets_branches():
    assert latex_of("2*x + 5 = 17") == "2 x + 5 = 17"
    assert latex_of("x > 3") == "x > 3"
    assert latex_of("x = 2; x = 3") == "x = 2; x = 3"
    branched = latex_of("x + 3 = 2 or x + 3 = -2")
    assert "\\text{ or }" in branched and "x + 3 = 2" in branched


def test_operand_arithmetic_survives():
    assert latex_of("25 - 24 = 1") == "25 - 24 = 1"
    assert latex_of("(x - 3)*(2*x - 1) = 0") == (
        "\\left(x - 3\\right) \\left(2 x - 1\\right) = 0")


def test_mid_expression_fractions_fold_cleanly():
    assert latex_of("x/2 + 1/3 = 5/6") == (
        "\\frac{x}{2} + \\frac{1}{3} = \\frac{5}{6}")
    # ...but genuine coefficients are never eaten:
    assert latex_of("21*x = 42") == "21 x = 42"


def test_garbage_passes_through_unchanged():
    assert latex_of("@@@not math@@@") == "@@@not math@@@"
    assert latex_of("") == ""


def test_solution_enrichment_keeps_math_intact():
    sol = Solution(
        interpretation="2*x + 5 = 17", exact=("6",), approximate=("6.0",),
        steps=(make_step("divide_both_sides", "2", "2*x = 12", "x = 6"),),
    )
    rich = latex_solution(sol)
    assert rich.interpretation == sol.interpretation  # math untouched
    assert rich.interpretation_latex == "2 x + 5 = 17"
    assert rich.exact_latex == ("6",)
    assert rich.steps[0].before_latex == "2 x = 12"
    assert rich.steps[0].after_latex == "x = 6"
