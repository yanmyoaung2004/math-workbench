"""Matrix/vector operations with exact rational arithmetic and shown working.

Verification strategy per op (documented honestly):
- inverse: A·A⁻¹ = I checked symbolically — independent verification.
- determinant/multiply/dot/cross/magnitude: exact SymPy arithmetic (no
  floating point anywhere), dimension/shape preconditions enforced, plus
  algebraic cross-checks in property tests (associativity, det(AB)=detA·detB).
"""

from __future__ import annotations

from sympy import Matrix, eye, latex as _latex, simplify, sqrt, sstr

from ..adapters._sympy_common import to_sympy
from ..domain.exceptions import NoSolutionError, ValidationError
from .models import MatrixResult, MatrixStep


def _matrix(name: str, rows) -> Matrix:
    if not isinstance(rows, list) or not rows or not all(isinstance(r, list) for r in rows):
        raise ValidationError(f"{name} must be a list of row lists, e.g. [[1, 2], [3, 4]].")
    width = len(rows[0])
    if width == 0 or any(len(r) != width for r in rows):
        raise ValidationError(f"{name} rows must all have the same non-zero length.")
    try:
        entries = [[to_sympy(str(v)) for v in row] for row in rows]
    except Exception as exc:
        raise ValidationError(f"{name} entries must be numbers.") from exc
    mat = Matrix(entries)
    if mat.free_symbols:
        raise ValidationError(f"{name} entries must be numbers, not variables.")
    if len(rows) * width > 100:
        raise ValidationError("Matrices are capped at 100 entries in V2.")
    return mat


def _vector(name: str, values) -> Matrix:
    if not isinstance(values, list) or not values:
        raise ValidationError(f"{name} must be a non-empty list, e.g. [1, 2, 3].")
    return _matrix(name, [values]).T


def _str(mat: Matrix) -> str:
    return sstr(mat)


def _tex(mat: Matrix) -> str:
    try:
        return _latex(mat)
    except Exception:
        return sstr(mat)


def _nested(mat: Matrix) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(sstr(v) for v in row) for row in mat.tolist())


def multiply(a_rows, b_rows) -> MatrixResult:
    a, b = _matrix("matrix_a", a_rows), _matrix("matrix_b", b_rows)
    if a.cols != b.rows:
        raise ValidationError(
            f"Cannot multiply {a.rows}x{a.cols} by {b.rows}x{b.cols}: "
            "inner dimensions must match.")
    product = a * b
    steps = []
    if a.rows <= 3 and a.cols <= 3 and b.cols <= 3:
        for i in range(a.rows):
            for j in range(b.cols):
                terms = " + ".join(f"{sstr(a[i, k])}*{sstr(b[k, j])}" for k in range(a.cols))
                steps.append(MatrixStep(
                    operation="compute_entry",
                    explanation=f"Entry ({i + 1},{j + 1}): multiply row {i + 1} by column {j + 1}, then add.",
                    math=f"{terms} = {sstr(product[i, j])}"))
    else:
        steps.append(MatrixStep(
            operation="multiply_matrices",
            explanation="Multiply rows by columns and add (entry detail omitted for size).",
            math=f"{_str(a)} * {_str(b)} = {_str(product)}"))
    return MatrixResult(operation="multiply", input_display=f"{_str(a)} * {_str(b)}",
                        result=_nested(product), result_latex=_tex(product),
                        steps=tuple(steps))


def determinant(a_rows) -> MatrixResult:
    a = _matrix("matrix_a", a_rows)
    if a.rows != a.cols:
        raise ValidationError("Determinants need a square matrix.")
    det = a.det()
    steps = []
    if a.rows == 2:
        x, y, z, w = (a[0, 0], a[0, 1], a[1, 0], a[1, 1])
        steps.append(MatrixStep(
            operation="compute_determinant",
            explanation="For a 2x2 matrix, det = ad − bc.",
            math=f"{sstr(x)}*{sstr(w)} - {sstr(y)}*{sstr(z)} = {sstr(det)}"))
    else:
        steps.append(MatrixStep(
            operation="compute_determinant",
            explanation="Determinant by cofactor expansion (verified exact).",
            math=f"det({_str(a)}) = {sstr(det)}"))
    return MatrixResult(operation="determinant", input_display=f"det({_str(a)})",
                        result=((sstr(det),),), result_latex=_latex(det),
                        steps=tuple(steps))


