"""Shared function resolution + finite-pole clipping for the graph subdomain."""

from __future__ import annotations

import numpy as np
from sympy import Interval, S, Symbol
from sympy.calculus.singularities import singularities

from ..adapters._sympy_common import to_sympy
from ..domain.exceptions import ValidationError
from ..ports.parser_port import ParserPort


def resolve_function(raw: str, parser: ParserPort) -> tuple[str, object, Symbol]:
    """Return (display_text, sympy_expr, x) for 'y = f' or bare 'f'."""
    expr = parser.parse(raw)
    text = expr.canonical
    if expr.kind == "equation":
        sides = text.split("=", 1)
        if sides[0].strip() != "y":
            raise ValidationError(
                "For graphing, enter 'y = ...' in x — e.g. y = x^2 + 1."
            )
        text = sides[1].strip()
    try:
        parsed = to_sympy(text)
    except Exception as exc:
        raise ValidationError(f"I couldn't parse {raw!r} for graphing.") from exc
    symbols = parsed.free_symbols
    if len(symbols) > 1:
        raise ValidationError("Graphs show functions of x only in V1.")
    x = next(iter(symbols)) if symbols else Symbol("x")
    if x.name != "x":
        raise ValidationError("Use x as the variable for graphing in V1.")
    return text, parsed, x


def finite_poles(parsed, x: Symbol, x_min: float, x_max: float) -> tuple[float, ...]:
    """Real poles strictly inside the viewport (best effort, never raises)."""
    try:
        poles = singularities(parsed, x, domain=S.Reals)
        if not getattr(poles, "is_FiniteSet", False):
            clipped = poles.intersect(Interval(x_min, x_max))
            poles = clipped if getattr(clipped, "is_FiniteSet", False) else S.EmptySet
        out = []
        for p in poles:
            if getattr(p, "is_real", False):
                try:
                    v = float(p)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(v) and x_min < v < x_max:
                    out.append(v)
        return tuple(sorted(out))
    except Exception:
        return ()
