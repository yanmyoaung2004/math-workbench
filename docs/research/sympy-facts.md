# Research evidence — SymPy (gathered 2026-10-06, subagent)

Verified against SymPy 1.14.0 `latest` docs. Full fact sheet archived from
evidence-gathering subagent; synthesis in `../decisions/0002-sympy-solveset-parse-verify.md`.

## solve vs solveset

- `solveset(f, symbol, domain=S.Complexes)` returns a `Set`; `solve(f, *symbols)`
  is older, output shape inconsistent (empty list ambiguous: no-solution vs not-found).
  Tutorial recommends `solveset`. Sources:
  https://docs.sympy.org/latest/modules/solvers/solveset.html ·
  https://docs.sympy.org/latest/tutorials/intro-tutorial/solvers.html ·
  https://docs.sympy.org/latest/explanation/solve-output.html
- Return tags: `FiniteSet` (e.g. `{0,1}`), `Interval`, `Union/ImageSet`,
  `EmptySet` (provably none, e.g. `solveset(exp(x),x)`), `ConditionSet`
  (unsolved, e.g. `cos(x)-x`), `S.Reals` identity (infinite, e.g. `x-x`),
  `ImageSet` periodic infinite (e.g. `sin(x)-1` over Reals).
- Default domain is Complexes: `solveset(x**2+1,x)` → `{-I,I}` but with
  `domain=S.Reals` → `EmptySet`. Inequalities real-only; result intersected with domain.
- `solve(..., check=True)` default verifies via `checksol` + excludes
  zero-denominators (`solve(sin(x)/x)` → `[pi]`, `check=False` → spurious `[0,pi]`).

## Parsing

- `parse_expr` (not `sympify`) is correct for user strings. `sympify("2x+1")`
  raises `SympifyError`; `parse_expr("2x+1", transformations="all")` → `2*x+1`.
  Best-practice doc says string→`sympify` inside library functions is accidental.
  Sources: https://docs.sympy.org/latest/explanation/best-practices.html ·
  https://docs.sympy.org/latest/modules/parsing.html · https://docs.sympy.org/latest/modules/core.html
- Needed transforms: `convert_xor` (`^`→`**`), `implicit_multiplication[_application]`
  (`2x`, `3 x y`); `standard_transformations` alone does NOT cover implicit mult
  (`parse_expr("2x", T[:5])` → `SyntaxError`, `T[:6]` → `2*x`).
- `parse_expr` uses `eval` — never on unsanitized input.
- Equations are `Eq`; `==` is structural (`(x+1)**2 == x**2+2*x+1` → `False`).
  Gotchas: https://docs.sympy.org/latest/tutorials/intro-tutorial/gotchas.html

## Verify + exact vs float

- `subs` returns new expr; verify via `simplify(a-b)==0`; `equals()` is randomized
  numeric (Richardson undecidability caveat).
- Exact: `sympy.pi`, `Rational(1,2)`; `sin(sympy.pi)==0` vs `sin(math.pi)==1.2e-16`;
  `factor(x**2.0-1)` fails where `factor(x**2-1)` works. `N(expr)`/`evalf()` (15 digits
  default) only for the separate `approximate` field.
  Sources: https://docs.sympy.org/latest/modules/evalf.html ·
  https://docs.sympy.org/latest/tutorials/intro-tutorial/basic_operations.html

## simplify/expand/factor

- `simplify()` heuristic, output not guaranteed — avoid programmatically; use
  targeted `cancel/expand/collect`. `factor()` guaranteed irreducible over
  rationals; `expand()` canonical sum-of-monomials.
  Source: https://docs.sympy.org/latest/modules/simplify/simplify.html ·
  https://docs.sympy.org/latest/tutorials/intro-tutorial/simplification.html

## Errors

- `SympifyError` (unparseable), `SyntaxError` (bad `2x` without transforms),
  `solveset`: `NotImplementedError` (complex inequalities), `ValueError` (bad input).
