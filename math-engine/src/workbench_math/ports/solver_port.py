"""Inbound ports — ABCs the application depends on (dependency inversion).

Adapters implement these; tests fake them. Ports transfer domain DTOs and
plain data only, never SymPy objects (ADR-0001).
"""

from __future__ import annotations

import abc
from dataclasses import dataclass

from ..domain.models import Domain, Expression
from .parser_port import ParserPort

__all__ = ["LinearFacts", "QuadraticFacts", "SystemFacts", "InequalityFacts", "TransformFacts", "ParserPort", "SolverPort"]


@dataclass(frozen=True)
class LinearFacts:
    """Algebraic facts about a linear equation, computed by the adapter.

    Represents `a*symbol + b = rhs` plus the exact solution strings and the
    ordered chain of (operation, operand, before, after) canonical strings the
    domain step-builder will attach pedagogy to. `set_tag` is one of
    "finite" | "empty" | "infinite" | "condition" (mirrors the solveset Set tag).
    """

    symbol: str
    solutions: tuple[str, ...]
    approximate: tuple[str, ...]
    set_tag: str
    chain: tuple[tuple[str, str, str, str], ...]  # (op, operand, before, after)
    interpretation: str


@dataclass(frozen=True)
class TransformFacts:
    """Result of simplify | expand | factorise: before/after canonical strings."""

    interpretation: str
    before: str
    after: str


@dataclass(frozen=True)
class QuadraticFacts:
    """Algebraic facts about a quadratic equation.

    `method` is one of "factorise" | "formula" | "complete_square".
    `discriminant` is the canonical string of b^2 - 4ac. Multi-root solutions
    share one chain whose final `after` is the joined set "x = r1; x = r2".
    """

    symbol: str
    a: str
    b: str
    c: str
    discriminant: str
    solutions: tuple[str, ...]
    approximate: tuple[str, ...]
    set_tag: str
    method: str
    chain: tuple[tuple[str, str, str, str], ...]  # (op, operand, before, after)
    interpretation: str


@dataclass(frozen=True)
class SystemFacts:
    """Algebraic facts about a 2x2 linear system.

    `variables` are sorted names; `bindings` are (variable, exact, approx).
    `set_tag`: "finite" | "empty" | "infinite". The chain works on the joined
    state "eq1; eq2" so single-string steps stay continuous.
    """

    variables: tuple[str, ...]
    bindings: tuple[tuple[str, str, str], ...]
    set_tag: str
    chain: tuple[tuple[str, str, str, str], ...]  # (op, operand, before, after)
    interpretation: str


@dataclass(frozen=True)
class InequalityFacts:
    """Algebraic facts about a single-variable linear inequality.

    `relation` is the canonical input ("2*x + 3 > 9"); `phrase` is the GCSE
    solution phrase ("x > 3"); `set_tag`: "interval" | "empty" | "all" |
    "condition". `test_point` is an interior value proving the set (FR-VER-1).
    """

    symbol: str
    relation: str
    phrase: str
    set_tag: str
    test_point: str
    chain: tuple[tuple[str, str, str, str], ...]  # (op, operand, before, after)
    interpretation: str


class SolverPort(abc.ABC):
    @abc.abstractmethod
    def solve_linear(
        self, expr: Expression, domain: Domain = Domain.REALS
    ) -> LinearFacts:
        raise NotImplementedError

    @abc.abstractmethod
    def transform(self, expr: Expression, kind: str) -> TransformFacts:
        """kind: simplify | expand | factorise."""
        raise NotImplementedError

    @abc.abstractmethod
    def check_equality(
        self, lhs: str, rhs: str, symbol: str, candidate: str
    ) -> bool:
        """Independent substitution check under exact semantics (FR-VER-1)."""
        raise NotImplementedError

    @abc.abstractmethod
    def check_identity(self, before: str, after: str) -> bool:
        """Identity check for transforms: simplify(before - after) == 0."""
        raise NotImplementedError

    @abc.abstractmethod
    def check_system_equality(
        self, equations: tuple[str, ...], bindings: tuple[tuple[str, str], ...]
    ) -> bool:
        """Substitute all bindings into every equation; True iff all hold."""
        raise NotImplementedError

    @abc.abstractmethod
    def check_inequality(
        self, lhs: str, rhs: str, rel: str, symbol: str, candidate: str
    ) -> bool:
        """True iff the candidate satisfies `lhs rel rhs` (exact semantics)."""
        raise NotImplementedError

    @abc.abstractmethod
    def solve_quadratic(
        self, expr: Expression, domain: Domain = Domain.REALS, method: str = "auto"
    ) -> QuadraticFacts:
        """method: auto | factorise | formula | complete_square."""
        raise NotImplementedError

    @abc.abstractmethod
    def solve_system(
        self, exprs: tuple[Expression, ...], domain: Domain = Domain.REALS
    ) -> SystemFacts:
        """Two linear equations in two variables (V1)."""
        raise NotImplementedError

    @abc.abstractmethod
    def solve_inequality(
        self, expr: Expression, domain: Domain = Domain.REALS
    ) -> InequalityFacts:
        """Single-variable linear inequality (V1)."""
        raise NotImplementedError
