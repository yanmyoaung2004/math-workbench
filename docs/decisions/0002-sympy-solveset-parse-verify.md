# ADR-0002: SymPy usage — solveset + parse_expr + substitution verify

Date: 2026-10-06 · Status: **accepted** · Sources: `../research/sympy-facts.md` (SymPy 1.14 docs)

## Context

Engine must parse GCSE strings (`2x`, `x^2`, `1/x`), solve with explicit
no/infinite/unsolvable distinction, preserve exacts, and verify independently.

## Decision

1. **Solve with `solveset(equation, symbol, domain)`**, default `domain=S.Reals`
   for GCSE (opt-in `S.Complexes`). Read the returned `Set` tag:
   `EmptySet` → `NO_SOLUTION`; `Reals` identity → `INFINITE_SOLUTIONS`;
   `FiniteSet` → solutions; `ConditionSet`/raise `NotImplementedError` → `UNSOLVABLE`
   (honest "could not solve"). `solve()` rejected: output shape inconsistent,
   empty list ambiguous (no-solution vs not-found).
2. **Parse with `parse_expr(s, transformations=implicit_multiplication_application
   + convert_xor + …)`** over a GCSE `local_dict` (`pi`, `sqrt`, `sin/cos/tan`,
   `log`). `sympify`-on-strings rejected: fails on `2x`, called out in SymPy best
   practices as accidental API. `parse_expr` uses `eval` → treat input as
   untrusted: length cap, no dunder access, map `SyntaxError`/`SympifyError` to
   friendly `PARSE_ERROR`.
3. **Verify by independent substitution**: `simplify(lhs.subs(x,c) - rhs.subs(x,c)) == 0`
   (structural `==` on the simplified difference, not on raw floats). Keep
   `exact` (SymPy `sstr`) and `approximate` (`N(x,15)`) as separate fields —
   never float-ify exacts. `factor()`/`expand()` used for their GCSE ops;
   `simplify()` avoided programmatically (heuristic, output not guaranteed).
4. Equations are `Eq` objects; bare expressions `== 0` per solver convention.

## Consequences

+ Deterministic error taxonomy; property test `substitute(solution)==True` holds.
+ `^`, `2x`, fractions work as students write them.
− Must maintain `local_dict`/transformation set; new functions added deliberately.
− `ConditionSet` cases need graceful UX copy (Phase 4), not silent failure.
