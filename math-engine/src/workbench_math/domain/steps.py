"""Step construction — pedagogy lives here, algebra arrives as data.

Split of responsibilities (documented for future agents):
- adapters (SymPy side) compute the *algebraic facts*: the chain of
  (operation, operand, before, after) canonical strings.
- THIS module validates the chain and attaches the *teaching layer*:
  rule names + GCSE explanations from templates below.

That keeps SymPy out of the domain while keeping all student-facing wording in
one reviewable place (educational tests target this module).
"""

from __future__ import annotations

from .exceptions import ValidationError
from .models import Step, Verification

# operation -> (rule, explanation template). Templates take {operand} and {symbol}.
EXPLANATIONS: dict[str, tuple[str, str]] = {
    "subtract_both_sides": (
        "subtraction_property_of_equality",
        "Subtract {operand} from both sides to remove the constant term.",
    ),
    "add_both_sides": (
        "addition_property_of_equality",
        "Add {operand} to both sides to remove the constant term.",
    ),
    "divide_both_sides": (
        "division_property_of_equality",
        "Divide both sides by {operand} to isolate {symbol}.",
    ),
    "multiply_both_sides": (
        "multiplication_property_of_equality",
        "Multiply both sides by {operand} to isolate {symbol}.",
    ),
    "distribute": (
        "distributive_property",
        "Expand the brackets in {operand}.",
    ),
    "collect_like_terms": (
        "combining_like_terms",
        "Collect the like terms ({operand}) on each side.",
    ),
    "rewrite": (
        "equivalent_form",
        "Rewrite in an equivalent form.",
    ),
    "simplify_expression": (
        "simplification",
        "Simplify the expression.",
    ),
    "expand_expression": (
        "expansion",
        "Expand the brackets.",
    ),
    "factorise_expression": (
        "factorisation",
        "Factorise into irreducible factors.",
    ),
    "factorise_equation": (
        "factorisation",
        "Factorise the left-hand side: {operand}.",
    ),
    "apply_zero_product": (
        "zero_product_property",
        "Set the factor {operand} to zero and solve.",
    ),
    "identify_coefficients": (
        "standard_quadratic_form",
        "Identify a, b and c in {operand}.",
    ),
    "compute_discriminant": (
        "discriminant",
        "Compute the discriminant: {operand}.",
    ),
    "apply_quadratic_formula": (
        "quadratic_formula",
        "Apply the quadratic formula: {operand}.",
    ),
    "complete_the_square": (
        "completing_the_square",
        "Complete the square to get {operand}.",
    ),
    "take_square_root_pm": (
        "square_root_property",
        "Take the square root of both sides ({operand}), remembering both signs.",
    ),
    "scale_equation": (
        "multiplication_property_of_equality",
        "Multiply the whole equation by {operand}.",
    ),
    "eliminate_variable": (
        "elimination_method",
        "Add or subtract the equations to eliminate {operand}.",
    ),
    "substitute_back": (
        "substitution_method",
        "Substitute {operand} into the other equation.",
    ),
    "flip_inequality_sign": (
        "inequality_sign_reversal",
        "Multiply by {operand} (negative), so reverse the inequality sign.",
    ),
}

INEQUALITY_FLIP_NOTE = (
    " When multiplying or dividing an inequality by a negative number, "
    "reverse the inequality sign."
)


def make_step(
    operation: str,
    operand: str,
    before: str,
    after: str,
    symbol: str = "x",
    verification: str = Verification.VERIFIED.value,
) -> Step:
    """Build a Step with rule + explanation derived from the operation."""
    if operation not in EXPLANATIONS:
        raise ValidationError(f"Unknown step operation: {operation!r}.")
    if not before or not after:
        raise ValidationError("Step needs non-empty before/after expressions.")
    rule, template = EXPLANATIONS[operation]
    return Step(
        operation=operation,
        operand=operand,
        before=before,
        after=after,
        rule=rule,
        explanation=template.format(operand=operand, symbol=symbol),
        verification=verification,
    )


def check_chain(interpretation: str, steps: tuple[Step, ...], final: str) -> bool:
    """Structural continuity: interpretation -> s0.before -> ... -> final.

    Pure string check; mathematical validity is the verifier's job.
    """
    if not steps:
        return interpretation == final
    if steps[0].before != interpretation:
        return False
    for prev, nxt in zip(steps, steps[1:]):
        if prev.after != nxt.before:
            return False
    return steps[-1].after == final
