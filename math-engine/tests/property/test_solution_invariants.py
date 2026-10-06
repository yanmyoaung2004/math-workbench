"""Property tests: substitute(solution) == True across randomized linear equations."""

from fractions import Fraction

from hypothesis import given, settings, strategies as st

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.solve_linear import solve_linear
from workbench_math.domain.models import Domain
from workbench_math.domain.verify import solution_holds, solution_self_consistent

PARSER = SymPyParser()
SOLVER = SymPySolver()

nonzero = st.integers(-12, 12).filter(lambda v: v != 0)
small = st.integers(-30, 30)


@given(a=nonzero, b=small, c=small)
@settings(max_examples=60)
def test_random_linear_substitution_holds(a, b, c):
    raw = f"{a}x+{b}={c}"
    sol = solve_linear(raw, PARSER, SOLVER, Domain.REALS)
    assert sol.verification == "verified"
    expected = str(Fraction(c - b, a))
    assert sol.exact == (expected,)
    for candidate in sol.exact:
        assert solution_holds(sol.interpretation, "x", candidate, SOLVER.check_equality)
    final = sol.steps[-1].after if sol.steps else sol.interpretation
    assert solution_self_consistent(sol, final)


@given(a=nonzero, b=small, c=small)
@settings(max_examples=25)
def test_random_linear_spaced_form(a, b, c):
    raw = f"{a} * x + {b} = {c}"
    sol = solve_linear(raw, PARSER, SOLVER, Domain.REALS)
    assert sol.exact == (str(Fraction(c - b, a)),)
    assert sol.verification == "verified"
