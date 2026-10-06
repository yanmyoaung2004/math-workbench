"""SymPy solver adapter — algebra facts computed here, decisions made in application.

Research basis: docs/research/sympy-facts.md, ADR-0002.
Key behaviors: solveset with explicit Set-tag reading, exact/approx separation,
independent substitution check, step-chain strings built from real SymPy objects
(sstr of Eq) so formatting can never drift from engine values.
"""

from __future__ import annotations

from sympy import Eq, N, Poly, S, Symbol, expand, factor, simplify, sstr
from sympy.solvers.solveset import solveset

from ..domain.exceptions import UnsolvableError, ValidationError
from ..domain.models import Domain, Expression
from ..ports.solver_port import LinearFacts, SolverPort, TransformFacts
from ._sympy_common import canonical, eq_str, has_bracket_product, to_sympy

_INFINITE_SETS = (S.Reals, S.Complexes)


class SymPySolver(SolverPort):
    # -- linear equations -------------------------------------------------
    def solve_linear(
        self, expr: Expression, domain: Domain = Domain.REALS
    ) -> LinearFacts:
        if expr.kind != "equation":
            raise ValidationError(
                "To solve, enter an equation with '=' — e.g. 2x + 5 = 17. "
                "Expressions without '=' can be simplified, expanded or factorised."
            )
        lhs_raw, rhs_raw = expr.canonical.split("=", 1)
        lhs, rhs = to_sympy(lhs_raw), to_sympy(rhs_raw)
        symbols = lhs.free_symbols | rhs.free_symbols
        if len(symbols) > 1:
            names = ", ".join(sorted(s.name for s in symbols))
            raise UnsolvableError(
                f"I can only solve equations in one variable so far (found {names}). "
                "Simultaneous equations arrive in Phase 1b."
            )
        if not symbols:
            tag = "infinite" if bool(simplify(lhs - rhs) == 0) else "empty"
            return LinearFacts(
                symbol="x", solutions=(), approximate=(), set_tag=tag, chain=(),
                interpretation=expr.canonical,
            )

        x = next(iter(symbols))
        diff = expand(lhs - rhs)
        if diff.is_zero:
            return LinearFacts(
                symbol=x.name, solutions=(), approximate=(), set_tag="infinite",
                chain=(), interpretation=expr.canonical,
            )
        try:
            degree = Poly(diff, x).degree()
        except Exception as exc:
            raise UnsolvableError(
                "That isn't a linear equation I can break into steps yet. "
                "Quadratics and higher degrees arrive in Phase 1b."
            ) from exc
        if degree == 0:
            return LinearFacts(
                symbol=x.name, solutions=(), approximate=(), set_tag="empty",
                chain=(), interpretation=expr.canonical,
            )
        if degree != 1:
            raise UnsolvableError(
                f"That is a degree-{degree} equation. I solve linear equations so far; "
                "quadratics arrive in Phase 1b."
            )

        domain_set = S.Reals if domain is Domain.REALS else S.Complexes
        try:
            result = solveset(Eq(lhs, rhs), x, domain=domain_set)
        except (NotImplementedError, ValueError) as exc:
            raise UnsolvableError(
                "I couldn't solve that automatically — no solution was guessed. "
                "Try a simpler linear form like 2x + 5 = 17."
            ) from exc

        if result is S.EmptySet:
            return LinearFacts(
                symbol=x.name, solutions=(), approximate=(), set_tag="empty", chain=(),
                interpretation=expr.canonical,
            )
        if result in _INFINITE_SETS:
            return LinearFacts(
                symbol=x.name, solutions=(), approximate=(), set_tag="infinite",
                chain=(), interpretation=expr.canonical,
            )
        if not getattr(result, "is_FiniteSet", False):
            raise UnsolvableError(
                "I couldn't reduce that to explicit solutions — no solution was guessed."
            )

        solutions = tuple(sorted((sstr(s) for s in result), key=str))
        approximate = tuple(str(N(to_sympy(s), 15)) for s in solutions)
        chain = self._linear_chain(expr.canonical, lhs, rhs, x)
        return LinearFacts(
            symbol=x.name,
            solutions=solutions,
            approximate=approximate,
            set_tag="finite",
            chain=chain,
            interpretation=expr.canonical,
        )

    # -- step-chain construction -------------------------------------------
    def _linear_chain(self, interpretation: str, lhs, rhs, x: Symbol):
        """Ordered (operation, operand, before, after) GCSE chain.

        Layout after the optional normalize step: `a*x + b = R`. Every string is
        sstr() of a real SymPy Eq so display can never drift from engine values.
        The normalize step compares the student's written (display) sides with
        the expanded sides: brackets → distribute, otherwise → collect.
        """
        chain: list[tuple[str, str, str, str]] = []
        display_lhs, display_rhs = (
            interpretation.split("=", 1)[0].strip(),
            interpretation.split("=", 1)[1].strip(),
        )
        expanded_lhs, expanded_rhs = canonical(expand(lhs)), canonical(expand(rhs))
        cur_lhs, cur_rhs = expand(lhs), expand(rhs)

        if display_lhs != expanded_lhs or display_rhs != expanded_rhs:
            after = f"{expanded_lhs} = {expanded_rhs}"
            display = f"{display_lhs} = {display_rhs}"
            bracketed = [
                side
                for side in (display_lhs, display_rhs)
                if has_bracket_product(to_sympy(side, evaluate=False))
            ]
            if bracketed:
                chain.append(("distribute", " and ".join(bracketed), display, after))
            else:
                combined = " and ".join(
                    side for side, exp in ((display_lhs, expanded_lhs), (display_rhs, expanded_rhs))
                    if side != exp
                )
                chain.append(("collect_like_terms", combined, display, after))

        total = expand(cur_lhs - cur_rhs)
        poly = Poly(total, x)
        coeffs = poly.all_coeffs()
        a = coeffs[0]
        const = coeffs[1] if len(coeffs) > 1 else S.Zero

        before = chain[-1][3] if chain else interpretation
        if x in cur_rhs.free_symbols:
            # Two-sided: collect into a*x = R'. Operand names the moved groups.
            new_rhs = -const
            after = eq_str(a * x, new_rhs)
            moved_const = Poly(cur_lhs, x).nth(0)
            moved_x = Poly(cur_rhs, x).nth(1) * x
            operand = f"{canonical(moved_x)} and {canonical(moved_const)}"
            chain.append(("collect_like_terms", operand, before, after))
            cur_lhs, cur_rhs = a * x, new_rhs
            before = after

        # Single-sided form: cur_lhs = a*x + b, cur_rhs = R constant.
        b = expand(cur_lhs - a * x)
        r = cur_rhs
        if b != 0:
            if bool(b > 0):
                op, operand = "subtract_both_sides", canonical(b)
            else:
                op, operand = "add_both_sides", canonical(-b)
            after = eq_str(a * x, r - b)
            chain.append((op, operand, before, after))
            before, r = after, r - b

        if a != 1:
            after = eq_str(x, r / a)
            if a.is_Rational and a.p in (1, -1) and abs(int(a.q)) > 1:
                mult = int(a.q) if a.p == 1 else -int(a.q)
                chain.append(("multiply_both_sides", canonical(S(mult)), before, after))
            else:
                chain.append(("divide_both_sides", canonical(a), before, after))
        return tuple(chain)

    # -- transforms ---------------------------------------------------------
    def transform(self, expr: Expression, kind: str) -> TransformFacts:
        ops = {"simplify": simplify, "expand": expand, "factorise": factor}
        if kind not in ops:
            raise ValidationError(
                f"Unknown transform {kind!r}. Choose simplify, expand or factorise."
            )
        if expr.kind == "equation":
            raise ValidationError(
                "Transforms work on expressions without '='. "
                "To solve an equation, use solve_linear."
            )
        parsed = to_sympy(expr.canonical)
        try:
            out = ops[kind](parsed)
        except Exception as exc:
            raise UnsolvableError(
                f"I couldn't {kind} that expression automatically."
            ) from exc
        return TransformFacts(
            interpretation=expr.canonical, before=canonical(parsed), after=canonical(out)
        )

    # -- independent checks --------------------------------------------------
    def check_equality(self, lhs: str, rhs: str, symbol: str, candidate: str) -> bool:
        try:
            left, right = to_sympy(lhs), to_sympy(rhs)
            sym = Symbol(symbol)
            value = simplify((left - right).subs(sym, to_sympy(candidate)))
            return bool(value == 0)
        except Exception:
            return False

    def check_identity(self, before: str, after: str) -> bool:
        try:
            return bool(simplify(to_sympy(before) - to_sympy(after)) == 0)
        except Exception:
            return False
