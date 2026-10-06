"""Domain value objects — stdlib only. Never import sympy in this package.

These are the stable contracts the UI, AI tutor, and sidecar protocol depend on
(see docs/math-engine.md). SymPy objects are translated to these DTOs at the
adapter boundary and never leak inward (ADR-0001).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Domain(Enum):
    REALS = "reals"
    COMPLEX = "complex"


class Verification(Enum):
    VERIFIED = "verified"
    UNVERIFIABLE = "unverifiable"


@dataclass(frozen=True)
class Expression:
    """A parsed user input. `canonical` is the engine's normalized form."""

    raw: str
    canonical: str
    kind: str  # "expression" | "equation"


@dataclass(frozen=True)
class Step:
    """One verifiable pedagogical transformation (product.md Step Engine)."""

    operation: str  # e.g. subtract_both_sides (see math-engine.md §5 vocabulary)
    operand: str  # canonical string of the operand
    before: str
    after: str
    rule: str  # e.g. subtraction_property_of_equality
    explanation: str  # GCSE wording, no advanced terms by default
    verification: str = Verification.VERIFIED.value


@dataclass(frozen=True)
class DomainInfo:
    domain: str
    excluded: tuple[str, ...] = ()


@dataclass(frozen=True)
class Binding:
    """One named solution value, e.g. x = 3 (systems; also filled for single)."""

    variable: str
    exact: str
    approximate: str


@dataclass(frozen=True)
class Solution:
    """Use-case output: exact + approximate kept separate (FR-ALG-5)."""

    interpretation: str
    exact: tuple[str, ...]
    approximate: tuple[str, ...]
    steps: tuple[Step, ...]
    verification: str = Verification.VERIFIED.value
    domain_info: DomainInfo = DomainInfo(domain=Domain.REALS.value)
    bindings: tuple[Binding, ...] = ()
