"""Use-case: solve a linear inequality end-to-end (with sign-flip teaching)."""

from __future__ import annotations

from ..domain.exceptions import (
    InfiniteSolutionsError,
    NoSolutionError,
    UnsolvableError,
)
from ..domain.models import Domain, DomainInfo, Solution, Verification
from ..domain.steps import make_step
from ..domain.verify import solution_self_consistent
from ..ports.parser_port import ParserPort
from ..ports.solver_port import SolverPort


def solve_inequality(
    raw: str,
    parser: ParserPort,
    solver: SolverPort,
    domain: Domain = Domain.REALS,
) -> Solution:
    expr = parser.parse(raw)
    facts = solver.solve_inequality(expr, domain)

    if facts.set_tag == "empty":
        raise NoSolutionError("No values satisfy that inequality.")
    if facts.set_tag == "all":
        raise InfiniteSolutionsError(
            "That inequality is true for every real number."
            if facts.phrase == "all real numbers"
            else "That inequality is always true."
        )
    if facts.set_tag != "interval":
        raise UnsolvableError(
            "I couldn't reduce that inequality to an explicit range."
        )

    steps = tuple(
        make_step(op, operand, before, after, symbol=facts.symbol)
        for op, operand, before, after in facts.chain
    )
    final = steps[-1].after if steps else facts.interpretation

    rel = next(
        (op for op in (">=", "<=", ">", "<") if f" {op} " in f" {facts.relation} "),
        None,
    )
    lhs_raw, rhs_raw = facts.relation.split(rel, 1) if rel else ("", "")
    point_holds = bool(rel) and solver.check_inequality(
        lhs_raw, rhs_raw, rel, facts.symbol, facts.test_point
    )
    consistent = solution_self_consistent(
        Solution(
            interpretation=facts.interpretation, exact=(facts.phrase,),
            approximate=(), steps=steps,
        ),
        final,
    )
    agrees = facts.phrase == final
    verification = (
        Verification.VERIFIED.value
        if (point_holds and consistent and agrees)
        else Verification.UNVERIFIABLE.value
    )
    return Solution(
        interpretation=facts.interpretation,
        exact=(facts.phrase,),
        approximate=(),
        steps=steps,
        verification=verification,
        domain_info=DomainInfo(domain=domain.value),
    )
