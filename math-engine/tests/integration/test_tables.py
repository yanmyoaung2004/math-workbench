"""Tables: exact cells, undefined handling, row caps."""

import pytest

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.domain.exceptions import ValidationError
from workbench_math.graph.tables import table_values

PARSER = SymPyParser()


def test_parabola_table():
    res = table_values("y = x^2 - 2", "-3", "3", "1", PARSER)
    assert list(res.xs) == ["-3", "-2", "-1", "0", "1", "2", "3"]
    assert list(res.ys) == ["7", "2", "-1", "-2", "-1", "2", "7"]
    assert list(res.ys_approx) == [7.0, 2.0, -1.0, -2.0, -1.0, 2.0, 7.0]


def test_fractional_step_stays_exact():
    res = table_values("y = x/2", "0", "1", "1/2", PARSER)
    assert list(res.xs) == ["0", "1/2", "1"]
    assert list(res.ys) == ["0", "1/4", "1/2"]


def test_undefined_cells_flagged():
    res = table_values("y = 1/x", "-1", "1", "1", PARSER)
    assert list(res.ys) == ["-1", "undefined", "1"]
    assert res.ys_approx[1] is None


def test_caps_and_signs():
    with pytest.raises(ValidationError):
        table_values("y = x", "0", "10", "0", PARSER)  # zero step
    with pytest.raises(ValidationError):
        table_values("y = x", "0", "10", "-1", PARSER)  # wrong direction
    with pytest.raises(ValidationError):
        table_values("y = x", "0", "10000", "1", PARSER)  # too many rows
    with pytest.raises(ValidationError):
        table_values("y = x", "a", "10", "1", PARSER)  # not a number


def test_descending_tables():
    res = table_values("y = 2x", "2", "0", "-1", PARSER)
    assert list(res.xs) == ["2", "1", "0"]
    assert list(res.ys) == ["4", "2", "0"]
