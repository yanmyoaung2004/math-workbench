"""Geometry DTOs — stdlib only (same rule as domain/graph/linalg models)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeometryStep:
    operation: str  # state_formula | substitute | evaluate
    explanation: str
    math: str
    math_latex: str = ""


@dataclass(frozen=True)
class GeometryResult:
    shape: str
    find: str
    inputs: tuple[tuple[str, str], ...]
    result_exact: str
    result_approx: float | None
    steps: tuple[GeometryStep, ...] = ()
    verification: str = "verified"
    result_latex: str = ""
