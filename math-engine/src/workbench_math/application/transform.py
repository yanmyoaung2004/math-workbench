"""Use-case: simplify | expand | factorise an expression (single verified step)."""

from __future__ import annotations

from ..domain.exceptions import ValidationError
from ..domain.models import Domain, DomainInfo, Solution, Verification
from ..domain.steps import make_step
from ..ports.parser_port import ParserPort
from ..ports.solver_port import SolverPort

_OPS = {
    "simplify": "simplify_expression",
    "expand": "expand_expression",
    "factorise": "factorise_expression",
}


def transform_expression(
    raw: str,
    kind: str,
    parser: ParserPort,
    solver: SolverPort,
) -> Solution:
    if kind not in _OPS:
        raise ValidationError(
            f"Unknown transform {kind!r}. Choose simplify, expand or factorise."
        )
    expr = parser.parse(raw)
    facts = solver.transform(expr, kind)
    holds = solver.check_identity(facts.before, facts.after)
    verification = (
        Verification.VERIFIED.value if holds else Verification.UNVERIFIABLE.value
    )
    step = make_step(
        _OPS[kind], "", facts.before, facts.after, verification=verification
    )
    return Solution(
        interpretation=facts.interpretation,
        exact=(facts.after,),
        approximate=(facts.after,),
        steps=(step,),
        verification=verification,
        domain_info=DomainInfo(domain=Domain.REALS.value),
    )
