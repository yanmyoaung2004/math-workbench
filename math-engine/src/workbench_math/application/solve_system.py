"""Use-case: solve a 2x2 linear system end-to-end (elimination steps)."""

from __future__ import annotations

from ..domain.exceptions import (
    InfiniteSolutionsError,
    NoSolutionError,
    UnsolvableError,
    ValidationError,
)
from ..domain.models import Binding, Domain, DomainInfo, Solution, Verification
from ..domain.steps import make_step
from ..domain.verify import solution_self_consistent, system_holds
from ..ports.parser_port import ParserPort
from ..ports.solver_port import SolverPort


def solve_system(
    raws: list[str],
    parser: ParserPort,
    solver: SolverPort,
    domain: Domain = Domain.REALS,
) -> Solution:
    if not isinstance(raws, list) or len(raws) != 2:
        raise ValidationError(
            "Send exactly two equations as a list — e.g. "
            '{"op": "solve_system", "equations": ["2x + y = 7", "x - y = 2"]}.'
        )
    exprs = tuple(parser.parse(raw) for raw in raws)
    facts = solver.solve_system(exprs, domain)

    if facts.set_tag == "empty":
        raise NoSolutionError(
            "The lines are parallel — no point satisfies both equations."
        )
    if facts.set_tag == "infinite":
        raise InfiniteSolutionsError(
            "Both equations describe the same line — every point on it is a solution."
        )
    if facts.set_tag != "finite" or not facts.bindings:
        raise UnsolvableError(
            "I couldn't reduce that system to explicit values — nothing was guessed."
        )

    symbol = facts.variables[0]
    steps = tuple(
        make_step(op, operand, before, after, symbol=symbol)
        for op, operand, before, after in facts.chain
    )
    final = steps[-1].after if steps else facts.interpretation

    bindings = tuple(
        Binding(variable=var, exact=exact, approximate=approx)
        for var, exact, approx in facts.bindings
    )
    equations = tuple(facts.interpretation.split("; "))
    plain_bindings = tuple((b.variable, b.exact) for b in bindings)
    holds = system_holds(equations, plain_bindings, solver.check_system_equality)
    consistent = solution_self_consistent(
        Solution(
            interpretation=facts.interpretation,
            exact=tuple(b.exact for b in bindings),
            approximate=tuple(b.approximate for b in bindings),
            steps=steps,
        ),
        final,
    )
    verification = (
        Verification.VERIFIED.value
        if (holds and consistent)
        else Verification.UNVERIFIABLE.value
    )
    return Solution(
        interpretation=facts.interpretation,
        exact=tuple(b.exact for b in bindings),
        approximate=tuple(b.approximate for b in bindings),
        steps=steps,
        verification=verification,
        domain_info=DomainInfo(domain=domain.value),
        bindings=bindings,
    )
