"""SymPy solver adapter — algebra facts computed here, decisions made in application.

Research basis: docs/research/sympy-facts.md, ADR-0002.
Key behaviors: solveset with explicit Set-tag reading, exact/approx separation,
independent substitution check, step-chain strings built from real SymPy objects
(sstr of Eq) so formatting can never drift from engine values.
"""

from __future__ import annotations

from sympy import (
    Eq, Ge, Gt, Interval, Le, Lt, N, Poly, S, Symbol, Union,
    expand, factor, factor_list, simplify, sqrt, sstr,
)
from sympy.solvers.solveset import linsolve, solveset

from ..domain.exceptions import UnsolvableError, ValidationError
from ..domain.models import Domain, Expression
from ..ports.solver_port import (
    InequalityFacts,
    LinearFacts,
    QuadraticFacts,
    SolverPort,
    SystemFacts,
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

    # -- linear systems (2x2) ----------------------------------------------
    def solve_system(
        self, exprs: tuple[Expression, ...], domain: Domain = Domain.REALS
    ) -> SystemFacts:
        if len(exprs) != 2:
            raise ValidationError(
                f"Send exactly two equations (got {len(exprs)}). Larger systems "
                "are out of V1 scope."
            )
        interps = []
        eqs = []
        for expr in exprs:
            if expr.kind != "equation":
                raise ValidationError(
                    "Each system entry must be an equation with '='."
                )
            lhs_raw, rhs_raw = expr.canonical.split("=", 1)
            eqs.append((to_sympy(lhs_raw), to_sympy(rhs_raw)))
            interps.append(expr.canonical)
        symbols = sorted(
            set().union(*(l.free_symbols | r.free_symbols for l, r in eqs)),
            key=lambda s: s.name,
        )
        if len(symbols) < 2:
            raise ValidationError(
                "That has only one variable — use solve_linear or solve_quadratic."
            )
        if len(symbols) > 2:
            raise UnsolvableError(
                "I solve two-variable systems in V1; larger systems are out of scope."
            )
        u, v = symbols
        try:
            result = linsolve(
                (Eq(eqs[0][0], eqs[0][1]), Eq(eqs[1][0], eqs[1][1])), (u, v)
            )
        except Exception as exc:
            raise UnsolvableError(
                "I couldn't solve that system automatically."
            ) from exc
        interpretation = "; ".join(interps)
        if result is S.EmptySet:
            return SystemFacts(
                variables=(u.name, v.name), bindings=(), set_tag="empty", chain=(),
                interpretation=interpretation,
            )
        tup = next(iter(result))
        if any(s.free_symbols for s in tup):
            return SystemFacts(
                variables=(u.name, v.name), bindings=(), set_tag="infinite", chain=(),
                interpretation=interpretation,
            )
        values = {u.name: sstr(tup[0]), v.name: sstr(tup[1])}
        bindings = tuple(
            (name, values[name], str(N(to_sympy(values[name]), 15)))
            for name in (u.name, v.name)
        )
        chain = self._system_chain(interps, eqs, u, v, values)
        return SystemFacts(
            variables=(u.name, v.name), bindings=bindings, set_tag="finite",
            chain=chain, interpretation=interpretation,
        )

    def _system_chain(self, interps, eqs, u, v, values):
        """Elimination chain over the joined state "eq1; eq2"."""
        (l1, r1), (l2, r2) = eqs
        d1, d2 = expand(l1 - r1), expand(l2 - r2)
        k1 = Poly(d1, v).nth(1) if Poly(d1, v).degree() == 1 else S.Zero
        k2 = Poly(d2, v).nth(1) if Poly(d2, v).degree() == 1 else S.Zero
        chain: list[tuple[str, str, str, str]] = []
        state = "; ".join(interps)

        def scaled(pair, m):
            (l, r) = pair
            return expand(l * m), expand(r * m)

        if k1 == 0 or k2 == 0:
            # One equation is already single-variable: solve it, substitute.
            idx = 0 if k1 == 0 else 1
            l, r = (l1, r1) if idx == 0 else (l2, r2)
            other = interps[1] if idx == 0 else interps[0]
            dd = expand(l - r)
            ku = Poly(dd, u).nth(1)
            uval = to_sympy(values[u.name])
            after = f"{eq_str(u, uval)}; {other}"
            chain.append(("divide_both_sides", canonical(ku), state, after))
            sl, sr = (l2, r2) if idx == 0 else (l1, r1)
            sub = (expand(sl.subs(u, uval)), expand(sr.subs(u, uval)))
            after2 = f"{eq_str(u, uval)}; {eq_str(*sub)}"
            chain.append(("substitute_back", f"{u.name} = {values[u.name]}", after, after2))
            dd2 = expand(sub[0] - sub[1])
            kv = Poly(dd2, v).nth(1)
            final = f"{eq_str(u, uval)}; {eq_str(v, to_sympy(values[v.name]))}"
            chain.append(("divide_both_sides", canonical(kv), after2, final))
            return tuple(chain)

        m1, m2 = abs(k2), abs(k1)
        s1 = scaled((l1, r1), m1)
        s2 = scaled((l2, r2), m2)
        if m1 != 1:
            after = f"{eq_str(*s1)}; {interps[1]}"
            chain.append(("scale_equation", canonical(m1), state, after))
            state = after
        if m2 != 1:
            first = state.split("; ", 1)[0]
            after = f"{first}; {eq_str(*s2)}"
            chain.append(("scale_equation", canonical(m2), state, after))
            state = after
        same_sign = bool(k1 * k2 > 0)
        new_l = s1[0] - s2[0] if same_sign else s1[0] + s2[0]
        new_r = s1[1] - s2[1] if same_sign else s1[1] + s2[1]
        after = f"{eq_str(new_l, new_r)}; {interps[1]}"
        chain.append(("eliminate_variable", v.name, state, after))
        ku = Poly(expand(new_l - new_r), u).nth(1)
        uval = to_sympy(values[u.name])
        after_u = f"{eq_str(u, uval)}; {interps[1]}"
        chain.append(("divide_both_sides", canonical(ku), after, after_u))
        sub = (expand(l2.subs(u, uval)), expand(r2.subs(u, uval)))
        after2 = f"{eq_str(u, uval)}; {eq_str(*sub)}"
        chain.append(("substitute_back", f"{u.name} = {values[u.name]}", after_u, after2))
        kv = Poly(expand(sub[0] - sub[1]), v).nth(1)
        final = f"{eq_str(u, uval)}; {eq_str(v, to_sympy(values[v.name]))}"
        chain.append(("divide_both_sides", canonical(kv), after2, final))
        return tuple(chain)

    # -- linear inequalities ------------------------------------------------
    _REL_CLASS = {"<": Lt, "<=": Le, ">": Gt, ">=": Ge}
    _FLIP = {"<": ">", ">": "<", "<=": ">=", ">=": "<="}

    def solve_inequality(
        self, expr: Expression, domain: Domain = Domain.REALS
    ):
        if expr.kind != "inequality":
            raise ValidationError(
                "To solve an inequality, enter one comparison — e.g. 2x + 3 > 9."
            )
        if domain is not Domain.REALS:
            raise ValidationError("Inequalities are solved over the reals in V1.")
        rel = next((op for op in (">=", "<=", ">", "<") if f" {op} " in f" {expr.canonical} "), None)
        if rel is None:
            raise ValidationError("I couldn't find a comparison in that input.")
        lhs_raw, rhs_raw = expr.canonical.split(rel, 1)
        lhs, rhs = to_sympy(lhs_raw), to_sympy(rhs_raw)
        symbols = lhs.free_symbols | rhs.free_symbols
        if len(symbols) > 1:
            raise UnsolvableError("I solve inequalities in one variable in V1.")
        if not symbols:
            holds = self.check_inequality(lhs_raw, rhs_raw, rel, "x", "0")
            tag = "all" if holds else "empty"
            return InequalityFacts(
                symbol="x", relation=expr.canonical, phrase="all real numbers",
                set_tag=tag, test_point="0", chain=(), interpretation=expr.canonical,
            )
        x = next(iter(symbols))
        diff = expand(lhs - rhs)
        if diff.is_zero:
            holds = self.check_inequality(lhs_raw, rhs_raw, rel, x.name, "0")
            tag = "all" if holds else "empty"
            return InequalityFacts(
                symbol=x.name, relation=expr.canonical,
                phrase="all real numbers", set_tag=tag, test_point="0", chain=(),
                interpretation=expr.canonical,
            )
        try:
            degree = Poly(diff, x).degree()
        except Exception as exc:
            raise UnsolvableError("That isn't linear — V1 shows steps for linear inequalities.") from exc
        if degree == 0:
            holds = self.check_inequality(lhs_raw, rhs_raw, rel, x.name, "0")
            tag = "all" if holds else "empty"
            return InequalityFacts(
                symbol=x.name, relation=expr.canonical,
                phrase="all real numbers", set_tag=tag, test_point="0", chain=(),
                interpretation=expr.canonical,
            )
        if degree != 1:
            raise UnsolvableError(
                "V1 shows steps for linear inequalities only — quadratics arrive later."
            )
        try:
            result = solveset(self._REL_CLASS[rel](lhs, rhs), x, domain=S.Reals)
        except (NotImplementedError, ValueError) as exc:
            raise UnsolvableError("I couldn't solve that inequality automatically.") from exc
        if result is S.EmptySet:
            return InequalityFacts(
                symbol=x.name, relation=expr.canonical, phrase="",
                set_tag="empty", test_point="", chain=(),
                interpretation=expr.canonical,
            )
        if result is S.Reals:
            return InequalityFacts(
                symbol=x.name, relation=expr.canonical, phrase="all real numbers",
                set_tag="all", test_point="0", chain=(),
                interpretation=expr.canonical,
            )
        phrase, test_point = self._describe_set(result, x.name)
        chain = self._inequality_chain(expr.canonical, lhs, rhs, x, rel)
        return InequalityFacts(
            symbol=x.name, relation=expr.canonical, phrase=phrase,
            set_tag="interval", test_point=test_point, chain=chain,
            interpretation=expr.canonical,
        )

    @staticmethod
    def _describe_set(solution_set, name: str) -> tuple[str, str]:
        """GCSE phrase + interior test point for an Interval/Union result."""
        parts = solution_set.args if isinstance(solution_set, Union) else (solution_set,)
        phrases, points = [], []
        for part in parts:
            if not isinstance(part, Interval):
                raise UnsolvableError(
                    "That solution set is too complex to display in V1."
                )
            a, b = part.start, part.end
            la = "<" if part.left_open else "<="
            ra = "<" if part.right_open else "<="
            sa, sb = canonical(a), canonical(b)
            if a is S.NegativeInfinity and b is S.Infinity:
                phrases.append("all real numbers")
                points.append("0")
            elif a is S.NegativeInfinity:
                phrases.append(f"{name} {ra} {sb}")
                points.append(canonical(b - 1))
            elif b is S.Infinity:
                op = ">" if la == "<" else ">="
                phrases.append(f"{name} {op} {sa}")
                points.append(canonical(a + 1))
            else:
                phrases.append(f"{sa} {la} {name} {ra} {sb}")
                points.append(canonical((a + b) / 2))
        return " or ".join(phrases), points[0]

    def _inequality_chain(self, interpretation, lhs, rhs, x, rel):
        """Linear inequality chain with sign-flip on negative multiply/divide."""
        flip = self._FLIP[rel]
        ineq = lambda l, r, o: f"{canonical(l)} {o} {canonical(r)}"  # noqa: E731
        chain: list[tuple[str, str, str, str]] = []
        display_lhs, display_rhs = (
            interpretation.split(rel, 1)[0].strip(),
            interpretation.split(rel, 1)[1].strip(),
        )
        expanded_lhs, expanded_rhs = canonical(expand(lhs)), canonical(expand(rhs))
        cur_lhs, cur_rhs = expand(lhs), expand(rhs)
        if display_lhs != expanded_lhs or display_rhs != expanded_rhs:
            after = f"{expanded_lhs} {rel} {expanded_rhs}"
            display = f"{display_lhs} {rel} {display_rhs}"
            bracketed = [
                side
                for side in (display_lhs, display_rhs)
                if has_bracket_product(to_sympy(side, evaluate=False))
            ]
            if bracketed:
                chain.append(("distribute", " and ".join(bracketed), display, after))
            else:
                chain.append(("collect_like_terms", display_lhs, display, after))

        total = expand(cur_lhs - cur_rhs)
        poly = Poly(total, x)
        coeffs = poly.all_coeffs()
        a = coeffs[0]
        const = coeffs[1] if len(coeffs) > 1 else S.Zero
        before = chain[-1][3] if chain else interpretation
        if x in cur_rhs.free_symbols:
            new_rhs = -const
            after = ineq(a * x, new_rhs, rel)
            chain.append(("collect_like_terms", "like terms", before, after))
            cur_lhs, cur_rhs = a * x, new_rhs
            before = after

        b = expand(cur_lhs - a * x)
        r = cur_rhs
        cur_rel = rel
        if b != 0:
            if bool(b > 0):
                op, operand = "subtract_both_sides", canonical(b)
            else:
                op, operand = "add_both_sides", canonical(-b)
            after = ineq(a * x, r - b, cur_rel)
            chain.append((op, operand, before, after))
            before, r = after, r - b

        if a != 1:
            if bool(a < 0):
                if a.is_Rational and a.p == -1 and abs(int(a.q)) > 1:
                    m = -int(a.q)
                else:
                    m = S.NegativeOne
                cur_rel = flip
                after = ineq(expand(a * x * m), expand(r * m), cur_rel)
                chain.append(("flip_inequality_sign", canonical(m), before, after))
                before, a, r = after, expand(a * m), expand(r * m)
            if a != 1:
                after = ineq(x, r / a, cur_rel)
                chain.append(("divide_both_sides", canonical(a), before, after))
        return tuple(chain)

    def check_inequality(self, lhs: str, rhs: str, rel: str, symbol: str, candidate: str) -> bool:
        try:
            value = simplify(
                (to_sympy(lhs) - to_sympy(rhs)).subs(Symbol(symbol), to_sympy(candidate))
            )
            zero = S.Zero
            return bool(
                {"<": value < zero, "<=": value <= zero,
                 ">": value > zero, ">=": value >= zero}[rel]
            )
        except Exception:
            return False

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

    def check_system_equality(self, equations, bindings) -> bool:
        try:
            sub = {Symbol(var): to_sympy(val) for var, val in bindings}
            for equation in equations:
                lhs_raw, rhs_raw = equation.split("=", 1)
                diff = simplify(
                    (to_sympy(lhs_raw) - to_sympy(rhs_raw)).subs(sub)
                )
                if not bool(diff == 0):
                    return False
            return True
        except Exception:
            return False
