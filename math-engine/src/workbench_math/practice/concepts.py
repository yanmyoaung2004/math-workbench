"""Concept notes: the 'why' behind each step rule (Skemp-style grounding).

Keyed by step `rule` so the UI can attach a note to any rendered step.
Every rule in domain/steps.py EXPLANATIONS must appear here (tested).
"""

from __future__ import annotations

CONCEPTS: dict[str, str] = {
    "subtraction_property_of_equality":
        "Equals stay equal when you subtract the same amount from both sides — "
        "that is what keeps the balance while the constant disappears.",
    "addition_property_of_equality":
        "Equals stay equal when you add the same amount to both sides.",
    "division_property_of_equality":
        "Dividing both sides by the same non-zero number keeps the equality "
        "true, and leaves x standing alone.",
    "multiplication_property_of_equality":
        "Multiplying both sides by the same number keeps the equality true. "
        "It is how fractions in front of x get cleared.",
    "distributive_property":
        "a(b + c) = ab + ac: the outside multiplier reaches every term inside.",
    "combining_like_terms":
        "Only terms with exactly the same variable part can merge — the numbers "
        "add, the letters stay.",
    "equivalent_form":
        "Rewriting changes the look, never the value: both forms have the same solutions.",
    "simplification":
        "Simplify collects and cancels until nothing redundant is left.",
    "expansion":
        "Expanding removes brackets by multiplying everything out.",
    "factorisation":
        "Factorising is expanding in reverse: find what the terms share.",
    "zero_product_property":
        "If two things multiply to zero, at least one of them is zero — that is "
        "why each factor gets its own equation.",
    "standard_quadratic_form":
        "ax² + bx + c = 0 names the three numbers every quadratic method needs.",
    "discriminant":
        "b² − 4ac predicts the roots before you find them: positive means two, "
        "zero means one repeated, negative means none (real).",
    "quadratic_formula":
        "The formula solves every quadratic by completing the square once, in general.",
    "completing_the_square":
        "Adding (b/2)² builds a perfect square, turning the equation into "
        "something a square root can undo.",
    "square_root_property":
        "Both 2² and (−2)² equal 4, so undoing a square always gives two signs.",
    "elimination_method":
        "Scaling both equations to match one variable lets addition or "
        "subtraction delete it entirely.",
    "substitution_method":
        "A solved variable is a known value — putting it into the other "
        "equation leaves one unknown.",
    "inequality_sign_reversal":
        "Order flips when multiplying or dividing by a negative: on the number "
        "line, everything mirrors.",
}


def concept_for(rule: str) -> str:
    try:
        return CONCEPTS[rule]
    except KeyError as exc:
        raise KeyError(f"No concept note for rule {rule!r}.") from exc
