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
(sign-flip steps), expand/factorise hardening, golden corpus growth per edge matrix.
Premium UI stays deferred to Phase 4 by architectural design (stable engine first).

---

## 2026-10-06 — V1 end-to-end build (roadmap `docs/roadmap-v1.md`)

One commit per task, tests written with code, full suite green before moving on.
Engine: **157 passed, 1 skipped** (CPython 3.12, SymPy 1.14, numpy 2.5).
Frontend: `tsc -b` strict clean, `vite build` emits dist, vitest 7 passed.

| Commit | Task | Evidence |
|--------|------|----------|
| `f9e913b` | docs: V1 end-to-end roadmap (stages A–G, DONE = product MVP) | toolchain probed: Rust 1.98, VS BuildTools, WebView2, npm registry |
| `6e37d13` | chore: numpy dependency for graph sampling | venv 2.5.3 |
| `84c57b8` | A1 quadratics: auto/factorise/formula/complete-square + joined multi-root finals | golden + Hypothesis root invariants |
| `83efad2` | A2 systems 2x2: linsolve tags, elimination chains, named bindings, system substitution check | golden + planted-solution properties |
| `9f2f269` | A3 inequalities: interval phrases, flip step with reversal rule, test-point verification | golden + flip-always property |
| `c3ba564` | B educational tier: order/rules/wording gates, banned-terms list | 7 pedagogy tests |
| `dca0823` | C1 graph sampler: lambdify/numpy, jump + non-finite splits, viewport-clipped poles (infinite ImageSets never iterated) | 1/x exactly 2 segments; tan ≥ 3 |
| `e4f3122` | C2 analysis: roots/intercept/turning/axis/asymptotes/gradient, substitution cross-checks | x²−4x+3 full feature set |
| `cbb340e` | C3 tables (Fraction-exact, undefined cells), intersections, 4 graph protocol ops | e2e graph round-trips |
| `0261c7d` | D1 SQLite history: versioned schema, auto-save, list/clear ops, e2e home-dir isolation | migration-gate test |
| `39c6eb0` | D2 practice: seeded templates, 100% engine verification, transparent mastery + recommendation | all topics × difficulties |
| `318eaf7` | E AI: provider seam + stub + urllib REST (loopback-proven), grounded tutor with fallback, L1–L5 hints, mistake classifier | no network in tests |
| `224da61` | F1 frontend scaffold: Vite + React 19 + strict TS + Tailwind v4 + tokens | 121 packages |
| `ea76b9f` | F2 engine service: FIFO session, sidecar spawn, mock, zustand store | vitest protocol + mock |
| `976c545` | F3 screens: solver/graph/practice/history/settings; plugin-shell v2 fix (events on Command) | tsc + build green |
| `e361ffe` | F4 frontend docs + verification record | tsc, build, vitest |
| `c28f343` | G1 Tauri shell: sidecar contract, scoped capabilities, generated icons | PNG/ICO validated |
| `669cafc` | G2 PyInstaller onefile sidecar (30 MB), protocol smoke test through the binary | solve + sample via exe |
| `69d3f10` | G3 desktop exe links (11.8 MB), launch smoke test (alive + responding + titled) | MSVC via VsDevCmd |

**Tag `v1-mvp`.** Known gaps (recorded, not hidden): installer bundles need
NSIS/WiX; in-app sidecar spawn proven at `tauri dev`/bundle time
(docs/packaging.md). Post-V1 per product: teacher analytics, adaptive ML,
advanced modules. Branch note: repo init created `master`; active branch is
`main` (single-branch history, 50+ commits).

---

## 2026-10-07 — Independent audit + fixes (4 parallel audit agents)

Engine agent: 162 passed + all 21 ops probed + error taxonomy + hand-checks.
Frontend agent: tsc/vitest/build green, zero contract drift across 5 probed ops,
9 low-severity notes. Packaging agent: three-way sidecar string MATCH, fresh
bundle, but found the shipped sidecar stale (pre-latex → Solver crash) plus
stray smoke rows in the user DB. Docs agent: full drift table (contracts,
architecture, AGENTS, README, ADRs verified, lifecycle hashes resolve).

Fixes, one commit per task (all suites re-greened):

- pole-aware graph splitting + `tests/regression/test_tan_wide_viewport.py`
  (wide tan spanned π/2 — now 5 segments, no pole spanned)
- mid-expression LaTeX fold (`1·½` → `½`, digit/brace-guarded)
- frontend gaps: `parse()` + full mock fixtures, expand/factorise tabs,
  fieldset/aria-pressed, connection feedback, theme-subscribed plot, keys,
  overflow guards, history fallback
- docs reconciled (contracts v1, architecture, AGENTS, README, testing,
  packaging); `Cargo.lock` committed; `gen/` ignored
- sidecar rebuilt (30.1 MB) and re-smoked with isolated data dir
  (`\frac{x}{2} + \frac{1}{3}`, tan 5 segments/4 poles); stray history cleared;
  exe relinked; app relaunched and responding

Final gates: engine **164 passed, 1 skipped**; frontend tsc strict clean,
vitest **10 passed**, `vite build` green. **Tag `v1-mvp-verified`.**

---

## 2026-10-07 — Feature research implementation (report: `yma/`, private)

Implemented the research report's M1–M3 recommendations, one commit per task:

| Commit | Task | Evidence |
|--------|------|----------|
| `cf11c39` | M1: mastery gates (80% unlocks), `ai_reflect` gate, mixed sets | mastery + e2e tests |
| `b498f66` | Practice store: attempts, SM-2 reviews, assignments; dashboard/streak ops | store integration + e2e |
| `6e5348e` | Worksheets (verified export), 12 spec codes, per-rule concept notes, live-proved examples, glossary | rule-coverage test |
| `bd860a4` | OCR seam: refusing stub, capped base64, `ocr_parse` op | stub honesty tests |
| `e2845f9` | Progress + Reference screens; exam timer, attempt recording, worksheet builder, mistake panel with reflection gate, concept notes, markdown copy, image import, graph sliders | vitest 13 passed |

Final gates after rebuild: engine **187 passed, 1 skipped**; frontend tsc strict
clean, vitest **13 passed**, `vite build` green; sidecar rebuilt and re-smoked
(worksheet, concept, glossary, reflect ops); desktop exe relinked, app
relaunched and responding. `yma/` research folder gitignored (private).
