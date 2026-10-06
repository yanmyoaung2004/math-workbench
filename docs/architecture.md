# Architecture — Math Workbench (Phase 0)

Decisions: `decisions/0001-clean-hexagonal.md`, `0002-sympy-*.md`, `0003-tauri-sidecar.md`.
Evidence: `research/`. Status: **baseline, 2026-10-06**.

## 1. System context (C1)

```text
Student/Teacher ──▶ Tauri shell (React premium UI, offline-first)
                        │  invoke/Channel/events (UI↔Rust)
                        │  shell-plugin → sidecar stdio/JSON (Rust↔Python)
                        ▼
                   Python sidecar: workbench_math (hexagonal engine, SymPy inside adapter only)
                        │  SQLite (local persistence: history, practice, classes later)
                        ▼
                   Cloud AI (optional, async, via AIProvider abstraction — never in solve path)
```

No microservices. No network for core math. See ADR-0003 for why sidecar over localhost HTTP.

## 2. Hexagonal + Clean mapping (ADR-0001)

```text
┌─ Primary/driving adapters ─────────────────┐
│ entrypoints/json_cli.py  (stdin JSON→stdout)│  ◀── Tauri sidecar spawns this
│ React services (typed DTO client + mock)    │
└───────────────────┬────────────────────────┘
                    │ primitives + DTOs only
┌─ Application (use-cases) ──────────────────┐
│ solve_linear|quadratic|system|inequality   │  orchestrate: parse→solve→verify→steps
│ transform.py (simplify|expand|factorise)   │
└──────┬──────────────────────┬──────────────┘
       │                      │ depends on ABCs (DIP)
┌─ Domain (pure, stdlib) ─┐ ┌─ Ports (ABCs) ─────────────┐
│ domain/models.py         │ │ ports/parser_port.py       │
│  Expression, Solution,   │ │ ports/solver_port.py       │
│  Step, Binding           │ │ ports/history_port.py      │
│ domain/exceptions|steps  │ └────────────────────────────┘
│ domain/verify.py         │                ▲ implements
└─────────────────────────┘ ┌─ Secondary/driven adapters ──────────────┐
                            │ adapters/sympy_parser|sympy_solver       │
                            │ adapters/sqlite_history (v1, user_version)│
                            │ adapters/latexing (presentation only)    │
                            └──────────────────────────────────────────┘
```

### Import rules (enforced by `tests/unit/test_architecture.py`)

- `domain/` → stdlib only. NEVER imports third-party, adapters, application.
- `ports/` → stdlib + domain only.
- `application/` → domain + ports only.
- `adapters/` → anything (ONLY unrestricted layer: sympy, sqlite3, urllib-adjacent).
- `graph/` → domain + ports + `adapters/_sympy_common` plumbing only; sympy+numpy allowed.
- `practice/` → application + ports + domain (seeded stdlib RNG orchestration).
- `ai/` → domain + ports; stdlib only (provider HTTP via urllib).
- `entrypoints/` → wires everything above into the JSON protocol (validation,
  history auto-save, LaTeX enrichment, AI/practice/graph dispatch).

Rationale: SymPy stays swappable; domain/steps testable without SymPy installed
(unit tier uses fakes); sidecar protocol depends on DTOs, not SymPy objects.

### Graph subdomain (`math-engine/.../graph/`)

Engine-internal subdomain under the same discipline: `graph/models.py` holds
stdlib-only DTOs; `graph/sampler.py` (+ analysis/tables later) may import
sympy+numpy and the shared plumbing `adapters/_sympy_common` only — never
adapter classes, application use-cases, or entrypoints. Enforced by
`tests/unit/test_architecture.py` (`ALLOWED["graph"]`, `THIRD_PARTY`).

## 3. Request flow (the non-negotiable pipeline)

```text
raw string → ParserPort.parse (parse_expr, implicit-mult+convert_xor) → Expression (canonical str + kind)
           → SolverPort.solve_* (solveset, domain=Reals default for GCSE) → facts + set_tag
           → application maps tags to error codes; verifier checks (subs + simplify(a-b)==0, exact semantics)
           → StepBuilder (domain pure fn: operation/operand/before/after/rule/explanation/verification)
           → Solution{exact[], approximate[], steps[], verification} → JSON → UI renders immediately
                                                                      → AI explains async (Phase 5)
```

Malformed input → `ParseError` (friendly message, no traceback).
Engine cannot solve (`ConditionSet`/NotImplemented) → `UnsolvableError` ("could not solve automatically"), never a guess.

## 4. Sidecar protocol (ADR-0003 summary)

- Packaging: PyInstaller `--onefile` → `src-tauri/binaries/workbench-engine-<triple>[.exe]`,
  declared in `bundle.externalBin`, invoked via `@tauri-apps/plugin-shell` `Command.sidecar`.
- Transport V1: **long-lived stdio JSON-lines** (`spawn()` + `child.write()`), one JSON
  request per line, one JSON response per line. Avoids port conflicts and localhost
  security surface; localhost HTTP reserved as fallback if profiling demands it.
- Request/response shapes: see `docs/math-engine.md`. Solve/transform responses
  carry `ok`, `verification`, and machine-readable `error.code` on failure;
  graph/history/practice/AI ops return their own result shapes (no fake
  verification field).

## 5. Frontend (shipped — premium bar held)

- React strict-TS + Vite + Tailwind v4 + hand-rolled tokens (no shadcn dependency);
  Zustand (app state), TanStack Query (async AI/data); KaTeX (bundled fonts, offline).
- No math logic in components: components call the engine service
  (`solveLinear(input)`) returning DTOs; no client-side solver duplication.
- Graphing via Plotly.js traces built from engine `segments` (discontinuity
  breaks computed by the engine — never auto-connected across gaps).
- Premium bar (explicit stakeholder ask): clarity-first workflow
  (enter → see interpretation → answer → expand steps → hint → visualize → practice),
  keyboard shortcuts, Desmos-feel pan/zoom, accessible graph text alternatives.
  Full design system lands with Phase 4; engine work must not pre-empt it.

## 6. Data (SQLite, offline-first)

Shipped: `history` table via `adapters/sqlite_history.py`, schema v1 gated by
`PRAGMA user_version` (future migrations bump it — no separate `database/`
folder). Teacher-mode tables (`students, classes, …`) land post-V1.

## 7. AI integration (shipped with offline default)

`ProviderPort` + `StubProvider` + OpenAI-compatible REST + `TutorService` with
fallback + deterministic `hints.py` ladder + `mistakes.py` classifier
(see `docs/ai.md`). Every AI call receives verified engine output as ground
truth; failures degrade to the deterministic fallback — math stays visible.

## 8. Quality attributes → tactics

| Attribute | Tactic |
|-----------|--------|
| Correctness | solveset+Reals default, substitution verification, property tests, golden corpus |
| Educ. value | Step DTOs, hint levels, mistake taxonomy, curriculum gate |
| Offline | Sidecar + SQLite, no CDN math, AI optional |
| Perf | Sync fast path <200ms, memoized engine, debounced graphs, AI off critical path |
| Testability | Ports+fakes, src-layout, pyramid (see `testing.md`) |
| Scalability | Hexagonal seams: new solvers/graph/AI providers are new adapters, domain untouched |
