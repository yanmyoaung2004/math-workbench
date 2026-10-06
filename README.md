# Math Workbench

GCSE/O-Level Mathematics Tutor + Mathematical Workbench (Windows-first Tauri desktop app).

> **Authoritative spec:** [`product.md`](product.md) — product vision, stack, and phased plan.
> **Agent rules:** [`AGENTS.md`](AGENTS.md) — non-negotiable architecture and workflow.
> **Lifecycle log:** [`docs/lifecycle-log.md`](docs/lifecycle-log.md) — what was done, when, and in which commit.

## Core principle

Deterministic math engine is truth. LLM never solves or overrides verified results:

```text
input → parser → normalized repr → SymPy engine → verified result → steps → AI explanation → UI
```

## Stack

| Layer    | Choice (see `docs/architecture.md`)                          |
|----------|--------------------------------------------------------------|
| Desktop  | Tauri 2, Windows-first, Python sidecar via `externalBin`     |
| Frontend | React 19 + TS strict + Vite + Tailwind v4 + hand-rolled tokens + Zustand + TanStack Query + KaTeX + Plotly.js |
| Math     | Python + SymPy (truth), NumPy (graph sampling only) |
| Graphing | Plotly.js behind replaceable renderer abstraction            |
| Storage  | SQLite, offline-first                                        |
| AI       | `AIProvider` abstraction, async/non-blocking, never in solve path |

## Repo layout (target)

```text
docs/            Phase 0 SDLC docs + decisions + research evidence
math-engine/     Python hexagonal engine (src/workbench_math/ + tests/)
frontend/        (Phase 4) React app — premium UI, no math logic in components
src-tauri/       (Phase 7) Tauri shell + sidecar wiring
tests/           Golden corpus lives under math-engine/tests/golden/
```

Engine internals follow Clean + Hexagonal — see
[`docs/architecture.md`](docs/architecture.md) and
[`docs/decisions/0001-clean-hexagonal.md`](docs/decisions/0001-clean-hexagonal.md):

```text
math-engine/src/workbench_math/
  domain/        Entities/VOs: Expression, Solution, Step (stdlib only, no sympy import)
  ports/         ABCs: SolverPort, ParserPort (dependency inversion)
  application/   Use-cases: solve_linear, simplify_expression (primitives in/out)
  adapters/      sympy_solver, sympy_parser (only place sympy is imported)
  entrypoints/   json_cli (stdin JSON → stdout JSON, the future Tauri sidecar protocol)
```

## Current status (2026-10-06, tag `v1-mvp`)

- [x] Phase 0 — requirements, architecture, API contracts, testing strategy (`docs/`)
- [x] Phase 1 — engine: parser, simplify/expand/factorise, linear, quadratics
      (3 paths), systems 2x2, inequalities (sign-flip), all verified + stepped
- [x] Phase 2 — step engine + educational tier (order/rules/wording gates)
- [x] Phase 3 — graph engine: sampler (discontinuity-safe), analysis
      (roots/turning/asymptotes/gradient), Fraction-exact tables, intersections
- [x] Engine extras — SQLite history, deterministic practice + mastery,
      grounded AI (stub default, hint ladder, mistake classifier)
- [x] Phase 4 — premium UI: solver/graph/practice/history/settings over a
      typed engine service (sidecar under Tauri, mock in browser)
- [x] Phase 7 — Tauri shell compiles (11.8 MB exe, launch smoke-tested);
      30 MB PyInstaller sidecar speaks the protocol
- [ ] Shippable installers (needs NSIS/WiX) and in-app sidecar proof via
      `tauri dev` — recorded gaps in `docs/packaging.md`
- [ ] Post-V1 (per product): teacher analytics, adaptive ML, advanced modules

## Quickstart (engine)

```powershell
cd math-engine
uv venv; .\.venv\Scripts\Activate.ps1
uv pip install -e ".[dev]"
pytest -q                    # full suite: unit + integration + property + golden
pytest -q tests/unit         # fast domain/contract tests only
pytest -q tests/golden       # GCSE golden corpus
python -m workbench_math.entrypoints.json_cli < example.json
```

JSON CLI request example:

```json
{"op": "solve_linear", "input": "2x + 5 = 17"}
```

## Docs index

| Doc | Contents |
|-----|----------|
| `docs/requirements.md` | Functional/non-functional requirements, MVP gate, traceability to `product.md` |
| `docs/architecture.md` | Clean/Hexagonal layers, import rules, sidecar protocol, offline + AI-async design |
| `docs/math-engine.md` | Engine API contracts (JSON + Python), step schema, error taxonomy |
| `docs/testing.md` | Test pyramid, golden corpus layout, property-test invariants, edge-case matrix |
| `docs/development.md` | SDLC gates, git/commit workflow, definition of done |
| `docs/decisions/` | ADRs 0001–0003 (why hexagonal, why solveset/parse_expr, why sidecar+stdin/JSON) |
| `docs/research/` | Verbatim evidence from subagent research (sources included) |
| `docs/lifecycle-log.md` | Chronological build log with commit hashes |
