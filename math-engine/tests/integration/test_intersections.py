"""Intersections: equation solving seen as graphs meeting."""

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.graph.intersections import intersect

PARSER = SymPyParser()


def test_line_meets_horizontal():
    pts = intersect("y = 2x + 4", "y = 10", PARSER)
    assert [(p.x, p.y) for p in pts] == [(3.0, 10.0)]
    assert pts[0].kind == "intersection" and pts[0].exact == "3"


def test_parallel_lines_no_points_not_error():
    assert intersect("y = 2x + 1", "y = 2x + 5", PARSER) == ()


def test_tangent_single_point():
    pts = intersect("y = x^2", "y = 2x - 1", PARSER)
    assert [(p.x, p.y) for p in pts] == [(1.0, 1.0)]


def test_two_points_sorted():
    pts = intersect("y = x^2 - 4x + 3", "y = 0", PARSER)
    assert [(p.x, p.y) for p in pts] == [(1.0, 0.0), (3.0, 0.0)]
