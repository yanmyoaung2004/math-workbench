"""Content modules: spec map validity, concept coverage, glossary, examples."""

import pytest

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.solve_inequality import solve_inequality
from workbench_math.application.solve_linear import solve_linear
from workbench_math.application.solve_quadratic import solve_quadratic
from workbench_math.application.transform import transform_expression
from workbench_math.domain.models import Domain
from workbench_math.domain.steps import EXPLANATIONS
from workbench_math.practice.concepts import CONCEPTS, concept_for
from workbench_math.practice.examples import EXAMPLES, examples_for
from workbench_math.practice.glossary import GLOSSARY
from workbench_math.practice.specmap import SPEC_POINTS, resolve_spec
from workbench_math.practice.worksheet import build_worksheet

PARSER = SymPyParser()
SOLVER = SymPySolver()


def test_spec_points_all_resolve_to_known_topics():
    from workbench_math.practice.generator import DIFFICULTIES, TOPICS

    assert len(SPEC_POINTS) >= 10
    for code, entry in SPEC_POINTS.items():
        topic, difficulty, label = resolve_spec(code)
        assert topic in TOPICS and difficulty in DIFFICULTIES and label
    with pytest.raises(KeyError):
        resolve_spec("NOPE-1")


def test_every_step_rule_has_concept_note():
    rules = {rule for rule, _ in EXPLANATIONS.values()}
    assert set(CONCEPTS) == rules
    for rule, note in CONCEPTS.items():
        assert len(note) > 20
    with pytest.raises(KeyError):
        concept_for("teleportation")


def test_glossary_sane():
    assert len(GLOSSARY) >= 15
    assert "discriminant" in GLOSSARY


def test_examples_all_verify_live():
    assert len(EXAMPLES) >= 8
    for topic, prompt, op_name in EXAMPLES:
        if op_name == "solve_linear":
            sol = solve_linear(prompt, PARSER, SOLVER, Domain.REALS)
        elif op_name == "solve_quadratic":
            sol = solve_quadratic(prompt, PARSER, SOLVER, Domain.REALS)
        elif op_name == "solve_inequality":
            sol = solve_inequality(prompt, PARSER, SOLVER, Domain.REALS)
        else:
            sol = transform_expression(prompt, op_name, PARSER, SOLVER)
        assert sol.verification == "verified", prompt
    assert examples_for("quadratic")
    assert len(examples_for("all")) == len(EXAMPLES)


def test_worksheet_verified_before_export():
    sheet = build_worksheet("linear", "basic", 5, 9, True, "", PARSER, SOLVER)
    assert len(sheet.prompts) == 5 == len(sheet.answer_key)
    assert all(sheet.answer_key)
    assert "linear" in sheet.title
