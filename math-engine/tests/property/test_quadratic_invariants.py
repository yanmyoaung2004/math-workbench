"""Property tests: integer-root quadratics always substitute true."""

from hypothesis import assume, given, settings, strategies as st

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.solve_quadratic import solve_quadratic
from workbench_math.domain.models import Domain
from workbench_math.domain.verify import solution_holds, solution_self_consistent

PARSER = SymPyParser()
SOLVER = SymPySolver()


def _quad_str(b: int, c: int) -> str:
    """Realistic form: skip zero coefficients, explicit signs (never '0x')."""
    s = "x^2"
    if b:
        s += f" + {b}x" if b > 0 else f" - {-b}x"
    if c:
        s += f" + {c}" if c > 0 else f" - {-c}"
    return s + " = 0"


@given(r1=st.integers(-6, 6), r2=st.integers(-6, 6))
@settings(max_examples=60)
def test_integer_root_quadratics(r1, r2):
    assume(not (r1 == 0 and r2 == 0))  # 0 = 0 is infinite solutions, not quadratic
    b, c = -(r1 + r2), r1 * r2
    sol = solve_quadratic(_quad_str(b, c), PARSER, SOLVER, Domain.REALS)
    assert sol.verification == "verified"
    assert sol.exact == tuple(sorted({str(r1), str(r2)}, key=str))
    for candidate in sol.exact:
        assert solution_holds(sol.interpretation, "x", candidate, SOLVER.check_equality)
    assert solution_self_consistent(sol, sol.steps[-1].after)
