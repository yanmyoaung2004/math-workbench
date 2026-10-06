"""GCSE input parser: implicit multiplication, `^` power, fractions/decimals.

Examples handled: "2x + 5 = 17", "x^2", "3(x+1)", "1/2 + 0.5", "sqrt(2)", "pi/3".
Equations are detected by a single '=' and each side is canonicalized so the UI
can echo the interpretation back (FR-IN-2) instead of silently misreading input.

The canonical form preserves the student's written structure (parsed with
evaluate=False, so "2(x+3)" is NOT silently expanded) — the solver expands
explicitly and records it as a distribute step.
"""

from __future__ import annotations

from ..domain.exceptions import ParseError
from ..domain.models import Expression
from ..ports.parser_port import ParserPort
from ._sympy_common import canonical, has_bracket_product, to_sympy


def _display(text: str) -> str:
    """Student-facing form: preserve written structure only when it carries
    teaching value (a bracket product like "2*(x + 3)"); otherwise show the
    evaluated normal form (so "x - 4" never echoes as "x - 1*4")."""
    unevaluated = to_sympy(text, evaluate=False)
    if has_bracket_product(unevaluated):
        return canonical(unevaluated)
    return canonical(to_sympy(text))


class SymPyParser(ParserPort):
    def parse(self, raw: str) -> Expression:
        if not raw or not raw.strip():
            raise ParseError("Please enter a mathematical expression or equation.")
        text = raw.strip()
        if "=" in text:
            parts = text.split("=")
            if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
                raise ParseError(
                    f"I couldn't parse {raw!r}. An equation needs exactly one "
                    "'=' with mathematics on both sides, e.g. 2x + 5 = 17."
                )
            lhs = _display(parts[0])
            rhs = _display(parts[1])
            return Expression(raw=raw, canonical=f"{lhs} = {rhs}", kind="equation")
        return Expression(raw=raw, canonical=_display(text), kind="expression")
