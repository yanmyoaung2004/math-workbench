"""Domain errors — one exception per contract error code (docs/math-engine.md §1).

Entrypoints map these to JSON `{ok:false, error:{code,message}}`. Messages are
user-facing (GCSE student reading level); no tracebacks cross the boundary.
"""

from __future__ import annotations


class MathEngineError(Exception):
    """Base. Every subclass sets `code` to a contract error code."""

    code = "INTERNAL_ERROR"


class ParseError(MathEngineError):
    code = "PARSE_ERROR"


class NoSolutionError(MathEngineError):
    code = "NO_SOLUTION"


class InfiniteSolutionsError(MathEngineError):
    code = "INFINITE_SOLUTIONS"


class UnsolvableError(MathEngineError):
    code = "UNSOLVABLE"


class DomainError(MathEngineError):
    code = "DOMAIN_ERROR"


class ValidationError(MathEngineError):
    code = "VALIDATION_ERROR"
