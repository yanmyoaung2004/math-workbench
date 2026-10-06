"""Equation-graph connection: solving f(x) = g(x) as intersection points.

Signature feature (product.md §8): students see that solving an equation is
finding where two graphs meet. Points are verified by substitution into both
functions; parallel graphs correctly yield no points (not an error).
"""

from __future__ import annotations

from sympy import N, S, simplify, sstr
from sympy.solvers.solveset import solveset

from ..domain.exceptions import UnsolvableError, ValidationError
from ..ports.parser_port import ParserPort
from .functions import resolve_function
from .models import FeaturePoint


def intersect(expr_a: str, expr_b: str, parser: ParserPort) -> tuple[FeaturePoint, ...]:
    text_a, f, x = resolve_function(expr_a, parser)
    text_b, g, _ = resolve_function(expr_b, parser)
    _ = (text_a, text_b)
    if f.free_symbols != g.free_symbols and (f.free_symbols | g.free_symbols) != {x}:
        raise ValidationError("Intersect two functions of x in V1.")
    try:
        solutions = solveset(f - g, x, domain=S.Reals)
    except (NotImplementedError, ValueError) as exc:
        raise UnsolvableError("I couldn't find those intersections automatically.") from exc
    if solutions is S.EmptySet:
        return ()
    if not getattr(solutions, "is_FiniteSet", False):
        raise UnsolvableError("Those intersections don't reduce to points in V1.")
    points = []
    for s in solutions:
        try:
            yv = simplify(f.subs(x, s))
            if not bool(simplify(f.subs(x, s) - g.subs(x, s)) == 0):
                continue
            points.append(FeaturePoint(
                kind="intersection", x=float(N(s)), y=float(N(yv)), exact=sstr(s)))
        except Exception:
            continue
    return tuple(sorted(points, key=lambda p: p.x))
