"""Linear-algebra DTOs — stdlib only (same rule as domain/graph models)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatrixStep:
    operation: str
    explanation: str
    math: str  # canonical math line shown with the explanation


@dataclass(frozen=True)
class MatrixResult:
    operation: str  # multiply | determinant | inverse | dot | cross | magnitude
    input_display: str
    result: tuple[tuple[str, ...], ...] | tuple[str, ...]
    result_latex: str = ""
    steps: tuple[MatrixStep, ...] = ()
    verification: str = "verified"
