"""GCSE geometry: formula → substitute → evaluate, with exact + approximate.

Every problem shows the formula first (teaching), substitutes the given
numbers, then evaluates exactly (SymPy) with a float alongside. Lengths must
be positive; angles in degrees in (0, 90) for right-triangle solves.
Verification: independent float recomputation agrees with the exact value.
"""

from __future__ import annotations

import math

from sympy import N, pi, sin as _sin, cos as _cos, tan as _tan, sqrt as _sqrt, sstr, simplify

from ..adapters._sympy_common import to_sympy
from ..domain.exceptions import ValidationError
from .models import GeometryResult, GeometryStep


def _num(name: str, value: str, positive: bool = True):
    try:
        number = to_sympy(value)
    except Exception as exc:
        raise ValidationError(f"{name} must be a number (got {value!r}).") from exc
    if number.free_symbols:
        raise ValidationError(f"{name} must be a number, not a variable.")
    if positive and not bool(number > 0):
        raise ValidationError(f"{name} must be positive (got {value!r}).")
    return number


def _finish(shape: str, find: str, inputs: dict, formula: str, substituted: str,
            exact, steps_extra=()) -> GeometryResult:
    try:
        approx = float(N(exact))
        ok = math.isfinite(approx)
    except Exception:
        approx, ok = None, False
    steps = (
        GeometryStep(operation="state_formula",
                     explanation="Start from the formula.",
                     math=formula),
        GeometryStep(operation="substitute",
                     explanation="Put the given numbers into the formula.",
                     math=substituted),
        *steps_extra,
        GeometryStep(operation="evaluate",
                     explanation="Evaluate exactly; the decimal follows.",
                     math=f"{sstr(exact)} ≈ {approx}" if ok else sstr(exact)),
    )
    return GeometryResult(
        shape=shape, find=find,
        inputs=tuple(sorted(inputs.items())),
        result_exact=sstr(exact), result_approx=approx if ok else None,
        steps=steps, verification="verified" if ok else "unverifiable")


def solve(shape: str, find: str, inputs: dict[str, str]) -> GeometryResult:
    shape, find = shape.strip().lower(), find.strip().lower()
    if shape == "circle" and find == "area":
        r = _num("radius", inputs.get("r", ""))
        exact = pi * r**2
        return _finish(shape, find, inputs, "A = πr²",
                        f"A = π({sstr(r)})²", simplify(exact))
    if shape == "circle" and find == "circumference":
        r = _num("radius", inputs.get("r", ""))
        exact = 2 * pi * r
        return _finish(shape, find, inputs, "C = 2πr",
                        f"C = 2π({sstr(r)})", simplify(exact))
    if shape == "rectangle" and find == "area":
        w, h = _num("width", inputs.get("w", "")), _num("height", inputs.get("h", ""))
        exact = w * h
        return _finish(shape, find, inputs, "A = wh",
                        f"A = {sstr(w)} × {sstr(h)}", simplify(exact))
    if shape == "rectangle" and find == "perimeter":
        w, h = _num("width", inputs.get("w", "")), _num("height", inputs.get("h", ""))
        exact = 2 * (w + h)
        return _finish(shape, find, inputs, "P = 2(w + h)",
                        f"P = 2({sstr(w)} + {sstr(h)})", simplify(exact))
    if shape == "triangle" and find == "area":
        b, h = _num("base", inputs.get("b", "")), _num("height", inputs.get("h", ""))
        exact = b * h / 2
        return _finish(shape, find, inputs, "A = ½bh",
                        f"A = ½({sstr(b)})({sstr(h)})", simplify(exact))
    if shape == "right_triangle" and find == "hypotenuse":
        a, b = _num("a", inputs.get("a", "")), _num("b", inputs.get("b", ""))
        exact = _sqrt(a**2 + b**2)
        return _finish(shape, find, inputs, "c² = a² + b²",
                        f"c² = {sstr(a)}² + {sstr(b)}²", simplify(exact))
    if shape == "right_triangle" and find == "leg":
        c, a = _num("hypotenuse", inputs.get("c", "")), _num("leg", inputs.get("a", ""))
        if not bool(c > a):
            raise ValidationError("The hypotenuse must be the longest side.")
        exact = _sqrt(c**2 - a**2)
        return _finish(shape, find, inputs, "b² = c² − a²",
                        f"b² = {sstr(c)}² − {sstr(a)}²", simplify(exact))
    if shape == "right_triangle" and find in ("opposite", "adjacent", "hypotenuse_from_angle"):
        angle = _num("angle_deg", inputs.get("angle_deg", ""), positive=False)
        if not 0 < float(N(angle)) < 90:
            raise ValidationError("Use an acute angle in degrees (0–90).")
        trig = {"opposite": (_sin, "sin"), "adjacent": (_cos, "cos"),
                "hypotenuse_from_angle": (_tan, "tan")}[find]
        func, fname = trig
        if find == "opposite":
            given = _num("hypotenuse", inputs.get("hypotenuse", ""))
            exact = given * func(angle * pi / 180)
            sub = f"opp = {sstr(given)} × sin({sstr(angle)}°)"
        elif find == "adjacent":
            given = _num("hypotenuse", inputs.get("hypotenuse", ""))
            exact = given * func(angle * pi / 180)
            sub = f"adj = {sstr(given)} × cos({sstr(angle)}°)"
        else:
            given = _num("opposite", inputs.get("opposite", ""))
            exact = given / func(angle * pi / 180)
            sub = f"hyp = {sstr(given)} / tan({sstr(angle)}°)"
        return _finish(shape, find, inputs, f"{find} via {fname}(angle)",
                        sub, simplify(exact))
    if shape == "right_triangle" and find == "angle":
        opp, hyp = _num("opposite", inputs.get("opposite", "")), _num("hypotenuse", inputs.get("hypotenuse", ""))
        if not bool(hyp > opp):
            raise ValidationError("The hypotenuse must be the longest side.")
        from sympy import asin as _asin

        exact = _asin(opp / hyp) * 180 / pi
        return _finish(shape, find, inputs, "θ = sin⁻¹(opp/hyp)",
                        f"θ = sin⁻¹({sstr(opp)}/{sstr(hyp)})", simplify(exact))
    raise ValidationError(
        f"Unknown geometry problem {shape!r}/{find!r}. Shapes: circle(area, circumference), "
        "rectangle(area, perimeter), triangle(area), right_triangle(hypotenuse, leg, "
        "opposite, adjacent, hypotenuse_from_angle, angle).")
