"""Graph analysis: engine-computed features, cross-checked by substitution."""

import pytest

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.graph.analysis import analyze

PARSER = SymPyParser()


def test_quadratic_full_analysis():
    res = analyze("y = x^2 - 4x + 3", PARSER)
    assert [(p.x, p.y) for p in res.roots] == [(1.0, 0.0), (3.0, 0.0)]
    assert [p.exact for p in res.roots] == ["1", "3"]
    assert (res.y_intercept.x, res.y_intercept.y) == (0.0, 3.0)
    assert [(p.x, p.y) for p in res.turning_points] == [(2.0, -1.0)]
    assert res.axis_of_symmetry == "x = 2"
    assert res.gradient == "2*x - 4"
    assert res.vertical_asymptotes == ()


def test_reciprocal_asymptotes():
    res = analyze("y = 1/x", PARSER)
    assert res.roots == ()
    assert res.y_intercept is None
    assert res.vertical_asymptotes == (0.0,)
    assert res.horizontal_asymptote == "y = 0"


def test_line_root_no_turning():
    res = analyze("y = 2x + 3", PARSER)
    assert [(p.x, p.y) for p in res.roots] == [(-1.5, 0.0)]
    assert res.turning_points == ()
    assert res.axis_of_symmetry == ""
    assert res.gradient == "2"


def test_cubic_inflection_not_turning_point():
    res = analyze("y = x^3", PARSER)
    assert [(p.x, p.y) for p in res.roots] == [(0.0, 0.0)]
    assert res.turning_points == ()  # x=0 is inflection, correctly skipped


def test_bare_expression_accepted():
    res = analyze("x^2 + 1", PARSER)
    assert res.roots == ()
    assert res.y_intercept.y == pytest.approx(1.0)
