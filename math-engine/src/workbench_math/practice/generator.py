"""Deterministic question generation: parameters first, engine proof after.

Architectural rule (product.md §17): the LLM never invents the mathematics.
Templates draw parameters from a seeded RNG, the engine solves + verifies, and
only verified questions ship. V1 prompts are numeric; LLM wording (re-verified)
arrives with the AI tutor. Same seed → same questions (testable, reproducible
worksheets).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from ..application.solve_linear import solve_linear
from ..application.solve_quadratic import solve_quadratic
from ..domain.exceptions import ValidationError
from ..domain.models import Domain
from ..ports.parser_port import ParserPort
from ..ports.solver_port import SolverPort

TOPICS = ("linear", "quadratic")
DIFFICULTIES = ("beginner", "basic", "intermediate", "advanced", "exam")


@dataclass(frozen=True)
class Question:
    topic: str
    difficulty: str
    prompt: str  # e.g. "3x + 7 = 25"
    expected: tuple[str, ...]  # engine-verified exact answers
    op: str  # solve_linear | solve_quadratic


def _ri(rng: random.Random, lo: int, hi: int, nonzero: bool = False) -> int:
    for _ in range(100):
        v = rng.randint(lo, hi)
        if v != 0 or not nonzero:
            return v
    return 1 if nonzero else 0


def _linear_prompt(rng: random.Random, difficulty: str) -> str:
    if difficulty == "beginner":
        b, x0 = _ri(rng, -9, 9), _ri(rng, -9, 9)
        return f"x + {b} = {x0 + b}" if b >= 0 else f"x - {-b} = {x0 + b}"
    if difficulty == "basic":
        a, x0, b = _ri(rng, 2, 5, True), _ri(rng, -9, 9), _ri(rng, -9, 9)
        c = a * x0 + b
        return f"{a}x + {b} = {c}" if b >= 0 else f"{a}x - {-b} = {c}"
    if difficulty == "intermediate":
        a, x0, b = _ri(rng, 2, 5, True), _ri(rng, -9, 9), _ri(rng, 1, 9, True)
        c = a * (x0 + b)
        return f"{a}(x + {b}) = {c}"
    if difficulty == "advanced":
        a, x0, b = _ri(rng, 2, 6, True), _ri(rng, -9, 9), _ri(rng, -9, 9)
        c = x0 + a * b
        num = f"x/{a}" if b == 0 else (f"x/{a} + {b}" if b > 0 else f"x/{a} - {-b}")
        return f"{num} = {c}"
    # exam: two-sided
    a, d = _ri(rng, 2, 6, True), _ri(rng, 2, 6, True)
    while a == d:
        d = _ri(rng, 2, 6, True)
    x0, b = _ri(rng, -9, 9), _ri(rng, -9, 9)
    e = (a - d) * x0 + b
    left = f"{a}x + {b}" if b >= 0 else f"{a}x - {-b}"
    right = f"{d}x + {e}" if e >= 0 else f"{d}x - {-e}"
    return f"{left} = {right}"


def _draw_quadratic(rng: random.Random, difficulty: str) -> str:
    if difficulty in ("beginner", "basic"):
        r1, r2 = _ri(rng, -6, 6), _ri(rng, -6, 6)
        a, b, c = 1, -(r1 + r2), r1 * r2
    elif difficulty == "intermediate":
        a = _ri(rng, 2, 3, True)
        r1, r2 = _ri(rng, -6, 6), _ri(rng, -6, 6)
        a, b, c = a, -a * (r1 + r2), a * r1 * r2
    else:
        a = _ri(rng, 1, 3, True)
        r1 = _ri(rng, -6, 6)
        extra = _ri(rng, 1, 5, True)
        a, b, c = a, -2 * a * r1, a * (r1 * r1 - extra)
    terms = []
    if a == 1:
        terms.append("x^2")
    elif a == -1:
        terms.append("-x^2")
    else:
        terms.append(f"{a}x^2")
    if b:
        terms.append(f"+ {b}x" if b > 0 else f"- {-b}x")
    if c:
        terms.append(f"+ {c}" if c > 0 else f"- {-c}")
    return " ".join(terms).replace("+ -", "- ") + " = 0"


def generate_questions(topic: str, difficulty: str, n: int, seed: int,
                       parser: ParserPort, solver: SolverPort) -> tuple[Question, ...]:
    if topic not in TOPICS:
        raise ValidationError(f"Unknown topic {topic!r}. Choose: {', '.join(TOPICS)}.")
    if difficulty not in DIFFICULTIES:
        raise ValidationError(
            f"Unknown difficulty {difficulty!r}. Choose: {', '.join(DIFFICULTIES)}.")
    if not 1 <= n <= 50:
        raise ValidationError("Ask for 1–50 questions.")
    rng = random.Random(seed)
    out: list[Question] = []
    for _ in range(n):
        if topic == "linear":
            prompt = _linear_prompt(rng, difficulty)
            sol = solve_linear(prompt, parser, solver, Domain.REALS)
            op = "solve_linear"
        else:
            prompt = _draw_quadratic(rng, difficulty)
            sol = solve_quadratic(prompt, parser, solver, Domain.REALS, "auto")
            op = "solve_quadratic"
        if sol.verification != "verified":
            raise ValidationError(
                f"Generated an unverifiable question ({prompt!r}) — this is an "
                "engine bug, please report it.")
        out.append(Question(topic=topic, difficulty=difficulty, prompt=prompt,
                            expected=sol.exact, op=op))
    return tuple(out)
