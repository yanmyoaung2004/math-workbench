# Requirements — Math Workbench (Phase 0)

Source: `product.md` §§ 1–21, 27–33. Status: **baseline, 2026-10-06**.
Every requirement traces to a `product.md` section (column `SRC`).

## 1. Stakeholders & users

| ID | Stakeholder | Needs |
|----|-------------|-------|
| ST-1 | GCSE/O-Level student | Correct answers, why-steps, hints (not answers), graphs, practice, offline |
| ST-2 | Teacher | Worksheets/quizzes, classes, mistake + weakness analytics |
| ST-3 | Agent/maintainer | Deterministic engine, tested contracts, no math in UI |

## 2. Functional requirements

### 2.1 Mathematical input (SRC §1, §33-UX)

| ID | Requirement |
|----|-------------|
| FR-IN-1 | Accept expression/equation strings: implicit mult (`2x`), `^` for power, fractions, decimals, `pi`, `sqrt` |
| FR-IN-2 | Show parsed interpretation back before solving (never silently misinterpret) |
| FR-IN-3 | Reject malformed/unsafe input with friendly error; never expose stack traces (SRC §32-ERR) |

### 2.2 Algebra core — MVP (SRC §§2–3, 27-P1, MVP list)

| ID | Requirement | Phase |
|----|-------------|-------|
| FR-ALG-1 | Simplify, collect like terms, expand, factorise | 1a (done: linear slice) / 1b |
| FR-ALG-2 | Linear equations incl. brackets + fractions, with steps | 1a ✅ |
| FR-ALG-3 | Quadratics: factorisation, formula, completing square | 1b |
| FR-ALG-4 | Simultaneous systems, inequalities (incl. sign-flip rule teaching) | 1b+ |
| FR-ALG-5 | Exact + approximate displayed separately (`√2` vs `1.414…`) | 1a ✅ |

### 2.3 Step engine (SRC §§2, 27-P2)

| ID | Requirement |
|----|-------------|
| FR-STEP-1 | Steps are data, not prose: `{operation, operand, before, after, rule, explanation, verification}` |
| FR-STEP-2 | Frontend renders from that schema; LLM may rephrase, never alter math |
| FR-STEP-3 | Every step carries verification status (substitution-checked) |

### 2.4 Verification (SRC §28-verify)

| ID | Requirement |
|----|-------------|
| FR-VER-1 | Substitute every equation solution into original (`simplify(a-b)==0` semantics); reject/flag unverifiable |
| FR-VER-2 | Cross-check graph roots/intersections against engine |
| FR-VER-3 | If engine cannot solve → say so explicitly; no hallucinated solution |

### 2.5 Graphing (SRC §§4–8, graph spec)

FR-GR-1..7 (deferred to Phase 3, contracts reserved): linear→trig + transforms,
zoom/pan, domain/range restriction, **no segment connection across
discontinuities**, feature analysis (roots, intercepts, turning points, symmetry),
table-of-values with user start/end/step, equation↔graph intersection view.

### 2.6 Hints / mistakes / practice (SRC §§15–18)

| ID | Requirement |
|----|-------------|
| FR-HINT-1 | 5 progressive hint levels (conceptual → full solution); never auto-reveal |
| FR-MIS-1 | Classify student error vs expected transform, minimal correction + why |
| FR-PRAC-1 | Deterministic template generation → engine solve+verify → store answer → optional LLM wording → re-verify wording matches math |
| FR-ADP-1 | Transparent deterministic mastery scoring first; no ML model in V1 |

### 2.7 AI tutor (SRC §§20–21, AI spec) — Phase 5, constraints apply now

Tutor context MUST include: verified result + steps + student attempt + detected
mistake + hints shown + level/topic. AI MUST NOT override engine, invent answers,
modify steps, or fabricate formulas/curriculum.

### 2.8 Teacher mode (SRC §19) — post-MVP

Students/classes/assignments/worksheets (PDF export, verified before export),
progress + mistake analytics. Deferred until MVP stable.

## 3. Non-functional requirements

| ID | Requirement (SRC) |
|----|-------------------|
| NFR-OFF-1 | Core (calc, algebra, graph, geometry/trig/stats, practice, history) works offline; network only for cloud AI/sync/updates |
| NFR-PERF-1 | Startup <2s; simple solve <200ms; graph 60fps; AI async, debounced graph input, memoized math |
| NFR-A11Y-1 | Keyboard nav, readable math typography, contrast, focus states, screen-reader labels, accessible graph descriptions |
| NFR-ERR-1 | Friendly errors; internal log {type, component, input, expression, timestamp}, minimal student PII |
| NFR-CURR-1 | Default GCSE/O-Level; advanced analysis behind explicit flag |
| NFR-ARCH-1 | No microservices; local Tauri + Python sidecar + SQLite; Rust only if profiling proves need |
| NFR-QUAL-1 | Strict TS, small modules, no giant components/services, no magic numbers/hidden globals, no unjustified deps, no reimplemented symbolic math |
| NFR-PREM-1 | Premium UI when Phase 4 lands (per stakeholder request): clarity-first, keyboard shortcuts, no dialog/animation excess — Desmos-level graph feel is the bar |

## 4. MVP acceptance gate (SRC §MVP-QUALITY — all must hold)

1. No incorrect equation answers; 2. steps never contradict answer;
3. graphs mathematically correct; 4. no crash on malformed input;
5. AI never invents math; 6. tests present (unit+integration+property+regression);
7. UI never blocks on compute/AI; 8. core works offline;
9. no silent misinterpretation of expressions.

## 5. Out of scope for V1

Teacher analytics, adaptive ML, advanced modules (calculus beyond GCSE gradient,
matrices beyond basics), cloud sync, custom WebGL renderer (Plotly first behind abstraction).
