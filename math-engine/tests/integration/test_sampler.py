"""Graph sampler: segments, discontinuities, poles, validation."""

import pytest

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.domain.exceptions import ValidationError
from workbench_math.graph.models import SampleRequest
from workbench_math.graph.sampler import sample

PARSER = SymPyParser()


def req(expr, x_min=-10.0, x_max=10.0, n=400):
    return SampleRequest(expression=expr, x_min=x_min, x_max=x_max, n_points=n)


def test_parabola_single_segment_endpoints():
    res = sample(req("y = x^2", -5, 5), PARSER)
    assert len(res.segments) == 1
    xs, ys = res.segments[0].xs, res.segments[0].ys
    assert xs[0] == pytest.approx(-5.0) and xs[-1] == pytest.approx(5.0)
    assert ys[0] == pytest.approx(25.0) and min(ys) == pytest.approx(0.0, abs=0.05)
    assert res.excluded == ()


def test_reciprocal_never_connects_across_pole():
    res = sample(req("y = 1/x", -5, 5), PARSER)
    assert len(res.segments) == 2
    left, right = res.segments
    assert max(left.xs) < 0 < min(right.xs)
    assert all(y < 0 for y in left.ys) and all(y > 0 for y in right.ys)
    assert res.excluded == (0.0,)


def test_tangent_breaks_at_asymptotes():
    import math

    res = sample(req("y = tan(x)", -math.pi, math.pi, n=800), PARSER)
    assert len(res.segments) >= 3
    assert res.excluded == pytest.approx((-math.pi / 2, math.pi / 2))
    for seg in res.segments:
        assert all(abs(y) < 1e6 for y in seg.ys)


def test_sqrt_domain_cut():
    res = sample(req("y = sqrt(x)", -4, 4), PARSER)
    assert len(res.segments) == 1
    assert min(res.segments[0].xs) >= 0.0
    assert res.segments[0].ys[0] == pytest.approx(0.0, abs=0.15)


def test_bare_expression_and_caret():
    res = sample(req("x^2 + 1", -2, 2, n=50), PARSER)
    assert len(res.segments) == 1
    assert res.interpretation == "x**2 + 1"


def test_validation():
    with pytest.raises(ValidationError):
        sample(req("y = x + 1", 5, -5), PARSER)  # inverted viewport
    with pytest.raises(ValidationError):
        sample(req("y = x + 1", -5, 5, n=1), PARSER)  # too few points
    with pytest.raises(ValidationError):
        sample(req("z = y + 1", -5, 5), PARSER)  # not y-in-x
    with pytest.raises(ValidationError):
        sample(req("y = x + t", -5, 5), PARSER)  # two variables
