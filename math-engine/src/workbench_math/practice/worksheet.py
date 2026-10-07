"""Deterministic worksheets: engine-generated, verified before export.

A worksheet is a seeded question set plus an answer key. Nothing reaches paper
(or PDF) that the engine hasn't solved and verified first.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..ports.parser_port import ParserPort
from ..ports.solver_port import SolverPort
from .generator import generate_questions


@dataclass(frozen=True)
class Worksheet:
    title: str
    topic: str
    difficulty: str
    seed: int
    prompts: tuple[str, ...]
    answer_key: tuple[tuple[str, ...], ...]
    with_answers: bool


def build_worksheet(topic: str, difficulty: str, n: int, seed: int,
                    with_answers: bool, title: str,
                    parser: ParserPort, solver: SolverPort) -> Worksheet:
    questions = generate_questions(topic, difficulty, n, seed, parser, solver)
    return Worksheet(
        title=title or f"{topic} — {difficulty} practice",
        topic=topic, difficulty=difficulty, seed=seed,
        prompts=tuple(q.prompt for q in questions),
        answer_key=tuple(q.expected for q in questions),
        with_answers=with_answers,
    )
