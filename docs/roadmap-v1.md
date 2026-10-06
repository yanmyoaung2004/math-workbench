# V1 Roadmap — Math Workbench to MVP-complete

DONE = product.md MVP (16 items) + quality bar (8 gates), all tested, committed
per task, verified executable. Teacher analytics/adaptive-ML stay post-V1.

## Stage A — Algebra completion (engine)

| Task | Scope | Acceptance |
|------|-------|------------|
| A1 quadratics | `solve_quadratic` (auto/formula/factorise/complete-square), discriminant teaching, verified steps | golden: factorable, formula, double root, no-real-roots, complex opt-in; property: substitute holds |
| A2 systems | `solve_system` 2x2 via linsolve, elimination steps, bindings result | golden: unique, no-solution, infinite; verified by substitution |
| A3 inequalities | `solve_inequality`, interval display (`x > 3`), sign-flip step + note | golden incl. negative-division flip, compound, empty, all-reals; test-point verification |

## Stage B — Step engine completion

B: completing-square + formula step chains, mistake-prone wording review,
educational tests (order/rule/terminology/difficulty). Exit: every Solver op
has stepped + educational coverage.

## Stage C — Graph engine (headless math; UI renders later)

| Task | Scope | Acceptance |
|------|-------|------------|
| C1 sampler | `sample_graph`: lambdify/numpy sampling, NaN/oo breaks, jump-split at asymptotes, pole exclusion via singularities | y=x^2, 1/x (no segment across x=0), tan (breaks), sqrt (domain cut) |
| C2 analysis | `analyze_graph`: roots, y-intercept, turning points, axis of symmetry, asymptotes — all cross-checked vs engine | x^2-4x+3 → roots 1,3; TP (2,-1); axis x=2 |
| C3 tables | `table_values` (Fraction-exact start/end/step), `solve_intersection` | tables match engine eval; 2x+4=10 ↔ intersection x=3 |

## Stage D — Persistence + practice (engine)

D1: SQLite history (`HistoryPort` + sqlite3 adapter + v1 migration, `WORKBENCH_DATA_DIR`).
D2: deterministic question generator (topic/difficulty/seed → solve+verify+store)
+ transparent mastery scoring. Exit: generated questions 100% verify.

## Stage E — AI abstraction (offline-safe)

E: `ProviderPort` + StubProvider (deterministic) + OpenAI-compatible REST provider
(stdlib urllib, key from env, proven against local stub HTTP server in tests) +
TutorService (grounded prompt) + HintService (L1–L5 from verified steps) +
MistakeService (bracket/sign/arithmetic classifiers). Exit: no network in tests;
engine works fully offline.

## Stage F — Premium frontend

F1 scaffold (Vite+React+TS strict+Tailwind+Zustand+Query, hand-rolled shadcn-style
tokens, system font stack for offline) + design-system doc.
F2 engine-service interface + Tauri sidecar impl + Mock impl (canned verified DTOs).
F3 screens: Solver, Graph (Plotly), Practice, History.
F4 vitest service tests + `tsc` + `vite build` green.

## Stage G — Tauri shell + packaging

G1 `src-tauri` (Tauri 2 + plugin-shell perms, `externalBin`, asset protocol).
G2 PyInstaller onefile sidecar → `binaries/workbench-engine-<triple>.exe`.
G3 `tauri build` (icons generated locally, ICO-wrapped PNG); installer tooling
(WiX/NSIS) documented if absent — raw exe + sidecar is the acceptance floor.

## Risks

- SymPy edge semantics (piecewise/nonlinear) → honest UNSOLVABLE, never guess.
- Frontend↔sidecar integration proven in Tauri runtime only; mock covers UI dev.
- AI cloud providers need user keys at runtime; stub is the default.
