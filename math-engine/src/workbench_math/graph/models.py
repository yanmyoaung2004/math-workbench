"""Graph subdomain DTOs — stdlib only (same rule as domain/).

The sampler/analysis in this package may import sympy+numpy (like adapters/),
but these DTOs stay plain so the sidecar protocol and future renderers depend
on data, never on symbolic objects. See docs/architecture.md §graph.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SampleRequest:
    expression: str  # "y = x^2 + 1" or bare "x^2 + 1" (single variable x)
    x_min: float = -10.0
    x_max: float = 10.0
    n_points: int = 400


@dataclass(frozen=True)
class Segment:
    xs: tuple[float, ...]
    ys: tuple[float, ...]


@dataclass(frozen=True)
class SampleResult:
    interpretation: str
    segments: tuple[Segment, ...]
    excluded: tuple[float, ...] = ()  # poles inside the viewport (never connected)


@dataclass(frozen=True)
class FeaturePoint:
    kind: str  # root | y_intercept | turning_point | intersection
    x: float
    y: float
    exact: str = ""
    exact_latex: str = ""


@dataclass(frozen=True)
class AnalysisResult:
    interpretation: str
    roots: tuple[FeaturePoint, ...]
    y_intercept: FeaturePoint | None
    turning_points: tuple[FeaturePoint, ...]
    axis_of_symmetry: str = ""
    vertical_asymptotes: tuple[float, ...] = ()
    horizontal_asymptote: str = ""
    gradient: str = ""
    axis_latex: str = ""
    gradient_latex: str = ""


@dataclass(frozen=True)
class TableResult:
    interpretation: str
    xs: tuple[str, ...]  # exact strings
    ys: tuple[str, ...]  # exact strings (or "undefined")
    ys_approx: tuple[float | None, ...]
    xs_latex: tuple[str, ...] = ()
    ys_latex: tuple[str, ...] = ()
