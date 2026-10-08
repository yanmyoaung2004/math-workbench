"""Property: differentiate-then-integrate round-trips on random polynomials."""

from hypothesis import given, settings, strategies as st

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.calculus import (
    differentiate_expression,
    integrate_expression,
)

PARSER = SymPyParser()
SOLVER = SymPySolver()


def _poly_str(coeffs):
    terms = []
    for power, coeff in enumerate(reversed(coeffs)):
        if coeff == 0:
            continue
        if power == 0:
            terms.append(f"{coeff}")
        elif power == 1:
            terms.append(f"{coeff}*x")
        else:
            terms.append(f"{coeff}*x^{power}")
    return " + ".join(terms).replace("+ -", "- ")


@given(coeffs=st.lists(st.integers(-5, 5), min_size=2, max_size=4))
@settings(max_examples=40)
def test_diff_then_integrate_round_trip(coeffs):
    assume_nonzero = any(coeffs[:-1])
    if not assume_nonzero:
        return
    raw = _poly_str(coeffs)
    derived = differentiate_expression(raw, PARSER, SOLVER)
    assert derived.verification == "verified"
    restored = integrate_expression(derived.exact[0], PARSER, SOLVER)
    assert restored.verification == "verified"
    # Antiderivative of the derivative recovers the polynomial up to a
    # constant — so differentiating the difference must give exactly 0.
    gap = differentiate_expression(
        f"({restored.exact[0].replace(' + C', '')}) - ({raw})", PARSER, SOLVER)
    assert gap.verification == "verified"
    assert gap.exact == ("0",)
