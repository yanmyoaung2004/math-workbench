"""SymPy solver adapter — algebra facts computed here, decisions made in application.

Research basis: docs/research/sympy-facts.md, ADR-0002.
Key behaviors: solveset with explicit Set-tag reading, exact/approx separation,
independent substitution check, step-chain strings built from real SymPy objects
(sstr of Eq) so formatting can never drift from engine values.
"""

from __future__ import annotations

from sympy import Eq, N, Poly, S, Symbol, expand, factor, factor_list, simplify, sqrt, sstr
from sympy.solvers.solveset import solveset

from ..domain.exceptions import UnsolvableError, ValidationError
from ..domain.models import Domain, Expression
from ..ports.solver_port import (
    LinearFacts,
    QuadraticFacts,
    SolverPort,
    TransformFacts,
)
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

    # -- quadratic equations -----------------------------------------------
    def solve_quadratic(
        self, expr: Expression, domain: Domain = Domain.REALS, method: str = "auto"
    ) -> QuadraticFacts:
        if method not in ("auto", "factorise", "formula", "complete_square"):
            raise ValidationError(
                f"Unknown method {method!r}. Choose auto, factorise, formula "
                "or complete_square."
            )
        if expr.kind != "equation":
            raise ValidationError(
                "To solve, enter an equation with '=' — e.g. x^2 - 5x + 6 = 0."
            )
        lhs_raw, rhs_raw = expr.canonical.split("=", 1)
        lhs, rhs = to_sympy(lhs_raw), to_sympy(rhs_raw)
        symbols = lhs.free_symbols | rhs.free_symbols
        if len(symbols) > 1:
            names = ", ".join(sorted(s.name for s in symbols))
            raise UnsolvableError(
                f"I can only solve equations in one variable so far (found {names})."
            )
        if not symbols:
            tag = "infinite" if bool(simplify(lhs - rhs) == 0) else "empty"
            return QuadraticFacts(
                symbol="x", a="0", b="0", c="0", discriminant="0", solutions=(),
                approximate=(), set_tag=tag, method="formula", chain=(),
                interpretation=expr.canonical,
            )
        x = next(iter(symbols))
        diff = expand(lhs - rhs)
        if diff.is_zero:
            return QuadraticFacts(
                symbol=x.name, a="0", b="0", c="0", discriminant="0", solutions=(),
                approximate=(), set_tag="infinite", method="formula", chain=(),
                interpretation=expr.canonical,
            )
        try:
            poly = Poly(diff, x)
            degree = poly.degree()
        except Exception as exc:
            raise UnsolvableError(
                "That isn't a polynomial equation I can break into steps yet."
            ) from exc
        if degree == 0:
            return QuadraticFacts(
                symbol=x.name, a="0", b="0", c="0", discriminant="0", solutions=(),
                approximate=(), set_tag="empty", method="formula", chain=(),
                interpretation=expr.canonical,
            )
        if degree == 1:
            raise ValidationError(
                "That is linear — use solve_linear for step-by-step working."
            )
        if degree != 2:
            raise UnsolvableError(
                f"That is a degree-{degree} equation. I solve up to quadratics; "
                "cubics and higher are out of scope for V1."
            )

        coeffs = poly.all_coeffs()
        a, b, c = coeffs[0], coeffs[1], coeffs[2]
        disc = expand(b**2 - 4 * a * c)

        # Resolve the method before solving so an infeasible explicit method
        # reports itself rather than a downstream symptom.
        if method == "auto":
            method = "factorise" if self._factorable(diff, x) else "formula"
        elif method == "factorise" and not self._factorable(diff, x):
            raise UnsolvableError(
                "That quadratic doesn't factorise over the rationals — "
                "use the formula or completing the square instead."
            )

        domain_set = S.Reals if domain is Domain.REALS else S.Complexes
        try:
            result = solveset(Eq(lhs, rhs), x, domain=domain_set)
        except (NotImplementedError, ValueError) as exc:
            raise UnsolvableError(
                "I couldn't solve that automatically — no solution was guessed."
            ) from exc
        if result is S.EmptySet:
            return QuadraticFacts(
                symbol=x.name, a=canonical(a), b=canonical(b), c=canonical(c),
                discriminant=canonical(disc), solutions=(), approximate=(),
                set_tag="empty", method="formula", chain=(),
                interpretation=expr.canonical,
            )
        if not getattr(result, "is_FiniteSet", False):
            raise UnsolvableError(
                "I couldn't reduce that to explicit solutions — no solution was guessed."
            )

        solutions = tuple(sorted((sstr(s) for s in result), key=str))
        approximate = tuple(str(N(to_sympy(s), 15)) for s in solutions)

        chain = self._quadratic_chain(
            expr.canonical, lhs, rhs, x, a, b, c, disc, solutions, method
        )
        return QuadraticFacts(
            symbol=x.name, a=canonical(a), b=canonical(b), c=canonical(c),
            discriminant=canonical(disc), solutions=solutions,
            approximate=approximate, set_tag="finite", method=method, chain=chain,
            interpretation=expr.canonical,
        )

    @staticmethod
    def _factorable(diff, x: Symbol) -> bool:
        """True iff diff splits into linear factors over the rationals."""
        try:
            _, factors = factor_list(diff, x)
            if not factors:
                return False
            return all(
                Poly(fac, x).degree() == 1 for fac, _ in factors
            ) and sum(
                Poly(fac, x).degree() * exp for fac, exp in factors
            ) == 2
        except Exception:
            return False

    def _quadratic_chain(self, interpretation, lhs, rhs, x, a, b, c, disc,
                         solutions, method):
        chain: list[tuple[str, str, str, str]] = []
        std = eq_str(expand(lhs - rhs), 0)
        before = interpretation
        if interpretation != std:
            chain.append(("rewrite", "", interpretation, std))
            before = std
        final = "; ".join(f"{x.name} = {s}" for s in solutions)

        if method == "factorise":
            factored = factor(expand(lhs - rhs))
            fstr = eq_str(factored, 0)
            chain.append(("factorise_equation", canonical(expand(lhs - rhs)), before, fstr))
            before = fstr
            _, factors = factor_list(expand(lhs - rhs), x)
            linears = sorted(
                {canonical(fac) for fac, _ in factors if Poly(fac, x).degree() == 1},
                key=str,
            )
            root_of = {}
            for s in solutions:
                for fac_str in linears:
                    if self.check_equality(fac_str, "0", x.name, s):
                        root_of.setdefault(fac_str, s)
            ordered = sorted(root_of.items(), key=lambda kv: str(kv[1]))
            for i, (fac_str, root) in enumerate(ordered):
                after = f"{x.name} = {root}" if i < len(ordered) - 1 else final
                chain.append(("apply_zero_product", fac_str, before, after))
                before = after
        elif method == "formula":
            coef = f"a = {canonical(a)}, b = {canonical(b)}, c = {canonical(c)}"
            chain.append(("identify_coefficients", coef, before, before))
            chain.append((
                "compute_discriminant",
                f"{canonical(b**2)} - {canonical(4 * a * c)} = {canonical(disc)}",
                before, before,
            ))
            chain.append((
                "apply_quadratic_formula",
                f"x = (-({canonical(b)}) +/- sqrt({canonical(disc)})) / (2*{canonical(a)})",
                before, final,
            ))
        else:  # complete_square
            cur = before
            aa, bb, cc = a, b, c
            if a != 1:
                cur = eq_str(x**2 + bb / aa * x + cc / aa, 0)
                chain.append(("divide_both_sides", canonical(aa), before, cur))
                aa, bb, cc = S.One, bb / a, cc / a
            half = bb / 2
            rest = half**2 - cc
            completed = eq_str((x + half) ** 2, rest)
            chain.append(("complete_the_square", canonical((x + half) ** 2), cur, completed))
            pos, neg = sqrt(rest), -sqrt(rest)
            branched = f"{eq_str(x + half, pos)} or {eq_str(x + half, neg)}"
            chain.append((
                "take_square_root_pm", f"+/-sqrt({canonical(rest)})",
                completed, branched,
            ))
            if bool(half > 0):
                op, operand = "subtract_both_sides", canonical(half)
            else:
                op, operand = "add_both_sides", canonical(-half)
            chain.append((op, operand, branched, final))
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
