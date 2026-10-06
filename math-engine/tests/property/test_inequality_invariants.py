"""Property tests: random linear inequalities verify at their test point."""

from hypothesis import given, settings, strategies as st

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.solve_inequality import solve_inequality
from workbench_math.domain.models import Domain

PARSER = SymPyParser()
SOLVER = SymPySolver()

nonzero = st.integers(-9, 9).filter(lambda v: v != 0)
small = st.integers(-20, 20)
rels = st.sampled_from([">", "<", ">=", "<="])


@given(a=nonzero, b=small, c=small, rel=rels)
@settings(max_examples=60)
def test_random_inequality(a, b, c, rel):
    b_part = "" if b == 0 else (f" + {b}" if b > 0 else f" - {-b}")
    sol = solve_inequality(f"{a}x{b_part} {rel} {c}", PARSER, SOLVER, Domain.REALS)
    assert sol.verification == "verified"
    assert "x" in sol.exact[0]


@given(a=nonzero, b=small, c=small)
@settings(max_examples=25)
def test_negative_coefficient_always_flips(a, b, c):
    a = -abs(a)
    b_part = "" if b == 0 else (f" + {b}" if b > 0 else f" - {-b}")
    sol = solve_inequality(f"{a}x{b_part} > {c}", PARSER, SOLVER, Domain.REALS)
    assert "flip_inequality_sign" in [s.operation for s in sol.steps]
    assert sol.verification == "verified"
