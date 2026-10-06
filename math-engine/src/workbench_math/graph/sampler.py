"""Function sampler: viewport → discontinuity-split segments.

Rules (product.md graph spec):
- undefined points (NaN/oo/complex) break segments — never connected;
- vertical jumps (asymptotes) split segments via a span-relative threshold;
- known poles from SymPy singularities() are reported as excluded (best effort;
  sampling never fails because of them).
"""

from __future__ import annotations

import numpy as np
from sympy import lambdify

from ..domain.exceptions import ParseError, ValidationError
from ..ports.parser_port import ParserPort
from .functions import finite_poles, resolve_function
from .models import SampleRequest, SampleResult, Segment

_MAX_POINTS = 5000


def _evaluate(fn, xs: np.ndarray) -> np.ndarray:
    """Vectorized eval with elementwise fallback; complex → nan unless real."""
    with np.errstate(all="ignore"):
        try:
            ys = fn(xs)
        except Exception:
            ys = None
    if ys is None:
        ys = np.array([np.nan] * len(xs))
    else:
        ys = np.asarray(ys, dtype=complex)
    out = np.full(len(xs), np.nan)
    real = np.isfinite(ys.real) & (np.abs(ys.imag) < 1e-9) & np.isfinite(ys.imag)
    out[real] = ys.real[real]
    if not np.any(np.isfinite(out)):
        # Vectorization may have failed opaquely (e.g. Piecewise) — retry pointwise.
        vals = []
        for xv in xs:
            try:
                with np.errstate(all="ignore"):
                    yv = complex(fn(xv))
                vals.append(yv.real if abs(yv.imag) < 1e-9 else np.nan)
            except Exception:
                vals.append(np.nan)
        out = np.array(vals)
    return out


def _split(ys: np.ndarray) -> list[int]:
    """Indices where a new segment must start (non-finite runs + jumps)."""
    finite = np.isfinite(ys)
    breaks = [0]
    span = float(np.nanmax(ys) - np.nanmin(ys)) if np.any(finite) else 0.0
    jump = max(span * 0.5, 1e-9)  # conservative: only true pole-crossings split
    for i in range(1, len(ys)):
        if not finite[i] or not finite[i - 1]:
            breaks.append(i)
        elif abs(float(ys[i]) - float(ys[i - 1])) > jump:
            breaks.append(i)
    breaks.append(len(ys))
    return breaks


def sample(request: SampleRequest, parser: ParserPort) -> SampleResult:
    if not (np.isfinite(request.x_min) and np.isfinite(request.x_max)):
        raise ValidationError("Viewport bounds must be finite numbers.")
    if not request.x_min < request.x_max:
        raise ValidationError("Viewport needs x_min < x_max.")
    if not 2 <= request.n_points <= _MAX_POINTS:
        raise ValidationError(f"Ask for 2–{_MAX_POINTS} points.")
    try:
        text, parsed, x = resolve_function(request.expression, parser)
    except (ParseError, ValidationError):
        raise
    except Exception as exc:
        raise ParseError(f"I couldn't parse {request.expression!r} for graphing.") from exc

    xs = np.linspace(request.x_min, request.x_max, request.n_points)
    try:
        fn = lambdify(x, parsed, modules="numpy")
    except Exception as exc:
        raise ValidationError("I couldn't evaluate that function for graphing.") from exc
    ys = _evaluate(fn, xs)

    breaks = _split(ys)
    segments = []
    for start, end in zip(breaks, breaks[1:]):
        mask = np.isfinite(ys[start:end])
        if not np.any(mask):
            continue
        idx = np.arange(start, end)[mask]
        segments.append(Segment(
            xs=tuple(float(v) for v in xs[idx]),
            ys=tuple(float(v) for v in ys[idx]),
        ))

    excluded = finite_poles(parsed, x, float(request.x_min), float(request.x_max))
    return SampleResult(interpretation=text, segments=tuple(segments), excluded=excluded)
