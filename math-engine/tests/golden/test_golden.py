"""Golden corpus runner: every row is a permanent GCSE contract."""

from pathlib import Path

import pytest
import yaml

from workbench_math.adapters.sympy_parser import SymPyParser
from workbench_math.adapters.sympy_solver import SymPySolver
from workbench_math.application.solve_linear import solve_linear
from workbench_math.domain.exceptions import MathEngineError
from workbench_math.domain.models import Domain

CASES = yaml.safe_load((Path(__file__).parent / "linear.yaml").read_text(encoding="utf-8"))
PARSER = SymPyParser()
SOLVER = SymPySolver()


@pytest.mark.parametrize("case", CASES, ids=[c["input"] for c in CASES])
def test_golden_linear(case):
    try:
        sol = solve_linear(case["input"], PARSER, SOLVER, Domain.REALS)
    except MathEngineError as exc:
        assert case.get("error") == exc.code, f"{case['input']}: expected {case.get('error')}, got {exc.code}"
        return
    assert "error" not in case, f"{case['input']}: expected error {case['error']}, got {sol.exact}"
    assert list(sol.exact) == case["exact"]
    assert [s.operation for s in sol.steps] == [str(op) for op in case.get("ops", [])]
    assert sol.verification == "verified"
    if "approx" in case:
        assert float(sol.approximate[0]) == pytest.approx(case["approx"])
