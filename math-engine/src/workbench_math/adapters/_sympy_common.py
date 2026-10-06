"""Shared SymPy plumbing for adapters — the ONLY module (plus its users in this
package) that may import sympy. Importing anything from here elsewhere breaks
the architecture test (tests/unit/test_architecture.py).

Security note: `parse_expr` uses `eval` under the hood, so raw input is treated
as untrusted: length cap + token blacklist + exception mapping to ParseError.
Residual risk (namespace probing via crafted names) is accepted for V1a local
use; sandboxing (e.g. dedicated global_dict lockdown) is a Phase-hardening item.
"""

from __future__ import annotations

from tokenize import TokenError

from sympy import Abs, Add, E, Mul, cos, exp, log, pi, sin, sqrt, sstr, tan
from sympy.core.traversal import preorder_traversal
from sympy.core.sympify import SympifyError
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from ..domain.exceptions import ParseError

TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

LOCAL_DICT = {
    "pi": pi,
    "E": E,
    "sqrt": sqrt,
    "sin": sin,
    "cos": cos,
    "tan": tan,
    "log": log,
    "exp": exp,
    "Abs": Abs,
    "abs": Abs,
}

MAX_INPUT_LEN = 500
_BLOCKED_TOKENS = ("__", "import", "lambda", "exec", "eval", "open", ";", "\n")


def to_sympy(text: str, evaluate: bool = True):
    """Parse one side/expression string into a SymPy object.

    `evaluate=False` preserves the student's written structure (e.g. "2*(x + 3)"
    stays factored) for display; the default evaluates for computation.
    Raises ParseError (user-facing message) on anything unparseable.
    """
    cleaned = text.strip()
    if not cleaned:
        raise ParseError("I couldn't find any mathematics to parse — the input is empty.")
    if len(cleaned) > MAX_INPUT_LEN:
        raise ParseError(
            f"That input is too long ({len(cleaned)} characters; limit {MAX_INPUT_LEN}). "
            "Try a shorter expression."
        )
    lowered = cleaned.lower()
    if any(tok in lowered for tok in _BLOCKED_TOKENS):
        raise ParseError(
            f"I couldn't parse {cleaned!r}. Only ordinary mathematical notation "
            "is supported (no code or statements)."
        )
    try:
        return parse_expr(
            cleaned, local_dict=dict(LOCAL_DICT), transformations=TRANSFORMATIONS,
            evaluate=evaluate,
        )
    except (
        SympifyError, SyntaxError, TypeError, ValueError, AttributeError, KeyError,
        TokenError, MemoryError, RecursionError,
    ) as exc:
        raise ParseError(
            f"I couldn't parse {cleaned!r}. Check brackets, operators and "
            "spelling, then try again."
        ) from exc


def canonical(expr) -> str:
    """Normalized display form (SymPy sstr)."""
    return sstr(expr)


def eq_str(lhs, rhs) -> str:
    """Equation display form 'lhs = rhs' (sstr(Eq) would give 'Eq(lhs, rhs)')."""
    return f"{canonical(lhs)} = {canonical(rhs)}"


def has_bracket_product(node) -> bool:
    """True iff the (unevaluated) tree multiplies a multi-term sum, e.g. 2*(x+3).

    Structural check — immune to false positives from function calls like
    sqrt(2), which contain brackets but no Mul-over-Add.
    """
    try:
        return any(
            isinstance(sub, Mul)
            and any(isinstance(arg, Add) and len(arg.args) > 1 for arg in sub.args)
            for sub in preorder_traversal(node)
        )
    except Exception:
        return False
