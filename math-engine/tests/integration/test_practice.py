"""Practice generator: determinism, 100% engine verification, validation."""

import pytest

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.solve_linear import solve_linear
from workbench_math.application.solve_quadratic import solve_quadratic
from workbench_math.domain.exceptions import ValidationError
from workbench_math.domain.models import Domain
from workbench_math.practice.generator import DIFFICULTIES, TOPICS, generate_questions

PARSER = SymPyParser()
SOLVER = SymPySolver()


def test_same_seed_same_paper():
    first = generate_questions("linear", "basic", 5, 42, PARSER, SOLVER)
    second = generate_questions("linear", "basic", 5, 42, PARSER, SOLVER)
    assert [q.prompt for q in first] == [q.prompt for q in second]
    assert generate_questions("linear", "basic", 5, 7, PARSER, SOLVER)[0] != first[0]


@pytest.mark.parametrize("topic", list(TOPICS))
@pytest.mark.parametrize("difficulty", list(DIFFICULTIES))
def test_every_generated_question_verifies(topic, difficulty):
    questions = generate_questions(topic, difficulty, 4, 1234, PARSER, SOLVER)
    assert len(questions) == 4
    for question in questions:
        if question.op == "solve_linear":
            sol = solve_linear(question.prompt, PARSER, SOLVER, Domain.REALS)
        else:
            sol = solve_quadratic(question.prompt, PARSER, SOLVER, Domain.REALS)
        assert sol.verification == "verified"
        assert sol.exact == question.expected


def test_validation():
    with pytest.raises(ValidationError):
        generate_questions("calculus", "basic", 1, 0, PARSER, SOLVER)
    with pytest.raises(ValidationError):
        generate_questions("linear", "impossible", 1, 0, PARSER, SOLVER)
    with pytest.raises(ValidationError):
        generate_questions("linear", "basic", 0, 0, PARSER, SOLVER)
