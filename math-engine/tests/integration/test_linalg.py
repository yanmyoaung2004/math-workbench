"""Linear algebra: exact results, shown working, independent checks."""

import pytest
from hypothesis import given, settings, strategies as st

from workbench_math.domain.exceptions import NoSolutionError, ValidationError
from workbench_math.linalg.matrices import (
    cross,
    determinant,
    dot,
    inverse,
    magnitude,
    multiply,
)

small = st.integers(-5, 5)
mat2 = st.lists(st.lists(small, min_size=2, max_size=2), min_size=2, max_size=2)


def test_multiply_with_entry_steps():
    res = multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
    assert res.result == (("19", "22"), ("43", "50"))
    assert len(res.steps) == 4  # one per entry
    assert "19" in res.steps[0].math
    assert res.verification == "verified"


def test_determinant_2x2_shows_formula():
    res = determinant([[4, 6], [3, 8]])
    assert res.result == (("14",),)
    assert "4*8 - 6*3" in res.steps[0].math


def test_inverse_verified_by_identity():
    res = inverse([[4, 7], [2, 6]])
    assert res.result == (("3/5", "-7/10"), ("-1/5", "2/5"))
    assert res.verification == "verified"
    assert any(s.operation == "compute_adjugate" for s in res.steps)


def test_singular_has_no_inverse():
    with pytest.raises(NoSolutionError):
        inverse([[1, 2], [2, 4]])


def test_dimension_mismatch_rejected():
    with pytest.raises(ValidationError):
        multiply([[1, 2, 3]], [[1, 2], [3, 4]])


def test_vectors():
    assert dot([1, 2, 3], [4, 5, 6]).result == (("32",),)
    assert cross([1, 0, 0], [0, 1, 0]).result == (("0", "0", "1"),)
    assert magnitude([3, 4]).result == (("5",),)
    assert magnitude([1, 1]).result == (("sqrt(2)",),)
    with pytest.raises(ValidationError):
        cross([1, 2], [3, 4])


@given(a=mat2, b=mat2)
@settings(max_examples=40)
def test_associativity_and_det_product(a, b):
    from workbench_math.linalg.matrices import _matrix

    A, B = _matrix("a", a), _matrix("b", b)
    left = (A * B) * A
    right = A * (B * A)
    assert (left - right).is_zero_matrix  # (AB)A = A(BA)
    assert (A.det() * B.det() - (A * B).det()) == 0  # det(AB) = detA·detB
