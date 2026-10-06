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
│ (future) tauri commands, React services     │
└───────────────────┬────────────────────────┘
                    │ primitives + DTOs only
┌─ Application (use-cases) ──────────────────┐
│ application/solve_equation.py               │  orchestrate: parse→solve→verify→steps
│ application/simplify_expression.py          │
└──────┬──────────────────────┬──────────────┘
       │                      │ depends on ABCs (DIP)
┌─ Domain (pure, stdlib) ─┐ ┌─ Ports (ABCs) ─────────────┐
│ domain/models.py         │ │ ports/parser_port.py       │
│  Expression, Solution,   │ │ ports/solver_port.py       │
│  Step, HintLevel, Error  │ │ ports/verifier_port.py     │
│ domain/exceptions.py     │ └────────────────────────────┘
│ domain/curriculum.py     │                ▲ implements
└─────────────────────────┘ ┌─ Secondary/driven adapters ──────────────┐
                            │ adapters/sympy_parser.py  (import sympy) │
                            │ adapters/sympy_solver.py  (import sympy) │
                            │ adapters/inmemory_history.py (later SQLite)│
                            └──────────────────────────────────────────┘
```

### Import rules (enforced by `tests/unit/test_architecture.py`)

- `domain/` → stdlib + typing only. NEVER imports `sympy`, adapters, application.
- `ports/` → stdlib + domain only.
- `application/` → domain + ports only.
- `adapters/` → domain + ports + third-party (`sympy`). Only layer allowed to import `sympy`.
- `entrypoints/` → application + adapters (wiring) + stdlib. Only JSON/shape validation here.

Rationale: SymPy stays swappable; domain/steps testable without SymPy installed
(unit tier uses fakes); sidecar protocol depends on DTOs, not SymPy objects.

## 3. Request flow (the non-negotiable pipeline)

```text
raw string → ParserPort.parse (parse_expr, implicit-mult+convert_xor) → Expression (canonical str + latex-ish)
           → SolverPort.solve (solveset, domain=Reals default for GCSE) → raw solutions
           → VerifierPort.check (subs + simplify(a-b)==0, exact semantics)
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
- Request/response shapes: see `docs/math-engine.md`. Every response carries
  `ok`, `verification`, and machine-readable `error.code` on failure.

## 5. Frontend (Phase 4 — reserved, premium bar set now)

- React strict-TS + Vite + Tailwind + shadcn/ui; Zustand (app state), TanStack Query (async AI/data).
- No math logic in components: components call engine service (`solveLinear(input)`)
  returning `Solution` DTOs; Math.js allowed only for trivial client eval/units.
- Graphing behind `GraphRenderer` interface (Plotly.js first: sampled lines;
  `scattergl` only for large data). Renderer takes pre-sampled points + discontinuity
  breaks computed by engine — never auto-connects across gaps.
- Premium bar (explicit stakeholder ask): clarity-first workflow
  (enter → see interpretation → answer → expand steps → hint → visualize → practice),
  keyboard shortcuts, Desmos-feel pan/zoom, accessible graph text alternatives.
  Full design system lands with Phase 4; engine work must not pre-empt it.

## 6. Data (SQLite, offline-first)

Tables (Phase 1: `history` only; rest land with features):
`students, classes, questions, attempts, solutions, mistakes, topics, settings, history`.
Migrations via versioned SQL in `database/migrations/` (to be created with persistence adapter).

## 7. AI integration (Phase 5 — constraints binding now)

`AIProvider` interface + `TutorService/Explanation/Hints/QuestionGen/MistakeAnalysis`
use-cases. Every AI call receives verified engine output as ground truth in prompt;
output is post-checked (numbers/steps referenced must match engine DTOs).
AI failures degrade to "explanation unavailable" — math stays visible.

## 8. Quality attributes → tactics

| Attribute | Tactic |
|-----------|--------|
| Correctness | solveset+Reals default, substitution verification, property tests, golden corpus |
| Educ. value | Step DTOs, hint levels, mistake taxonomy, curriculum gate |
| Offline | Sidecar + SQLite, no CDN math, AI optional |
| Perf | Sync fast path <200ms, memoized engine, debounced graphs, AI off critical path |
| Testability | Ports+fakes, src-layout, pyramid (see `testing.md`) |
| Scalability | Hexagonal seams: new solvers/graph/AI providers are new adapters, domain untouched |
