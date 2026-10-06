"""Table of values: Fraction-exact start/end/step, engine-evaluated cells.

x values stay exact Rationals end-to-end, so y cells keep SymPy exacts
("1/2", "sqrt(2)") with floats only in the parallel approximate column.
"""

from __future__ import annotations

from fractions import Fraction

from sympy import N, Rational, S, sstr

from ..domain.exceptions import ValidationError
from ..ports.parser_port import ParserPort
from .functions import resolve_function
from .models import TableResult

_MAX_ROWS = 1001


def _fraction(label: str, value: str) -> Fraction:
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValidationError(
            f"Table {label} must be a number like -3, 1/2 or 0.5 (got {value!r})."
        ) from exc


def table_values(expression: str, start: str, end: str, step: str,
                 parser: ParserPort) -> TableResult:
    lo, hi, st = _fraction("start", start), _fraction("end", end), _fraction("step", step)
    if st == 0:
        raise ValidationError("Table step cannot be zero.")
    if (hi - lo) * st < 0:
        raise ValidationError("Table step points away from end — check the signs.")
    n = int((hi - lo) / st) + 1
    if n > _MAX_ROWS:
        raise ValidationError(f"That table would have {n} rows (limit {_MAX_ROWS}).")
    text, f, x = resolve_function(expression, parser)
    xs, ys, approx = [], [], []
    for i in range(n):
        q = lo + st * i
        xs.append(str(q))
        try:
            y = f.subs(x, Rational(q.numerator, q.denominator))
            if y.has(S.ComplexInfinity, S.Infinity, S.NegativeInfinity, S.NaN):
                raise ValueError("undefined")
            exact = sstr(y)
            num = complex(N(y))
            if num.imag != 0 or num.real != num.real or abs(num.real) == float("inf"):
                raise ValueError("undefined")
            ys.append(exact)
            approx.append(float(num.real))
        except Exception:
            ys.append("undefined")
            approx.append(None)
    return TableResult(interpretation=text, xs=tuple(xs), ys=tuple(ys),
                       ys_approx=tuple(approx))
