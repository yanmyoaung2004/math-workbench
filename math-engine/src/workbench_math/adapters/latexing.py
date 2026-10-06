"""Presentation LaTeX: SymPy renders, the UI typesets (KaTeX), nobody hand-parses.

`latex_of` turns canonical engine strings ("2*x**2 - 7*x + 3") into LaTeX
("2 x^{2} - 7 x + 3"). Parsing is structure-preserving (evaluate=False) so
operand arithmetic like "25 - 24" survives. Anything unparseable passes
through unchanged — LaTeX must never break math delivery.

Enrichers fill the `*_latex` presentation fields on DTOs at the entrypoint
boundary (application stays presentation-free, domain stays stdlib-only).
"""

from __future__ import annotations

from dataclasses import replace

from sympy import latex as _latex

from ..domain.models import Binding, Solution, Step
from ..graph.models import AnalysisResult, FeaturePoint, TableResult
from ._sympy_common import to_sympy

_REL_OPS = (">=", "<=", "=", "<", ">")


def latex_side(text: str) -> str:
    try:
        rendered = _latex(to_sympy(text, evaluate=False))
    except Exception:
        return text
    # "1/2" parses (unevaluated) as 1*(1/2); fold the trivial leading "1 ·"
    # so fractions print cleanly. Genuine structure ("2*(x+3)") is untouched.
    if rendered.startswith("1 \\cdot "):
        return rendered[len("1 \\cdot "):]
    return rendered


def latex_of(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return t
    if ";" in t:
        return "; ".join(latex_of(part) for part in t.split(";"))
    if " or " in t:
        return r" \text{ or } ".join(latex_of(part) for part in t.split(" or "))
    padded = f" {t} "
    for op in _REL_OPS:
        if f" {op} " in padded:
            left, right = t.split(op, 1)
            return f"{latex_side(left)} {op} {latex_side(right)}"
    return latex_side(t)


def latex_step(step: Step) -> Step:
    return replace(
        step,
        before_latex=latex_of(step.before),
        after_latex=latex_of(step.after),
        operand_latex=latex_of(step.operand),
    )


def latex_solution(solution: Solution) -> Solution:
    return replace(
        solution,
        interpretation_latex=latex_of(solution.interpretation),
        exact_latex=tuple(latex_of(s) for s in solution.exact),
        steps=tuple(latex_step(s) for s in solution.steps),
        bindings=tuple(
            replace(b, exact_latex=latex_of(b.exact)) for b in solution.bindings
        ),
    )


def latex_point(point: FeaturePoint) -> FeaturePoint:
    return replace(point, exact_latex=latex_of(point.exact))


def latex_table(result: TableResult) -> TableResult:
    return replace(
        result,
        xs_latex=tuple(latex_of(x) for x in result.xs),
        ys_latex=tuple(latex_of(y) if y != "undefined" else y for y in result.ys),
    )


def latex_analysis(result: AnalysisResult) -> AnalysisResult:
    return replace(
        result,
        roots=tuple(latex_point(p) for p in result.roots),
        turning_points=tuple(latex_point(p) for p in result.turning_points),
        y_intercept=latex_point(result.y_intercept) if result.y_intercept else None,
        axis_latex=latex_of(result.axis_of_symmetry),
        gradient_latex=latex_of(result.gradient),
    )
