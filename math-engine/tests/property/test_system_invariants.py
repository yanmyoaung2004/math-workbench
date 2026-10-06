"""Property tests: random 2x2 systems with planted solutions verify."""

from hypothesis import assume, given, settings, strategies as st

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.solve_system import solve_system
from workbench_math.domain.models import Domain
from workbench_math.domain.verify import solution_self_consistent, system_holds

PARSER = SymPyParser()
SOLVER = SymPySolver()

coef = st.integers(-6, 6)
small = st.integers(-6, 6)


def _eq(a, b, c):
    """Realistic form: skip zero terms (never emits '0x', which is not valid input)."""
    parts = []
    if a:
        parts.append(f"{a}x")
    if b:
        parts.append(f"{b}y")
    return " + ".join(parts).replace("+ -", "- ") + f" = {c}"


@given(a1=coef, b1=coef, c1=coef, a2=coef, b2=coef, c2=coef)
@settings(max_examples=60)
def test_random_system_round_trip(a1, b1, c1, a2, b2, c2):
    assume(a1 * b2 - a2 * b1 != 0)  # unique solution (nonzero determinant)
    assume((a1, b1) != (0, 0) and (a2, b2) != (0, 0))
    sol = solve_system([_eq(a1, b1, c1), _eq(a2, b2, c2)], PARSER, SOLVER, Domain.REALS)
    assert sol.verification == "verified"
    plain = tuple((b.variable, b.exact) for b in sol.bindings)
    assert system_holds(
        (sol.interpretation.split("; ")[0], sol.interpretation.split("; ")[1]),
        plain, SOLVER.check_system_equality,
    )
    assert solution_self_consistent(sol, sol.steps[-1].after)


@given(x0=small, y0=small, a1=coef, b1=coef, a2=coef, b2=coef)
@settings(max_examples=40)
def test_planted_solution_recovered(x0, y0, a1, b1, a2, b2):
    assume(a1 * b2 - a2 * b1 != 0)
    assume((a1, b1) != (0, 0) and (a2, b2) != (0, 0))
    c1, c2 = a1 * x0 + b1 * y0, a2 * x0 + b2 * y0
    sol = solve_system([_eq(a1, b1, c1), _eq(a2, b2, c2)], PARSER, SOLVER, Domain.REALS)
    got = {b.variable: b.exact for b in sol.bindings}
    assert got == {"x": str(x0), "y": str(y0)}
    assert sol.verification == "verified"
