"""Geometry: formula-first steps, exact + approximate, physical validation."""

import math

import pytest

from workbench_math.domain.exceptions import ValidationError
from workbench_math.geometry.formulas import solve


def test_circle_area_exact_and_approx():
    res = solve("circle", "area", {"r": "7"})
    assert res.result_exact == "49*pi"
    assert res.result_approx == pytest.approx(49 * math.pi)
    assert [s.operation for s in res.steps] == ["state_formula", "substitute", "evaluate"]
    assert res.verification == "verified"


def test_pythagoras_and_leg():
    assert solve("right_triangle", "hypotenuse", {"a": "3", "b": "4"}).result_exact == "5"
    assert solve("right_triangle", "leg", {"c": "13", "a": "5"}).result_exact == "12"
    with pytest.raises(ValidationError):
        solve("right_triangle", "leg", {"c": "5", "a": "13"})


def test_sohcahtoa():
    assert solve("right_triangle", "opposite", {"angle_deg": "30", "hypotenuse": "10"}).result_exact == "5"
    angle = solve("right_triangle", "angle", {"opposite": "1", "hypotenuse": "2"})
    assert angle.result_exact == "30"
    with pytest.raises(ValidationError):
        solve("right_triangle", "opposite", {"angle_deg": "120", "hypotenuse": "10"})


def test_physical_validation():
    with pytest.raises(ValidationError):
        solve("circle", "area", {"r": "-7"})
    with pytest.raises(ValidationError):
        solve("circle", "volume", {"r": "7"})


def test_rectangle_and_triangle():
    assert solve("rectangle", "area", {"w": "3", "h": "1/2"}).result_exact == "3/2"
    assert solve("rectangle", "perimeter", {"w": "3", "h": "4"}).result_exact == "14"
    assert solve("triangle", "area", {"b": "5", "h": "4"}).result_exact == "10"
