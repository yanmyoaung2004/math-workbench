# Testing Strategy (Phase 0 binding)

Principle: **no math ships without tests written with the code — not after.**
`product.md` §§28–30 + stakeholder "test for everything".

## 1. Pyramid (where each tier lives)

```text
math-engine/tests/
  unit/           domain pure fns, step builder, contracts, arch import rules — no sympy/slow I/O, many
  integration/    parse→solve→verify→steps end-to-end through real SymPy adapter — per feature
  property/       Hypothesis: randomized equations, invariant substitute(solution)==True
  golden/         GCSE corpus: input/expected_answer/expected_steps/expected_domain (YAML)
  regression/     one file per fixed math bug: tests/regression/test_<issue>.py (never delete)
  e2e/    json_cli stdio round-trips (shipped); equation entry, graph, hints,
          practice flows covered via protocol + service tests
```

Plus `tests/educational/`: step order, rule names, GCSE wording, hint-level
progression — correct answer alone is NOT passing.

## 2. Commands

```powershell
pytest -q                       # everything (gate for every commit)
pytest -q tests/unit            # fast feedback (<5s target)
pytest -q tests/golden          # corpus only
pytest -q tests/property        # randomized (slower, run pre-push + CI)
pytest -q -k "linear"           # focused single-feature run
```

Coverage target: engine domain+application ≥95%; adapters ≥85% (SymPy branches excluded only with reason).

## 3. Invariants (property tests must assert)

1. `substitute(solution) ⟹ True` for every solved equation (exact semantics).
2. `exact[i]` re-parsed equals engine value; `approximate[i]` equals `N(exact[i])` within 1e-12.
3. Steps chain: `steps[0].before == interpretation`, `steps[k].after == steps[k+1].before`, last `after` contains solution.
4. `interpretation` re-parses to same canonical form (round-trip stability).
5. Error codes deterministic: same bad input → same `error.code` (no flaky messages asserted, only codes + key substrings).

## 4. Edge-case matrix (every solver × every row before MVP)

zero · negatives · fractions · decimals · irrationals (`sqrt(2)`) · large/small
coeffs · zero coefficient (`0x=5` → NO_SOLUTION, `0x=0` → INFINITE) · no/infinite/
multiple solutions · division-by-zero · undefined (`1/0`) · domain restrictions
(`1/x`, `log(x)`) · discontinuities/asymptotes (graph phase) · malformed input ·
`^` vs `**` · implicit mult (`2x`, `3(x+1)`) · `x=0` as solution (not "no solution").

Golden corpus covers this matrix; see `tests/golden/*.yaml` for the enrolled cases.

## 5. Regression policy

Every math bug that reaches a user gets a minimal reproducer under
`tests/regression/` in the SAME commit as the fix (append-only: never delete).
Bugs caught during development are covered in-tier instead (unit/integration/
golden) — e.g. the `Eq()` display, auto-expansion, and pole-spanning fixes —
with `tests/regression/` reserved for audit- or user-found escapes
(e.g. `test_tan_wide_viewport.py`).

## 6. What we defer (explicitly, not by neglect)

- UI tests (no UI until Phase 4; engine exposes `json_cli` e2e seam meanwhile).
- Perf benchmarks as tests (targets in `requirements.md` NFR-PERF-1; benchmark
  harness lands with graph engine where 60fps matters).
- Mutation testing (revisit post-MVP).
