"""Use-case: solve a linear equation end-to-end.

Flow: parse → solver facts → error mapping → step pedagogy → independent
verification → Solution DTO. The application owns the *decisions* (which error
code, verified vs unverifiable); the adapter owns the *algebra*.
"""

from __future__ import annotations

from ..domain.exceptions import (
    InfiniteSolutionsError,
    NoSolutionError,
    UnsolvableError,
)
from ..domain.models import Domain, DomainInfo, Solution, Verification
from ..domain.steps import make_step
from ..domain.verify import solution_holds, solution_self_consistent
from ..ports.parser_port import ParserPort
from ..ports.solver_port import SolverPort


def solve_linear(
    raw: str,
    parser: ParserPort,
    solver: SolverPort,
    domain: Domain = Domain.REALS,
) -> Solution:
    expr = parser.parse(raw)
    facts = solver.solve_linear(expr, domain)

    if facts.set_tag == "empty":
        raise NoSolutionError(
            "There is no solution — no value of "
            f"{facts.symbol} can make both sides equal."
        )
    if facts.set_tag == "infinite":
        raise InfiniteSolutionsError(
            "Both sides are already identical, so every value of "
            f"{facts.symbol} is a solution."
        )
    if facts.set_tag != "finite" or not facts.solutions:
        raise UnsolvableError(
            "I couldn't reduce that to explicit solutions — no solution was guessed."
        )

    steps = tuple(
        make_step(op, operand, before, after, symbol=facts.symbol)
        for op, operand, before, after in facts.chain
    )
    final = steps[-1].after if steps else facts.interpretation

    all_hold = all(
        solution_holds(facts.interpretation, facts.symbol, s, solver.check_equality)
        for s in facts.solutions
    )
    consistent = solution_self_consistent(
        Solution(
            interpretation=facts.interpretation,
            exact=facts.solutions,
            approximate=facts.approximate,
            steps=steps,
        ),
        final,
    )
    verification = (
        Verification.VERIFIED.value
        if (all_hold and consistent)
        else Verification.UNVERIFIABLE.value
    )
    return Solution(
        interpretation=facts.interpretation,
        exact=facts.solutions,
        approximate=facts.approximate,
        steps=steps,
        verification=verification,
        domain_info=DomainInfo(domain=domain.value),
    )
