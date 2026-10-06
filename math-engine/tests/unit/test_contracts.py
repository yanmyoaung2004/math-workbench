"""Contract tests: application behavior against faked ports (no SymPy needed).

Proves the use-cases own decisions (error codes, verification flags, step schema)
independent of the real engine.
"""

import pytest

from workbench_math.application.solve_linear import solve_linear
from workbench_math.application.transform import transform_expression
from workbench_math.domain.exceptions import (
    InfiniteSolutionsError,
    NoSolutionError,
    UnsolvableError,
)
from workbench_math.domain.models import Domain, Expression
from workbench_math.ports.parser_port import ParserPort
from workbench_math.ports.solver_port import LinearFacts, SolverPort, TransformFacts


class FakeParser(ParserPort):
    def __init__(self, canonical="2*x + 5 = 17", kind="equation"):
        self._canonical = canonical
        self._kind = kind

    def parse(self, raw: str) -> Expression:
        return Expression(raw=raw, canonical=self._canonical, kind=self._kind)


class FakeSolver(SolverPort):
    def __init__(self, facts=None, equality=True, identity=True):
        self._facts = facts or LinearFacts(
            symbol="x", solutions=("6",), approximate=("6.0",),
            set_tag="finite",
            chain=(("subtract_both_sides", "5", "2*x + 5 = 17", "2*x = 12"),
                   ("divide_both_sides", "2", "2*x = 12", "x = 6")),
            interpretation="2*x + 5 = 17",
        )
        self._equality = equality
        self._identity = identity

    def solve_linear(self, expr, domain=Domain.REALS):
        return self._facts

    def transform(self, expr, kind):
        return TransformFacts(interpretation="2*x + 3*x", before="2*x + 3*x", after="5*x")

    def check_equality(self, lhs, rhs, symbol, candidate):
        return self._equality

    def check_identity(self, before, after):
        return self._identity

    def solve_quadratic(self, expr, domain=Domain.REALS, method="auto"):
        raise NotImplementedError("contract fakes cover linear only")


def test_solve_linear_contract_shape():
    sol = solve_linear("2x + 5 = 17", FakeParser(), FakeSolver())
    assert sol.interpretation == "2*x + 5 = 17"
    assert sol.exact == ("6",) and sol.approximate == ("6.0",)
    assert sol.verification == "verified"
    assert [s.operation for s in sol.steps] == ["subtract_both_sides", "divide_both_sides"]
    for step in sol.steps:  # step schema completeness (docs/math-engine.md §1)
        assert step.operation and step.operand and step.before and step.after
        assert step.rule and step.explanation and step.verification


def test_set_tags_map_to_error_codes():
    for tag, exc in (("empty", NoSolutionError),
                     ("infinite", InfiniteSolutionsError),
                     ("condition", UnsolvableError)):
        facts = LinearFacts(symbol="x", solutions=(), approximate=(),
                            set_tag=tag, chain=(), interpretation="x + 1 = x + 2")
        with pytest.raises(exc) as err:
            solve_linear("x", FakeParser(), FakeSolver(facts=facts))
        assert err.value.code in ("NO_SOLUTION", "INFINITE_SOLUTIONS", "UNSOLVABLE")


def test_broken_chain_flags_unverifiable_not_silent():
    facts = LinearFacts(symbol="x", solutions=("6",), approximate=("6.0",),
                        set_tag="finite",
                        chain=(("divide_both_sides", "2", "2*x = 999", "x = 6"),),
                        interpretation="2*x + 5 = 17")
    sol = solve_linear("x", FakeParser(), FakeSolver(facts=facts))
    assert sol.verification == "unverifiable"


def test_failed_substitution_flags_unverifiable():
    sol = solve_linear("2x + 5 = 17", FakeParser(), FakeSolver(equality=False))
    assert sol.verification == "unverifiable"
    assert sol.exact == ("6",)  # still reported, but flagged (FR-VER-1)


def test_transform_contract():
    sol = transform_expression("2x + 3x", "simplify", FakeParser(kind="expression"), FakeSolver())
    assert sol.exact == ("5*x",) and len(sol.steps) == 1
    assert sol.steps[0].operation == "simplify_expression"
    assert sol.verification == "verified"


def test_transform_identity_failure_flagged():
    sol = transform_expression("2x", "simplify", FakeParser(kind="expression"), FakeSolver(identity=False))
    assert sol.verification == "unverifiable"
