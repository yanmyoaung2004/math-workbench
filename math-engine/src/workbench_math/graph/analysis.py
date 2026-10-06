"""Graph feature analysis — every feature cross-checked against the engine.

Roots, intercepts, turning points, symmetry axes, and asymptotes are computed
symbolically and verified by substitution; nothing is hallucinated from sampled
pixels (FR-VER-2). GCSE mode hides advanced output (kept minimal here by design).
"""

from __future__ import annotations

from sympy import N, Poly, S, diff, limit, oo, simplify, sstr
from sympy.solvers.solveset import solveset

from ..adapters._sympy_common import canonical
from ..ports.parser_port import ParserPort
from .functions import finite_poles, resolve_function
from .models import AnalysisResult, FeaturePoint


def _holds_zero(f, x, candidate) -> bool:
    try:
        return bool(simplify(f.subs(x, candidate)) == 0)
    except Exception:
        return False


def analyze(expression: str, parser: ParserPort,
            x_min: float = -10.0, x_max: float = 10.0) -> AnalysisResult:
    text, f, x = resolve_function(expression, parser)

    roots: list[FeaturePoint] = []
    try:
        solutions = solveset(f, x, domain=S.Reals)
        candidates = list(solutions) if getattr(solutions, "is_FiniteSet", False) else []
    except Exception:
        candidates = []
    for r in candidates:
        if _holds_zero(f, x, r):
            try:
                roots.append(FeaturePoint(
                    kind="root", x=float(N(r)), y=0.0, exact=sstr(r)))
            except (TypeError, ValueError):
                continue

    y_intercept = None
    try:
        y0 = simplify(f.subs(x, S.Zero))
        if y0.is_real and abs(complex(N(y0)).imag) < 1e-9:
            y_intercept = FeaturePoint(
                kind="y_intercept", x=0.0, y=float(N(y0)), exact=sstr(y0))
    except Exception:
        y_intercept = None

    turning: list[FeaturePoint] = []
    try:
        df = diff(f, x)
        critical = solveset(df, x, domain=S.Reals)
        points = list(critical) if getattr(critical, "is_FiniteSet", False) else []
    except Exception:
        points = []
    for c in points:
        try:
            second = simplify(diff(f, x, 2).subs(x, c))
            if second == 0 or not second.is_real:
                continue  # inflection or undecidable — not a turning point
            yv = simplify(f.subs(x, c))
            turning.append(FeaturePoint(
                kind="turning_point", x=float(N(c)), y=float(N(yv)), exact=sstr(c)))
        except Exception:
            continue

    axis = ""
    try:
        poly = Poly(f, x)
        if poly.degree() == 2:
            a, b = poly.all_coeffs()[0], poly.all_coeffs()[1]
            axis = f"x = {sstr(-b / (2 * a))}"
    except Exception:
        axis = ""

    vertical = finite_poles(f, x, x_min, x_max)

    horizontal = ""
    try:
        lp, lm = limit(f, x, oo), limit(f, x, -oo)
        parts = []
        if getattr(lp, "is_finite", False):
            parts.append(f"y -> {sstr(lp)} as x -> +inf")
        if getattr(lm, "is_finite", False):
            parts.append(f"y -> {sstr(lm)} as x -> -inf")
        if len(parts) == 2 and lp == lm:
            horizontal = f"y = {sstr(lp)}"
        else:
            horizontal = "; ".join(parts)
    except Exception:
        horizontal = ""

    try:
        gradient = canonical(diff(f, x))
    except Exception:
        gradient = ""

    return AnalysisResult(
        interpretation=text,
        roots=tuple(sorted(roots, key=lambda p: p.x)),
        y_intercept=y_intercept,
        turning_points=tuple(sorted(turning, key=lambda p: p.x)),
        axis_of_symmetry=axis,
        vertical_asymptotes=vertical,
        horizontal_asymptote=horizontal,
        gradient=gradient,
    )
