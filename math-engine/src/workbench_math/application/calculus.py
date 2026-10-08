"""Use-cases: differentiate, indefinite and definite integrals, all verified."""

from __future__ import annotations

from ..domain.exceptions import UnsolvableError
from ..domain.models import Binding, Domain, DomainInfo, Solution, Verification
from ..domain.steps import make_step
from ..domain.verify import solution_self_consistent
from ..ports.parser_port import ParserPort
from ..ports.solver_port import SolverPort


def _assemble(facts, solver: SolverPort, check) -> Solution:
    steps = tuple(
        make_step(op, operand, before, after, symbol=facts.symbol)
        for op, operand, before, after in facts.chain
    )
    final = steps[-1].after if steps else facts.interpretation
    consistent = solution_self_consistent(
        Solution(interpretation=facts.interpretation, exact=(facts.result,),
                 approximate=(facts.approximate,), steps=steps),
        final,
    )
    holds = check()
    verification = (Verification.VERIFIED.value
                    if (holds and consistent) else Verification.UNVERIFIABLE.value)
    return Solution(
        interpretation=facts.interpretation,
        exact=(facts.result,),
        approximate=(facts.approximate,),
        steps=steps,
        verification=verification,
        domain_info=DomainInfo(domain=Domain.REALS.value),
        bindings=(Binding(variable=facts.symbol, exact=facts.result,
                          approximate=facts.approximate),),
    )


def differentiate_expression(raw: str, parser: ParserPort, solver: SolverPort) -> Solution:
    expr = parser.parse(raw)
    facts = solver.differentiate(expr)
    if facts.set_tag != "ok":
        raise UnsolvableError("I couldn't differentiate that.")
    return _assemble(facts, solver,
                     lambda: solver.check_derivative(expr.canonical, facts.symbol))


def integrate_expression(raw: str, parser: ParserPort, solver: SolverPort,
                         a: str = "", b: str = "") -> Solution:
    expr = parser.parse(raw)
    facts = solver.integrate(expr, a, b)
    if facts.set_tag != "ok":
        raise UnsolvableError("I couldn't integrate that.")
    if facts.operation == "definite_integrate":
        check = lambda: solver.check_definite(  # noqa: E731
            expr.canonical, facts.symbol, facts.a, facts.b, facts.result)
    else:
        bare = facts.result[:-len(" + C")] if facts.result.endswith(" + C") else facts.result
        check = lambda: solver.check_antiderivative(  # noqa: E731
            bare, expr.canonical, facts.symbol)
    return _assemble(facts, solver, check)