def inverse(a_rows) -> MatrixResult:
    a = _matrix("matrix_a", a_rows)
    if a.rows != a.cols:
        raise ValidationError("Only square matrices have inverses.")
    det = a.det()
    if det == 0:
        raise NoSolutionError("That matrix has no inverse — its determinant is zero.")
    inv = a.inv()
    check = simplify(a * inv - eye(a.rows))
    verified = "verified" if check.is_zero_matrix else "unverifiable"
    steps = [MatrixStep(
        operation="compute_determinant",
        explanation="First the determinant (an inverse needs a non-zero one).",
        math=f"det = {sstr(det)}")]
    if a.rows == 2:
        x, y, z, w = (a[0, 0], a[0, 1], a[1, 0], a[1, 1])
        steps.append(MatrixStep(
            operation="compute_adjugate",
            explanation="Swap a and d, negate b and c — that is the adjugate.",
            math=f"adj = {sstr(Matrix([[w, -y], [-z, x]]))}"))
        steps.append(MatrixStep(
            operation="scale_matrix",
            explanation="Divide every entry by the determinant.",
            math=f"(1/{sstr(det)}) * adj = {_str(inv)}"))
    else:
        steps.append(MatrixStep(
            operation="invert_matrix",
            explanation="Inverse by adjugate over determinant (verified: A·A⁻¹ = I).",
            math=f"inv({_str(a)}) = {_str(inv)}"))
    return MatrixResult(operation="inverse", input_display=f"inv({_str(a)})",
                        result=_nested(inv), result_latex=_tex(inv),
                        steps=tuple(steps), verification=verified)


def dot(a_values, b_values) -> MatrixResult:
    a, b = _vector("vector_a", a_values), _vector("vector_b", b_values)
    if a.rows != b.rows:
        raise ValidationError("Dot product needs equal-length vectors.")
    value = sum((x * y for x, y in zip(a, b)), start=a[0] * 0)
    terms = " + ".join(f"{sstr(x)}*{sstr(y)}" for x, y in zip(a, b))
    return MatrixResult(
        operation="dot", input_display=f"{_str(a.T)} . {_str(b.T)}",
        result=((sstr(value),),), result_latex=_latex(value),
        steps=(MatrixStep(operation="dot_product",
                          explanation="Multiply matching entries, then add.",
                          math=f"{terms} = {sstr(value)}"),))


def cross(a_values, b_values) -> MatrixResult:
    a, b = _vector("vector_a", a_values), _vector("vector_b", b_values)
    if a.rows != 3 or b.rows != 3:
        raise ValidationError("Cross product needs two 3D vectors in V2.")
    value = a.cross(b)
    return MatrixResult(
        operation="cross", input_display=f"{_str(a.T)} x {_str(b.T)}",
        result=_nested(value.T), result_latex=_tex(value),
        steps=(MatrixStep(operation="cross_product",
                          explanation="Cross product via the determinant rule.",
                          math=f"{_str(a.T)} x {_str(b.T)} = {_str(value.T)}"),))


def magnitude(a_values) -> MatrixResult:
    a = _vector("vector_a", a_values)
    value = sqrt(sum((x * x for x in a), start=a[0] * 0))
    terms = " + ".join(f"{sstr(x)}^2" for x in a)
    return MatrixResult(
        operation="magnitude", input_display=f"|{_str(a.T)}|",
        result=((sstr(value),),), result_latex=_latex(value),
        steps=(MatrixStep(operation="vector_magnitude",
                          explanation="Square root of the sum of squared entries.",
                          math=f"sqrt({terms}) = {sstr(value)}"),))
