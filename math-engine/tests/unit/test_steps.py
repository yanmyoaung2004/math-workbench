"""Step pedagogy: known operations, rule mapping, chain continuity."""

import pytest

from workbench_math.domain.exceptions import ValidationError
from workbench_math.domain.steps import check_chain, make_step


def test_all_linear_operations_have_gcse_wording():
    for op in ("subtract_both_sides", "add_both_sides", "divide_both_sides",
               "multiply_both_sides", "distribute", "collect_like_terms"):
        step = make_step(op, "2", "2*x + 5 = 17", "2*x = 12", symbol="x")
        assert step.rule and step.explanation
        assert "2" in step.explanation  # operand referenced, GCSE tone


def test_transform_operations_exist():
    assert make_step("simplify_expression", "", "2*x + 3*x", "5*x").rule == "simplification"
    assert make_step("expand_expression", "", "(x + 1)**2", "x**2 + 2*x + 1").rule == "expansion"
    assert make_step("factorise_expression", "", "x**2 + 2*x + 1", "(x + 1)**2").rule == "factorisation"


def test_unknown_operation_rejected():
    with pytest.raises(ValidationError):
        make_step("teleport", "2", "a", "b")


def test_empty_step_parts_rejected():
    with pytest.raises(ValidationError):
        make_step("rewrite", "", "", "x = 1")


def test_chain_continuity():
    s1 = make_step("subtract_both_sides", "5", "2*x + 5 = 17", "2*x = 12")
    s2 = make_step("divide_both_sides", "2", "2*x = 12", "x = 6")
    assert check_chain("2*x + 5 = 17", (s1, s2), "x = 6")
    assert not check_chain("2*x + 5 = 17", (s1, s2), "x = 7")  # wrong final
    assert not check_chain("2*x + 5 = 18", (s1, s2), "x = 6")  # wrong start
    broken = make_step("divide_both_sides", "2", "2*x = 11", "x = 6")
    assert not check_chain("2*x + 5 = 17", (s1, broken), "x = 6")  # gap in middle


def test_empty_chain_matches_identity_only():
    assert check_chain("x = 6", (), "x = 6")
    assert not check_chain("2*x = 12", (), "x = 6")
