"""Regression: wide-viewport tan must not connect across poles.

Found by independent audit: the span-relative jump threshold alone missed real
pole crossings when the viewport span dwarfed interior jumps. Segments are now
split at known poles; this test pins that behavior permanently.
"""

import math

import pytest

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.graph.models import SampleRequest
from workbench_math.graph.sampler import sample

PARSER = SymPyParser()


def test_tan_wide_viewport_no_pole_spanning():
    res = sample(
        SampleRequest(expression="y = tan(x)", x_min=-6.28, x_max=6.28, n_points=400),
        PARSER,
    )
    assert list(res.excluded) == pytest.approx(
        [-3 * math.pi / 2, -math.pi / 2, math.pi / 2, 3 * math.pi / 2])
    assert len(res.segments) == 5
    for pole in res.excluded:
        for seg in res.segments:
            assert not (min(seg.xs) < pole < max(seg.xs)), f"segment spans pole {pole}"
