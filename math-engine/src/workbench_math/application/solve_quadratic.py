"""Use-case: solve a quadratic equation end-to-end.

Multi-root solutions share one chain whose final `after` is the joined set
"x = r1; x = r2" (contract docs/math-engine.md §1). Error mapping and
independent verification mirror solve_linear.
"""

from __future__ import annotations

from ..domain.exceptions import (
    InfiniteSolutionsError,
    NoSolutionError,
    UnsolvableError,
    ValidationError,
)
from ..domain.models import Domain, DomainInfo, Solution, Verification
from ..domain.steps import make_step
from ..domain.verify import solution_holds, solution_self_consistent
from ..ports.parser_port import ParserPort
from ..ports.solver_port import SolverPort

_METHODS = ("auto", "factorise", "formula", "complete_square")


def solve_quadratic(
    raw: str,
    parser: ParserPort,
    solver: SolverPort,
    domain: Domain = Domain.REALS,
    method: str = "auto",
) -> Solution:
    if method not in _METHODS:
        raise ValidationError(
            f"Unknown method {method!r}. Choose auto, factorise, formula "
            "or complete_square."
        )
    expr = parser.parse(raw)
    facts = solver.solve_quadratic(expr, domain, method)

    if facts.set_tag == "empty":
        raise NoSolutionError(
            "There are no real solutions — the discriminant is negative, "
            "so the parabola never crosses the x-axis."
            if domain is Domain.REALS
            else "There is no solution."
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
