# Lifecycle Log — task-level build record (SDLC)

One commit per task (project rule). Hashes from `git log`.
Tags: `phase-0` (SDLC baseline), `phase-1a` (engine bootstrap + linear slice).

## 2026-10-06 — Initiation

| Commit | Task |
|--------|------|
| `30d8720` | chore: initialize git repository with Python/Node/Tauri gitignore |
| `ff10acb` | docs: product specification baseline (pre-existing vision, 2785 lines) |
| `2b0fa67` | docs: agent operating guide (`AGENTS.md`) |

## 2026-10-06 — Phase 0 gate: requirements → architecture → contracts

| Commit | Task |
|--------|------|
| `f514518` | docs: requirements with traceability to `product.md` + MVP gate |
| `78294d2` | docs: clean-hexagonal system architecture |
| `42754f0` | docs: math-engine API contracts v1a (JSON + Python + step vocabulary) |
| `09c800c` | docs: testing strategy, pyramid, invariants, edge matrix |
| `d6e6475` | docs: SDLC gates G0–G7, git workflow, research-before-code rule |

ADRs (one each — evidence first, synthesis in the ADR):

| Commit | Task |
|--------|------|
| `5042e2b` | ADR-0001: Clean + Hexagonal engine |
| `d60d577` | ADR-0002: SymPy solveset + parse_expr + substitution verify |
| `086653a` | ADR-0003: Tauri sidecar over stdio JSON-lines |

Research (3 parallel evidence-gathering subagents; raw findings archived,
nothing guessed — every API/config claim cites docs URLs):

| Commit | Task | Sources |
|--------|------|---------|
| `739c568` | SymPy fact sheet (SymPy 1.14 docs) | solveset, parsing, evalf, sets |
| `3a78130` | Tauri sidecar fact sheet (Tauri v2 docs) | sidecar, shell plugin, PyInstaller |
| `122ee8a` | Hexagonal fact sheet (Cockburn/Clean/Cosmic Python) | layers, import rules, pyramid |

| Commit | Task |
|--------|------|
| `d4ae6dd` | docs: README (stack, layout, status, quickstart, docs index) — **tag `phase-0`** |

## 2026-10-06 — Phase 1a gate: hexagonal engine + linear slice

| Commit | Task | Verification note |
|--------|------|-------------------|
| `ee4c72b` | feat: package scaffold (`src` layout, pyproject, pytest.ini) | imports resolve |
| `7a67d95` | feat: domain DTOs + error taxonomy (stdlib only) | — |
| `fa42c87` | feat: step builder + verify helpers | — |
| `3758a00` | feat: ParserPort/SolverPort ABCs + fact DTOs | — |
| `3955330` | feat: SymPy parsing adapter (implicit-mult, `^`, structure display, blacklist) | manual probes |
| `886ff9c` | feat: SymPy solver adapter (solveset tags, chains, checks) | manual probes |
| `ee3bc83` | feat: application use-cases (error mapping, Solution assembly) | — |
| `696ac4c` | feat: stdio JSON sidecar entrypoint | manual pipe test |

Bugs found by tests and fixed in-task (TDD discipline, no separate fix commits):

- `sstr(Eq)` renders `Eq(2*x, 8)` — introduced `eq_str` (`lhs = rhs`).
- SymPy auto-distributes `2*(x+3)` at parse — structure-preserving display via
  `evaluate=False` + structural Mul-over-Add detection (immune to `sqrt(2)`).
- Zero-poly `Poly(0,x).degree()` is `-oo`, not `0` — identity checked via `is_zero` first.
- `is_EmptySet` deprecated — `result is S.EmptySet`.
- `0x` tokenizes as hex — `TokenError` mapped to `PARSE_ERROR`.

| Commit | Task | Result |
|--------|------|--------|
| `b1c720e` | test: domain unit tests | pass |
| `f74aa3e` | test: architecture import rules | pass |
| `6520071` | test: contract tests with faked ports | pass |
| `8a398d3` | test: linear integration (8 forms, taxonomy, transforms) | pass |
| `c99f802` | test: Hypothesis substitution properties | pass |
| `1b5efbf` | test: golden corpus (14 rows) + runner | pass |
| `ba98ab4` | test: sidecar e2e + regression policy | pass |

Final gate run: **48 passed, 1 skipped** (`pytest`, `math-engine/`, CPython 3.12,
SymPy 1.14). The skip is a Phase-7 PyInstaller parity placeholder.

## Next — Phase 1b (planned, not started)

Quadratics (factor/formula/completing-square), systems (`linsolve`), inequalities
(sign-flip steps), same-side collect step, golden growth per edge matrix.
Premium UI stays deferred to Phase 4 by architectural design (stable engine first).
