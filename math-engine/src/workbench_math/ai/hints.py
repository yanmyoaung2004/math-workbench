"""Deterministic hint ladder L1→L5 built from verified steps (no LLM needed).

L1 conceptual question, L2 operational nudge, L3 explicit instruction (the
step's own explanation), L4 next-step reveal, L5 full solution. Hints address
one step at a time (`step_index`, default 0); L1–L3 never leak the answer.
"""

from __future__ import annotations

from ..domain.exceptions import ValidationError
from ..domain.models import Solution

_READABLE = {
    "subtract_both_sides": "subtraction", "add_both_sides": "addition",
    "divide_both_sides": "division", "multiply_both_sides": "multiplication",
    "distribute": "expansion", "collect_like_terms": "collecting",
    "factorise_equation": "factorisation", "apply_zero_product": "zero-product",
    "identify_coefficients": "coefficient check", "compute_discriminant": "discriminant check",
    "apply_quadratic_formula": "formula substitution",
    "complete_the_square": "square completion",
    "take_square_root_pm": "square-rooting", "scale_equation": "scaling",
    "eliminate_variable": "elimination", "substitute_back": "substitution",
    "flip_inequality_sign": "sign flip", "rewrite": "rewriting",
    "simplify_expression": "simplification", "expand_expression": "expansion",
    "factorise_expression": "factorisation",
}


def hint(solution: Solution, level: int, step_index: int = 0) -> str:
    if level not in (1, 2, 3, 4, 5):
        raise ValidationError("Hint level must be 1–5.")
    if not solution.steps:
        if level >= 5:
            return f"The answer is already shown: {solution.interpretation}."
        raise ValidationError("There are no steps to hint at.")
    if not 0 <= step_index < len(solution.steps):
        raise ValidationError("That step is out of range.")
    step = solution.steps[step_index]
    symbol = _symbol_guess(solution)
    if level == 1:
        return (
            f"Look at {step.before}. What is stopping {symbol} from being "
            "alone on its side?"
        )
    if level == 2:
        return (
            f"Try {_READABLE.get(step.operation, 'the next operation')} — "
            "what happens if you apply it to both sides?"
        )
    if level == 3:
        return step.explanation
    if level == 4:
        return f"Do this step: {step.before} becomes {step.after}."
    tail = " Then: " + "; ".join(
        f"{s.before} becomes {s.after}" for s in solution.steps[step_index + 1:]
    ) if step_index + 1 < len(solution.steps) else ""
    answer = ", ".join(solution.exact) if solution.exact else solution.interpretation
    return f"Full working: {step.before} becomes {step.after}.{tail} Answer: {answer}."


def _symbol_guess(solution: Solution) -> str:
    if solution.bindings:
        return solution.bindings[0].variable
    for token in solution.interpretation.replace("=", " ").split():
        if token.isalpha() and len(token) == 1:
            return token
    return "x"
