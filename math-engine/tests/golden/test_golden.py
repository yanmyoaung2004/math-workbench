"""Golden corpus runner: every row is a permanent GCSE contract."""

from pathlib import Path

import pytest
import yaml

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.solve_inequality import solve_inequality
from workbench_math.application.solve_linear import solve_linear
from workbench_math.application.solve_quadratic import solve_quadratic
from workbench_math.application.solve_system import solve_system
from workbench_math.domain.exceptions import MathEngineError
from workbench_math.domain.models import Domain

HERE = Path(__file__).parent
CASES = []
for name in ("linear.yaml", "quadratics.yaml", "systems.yaml", "inequalities.yaml"):
    for case in yaml.safe_load((HERE / name).read_text(encoding="utf-8")):
        case.setdefault("op", "solve_linear")
        CASES.append(case)
PARSER = SymPyParser()
SOLVER = SymPySolver()


def _run(case):
    if case["op"] == "solve_quadratic":
        return solve_quadratic(
            case["input"], PARSER, SOLVER, Domain.REALS, case.get("method", "auto"))
    if case["op"] == "solve_system":
        return solve_system(case["input"], PARSER, SOLVER, Domain.REALS)
    if case["op"] == "solve_inequality":
        return solve_inequality(case["input"], PARSER, SOLVER, Domain.REALS)
    return solve_linear(case["input"], PARSER, SOLVER, Domain.REALS)


@pytest.mark.parametrize("case", CASES, ids=[f"{c['op']}:{c['input']}" for c in CASES])
def test_golden(case):
    try:
        sol = _run(case)
    except MathEngineError as exc:
        assert case.get("error") == exc.code, f"{case['input']}: expected {case.get('error')}, got {exc.code}"
        return
    assert "error" not in case, f"{case['input']}: expected error {case['error']}, got {sol.exact}"
    if "bindings" in case:
        assert [(b.variable, b.exact) for b in sol.bindings] == [tuple(p) for p in case["bindings"]]
    else:
        assert list(sol.exact) == case["exact"]
    if "ops" in case:
        assert [s.operation for s in sol.steps] == [str(op) for op in case["ops"]]
    assert sol.verification == "verified"
    if "approx" in case:
        assert abs(float(sol.approximate[0])) == pytest.approx(case["approx"])
