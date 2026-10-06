# Development Process & SDLC Gates

How this repo is built: `product.md` §DEVELOPMENT-PROCESS + real phase gates.
Every phase ends with docs + green tests + a tagged commit.

## 1. Lifecycle (waterfall of phases, agile inside each)

```text
0 Requirements → 1 Arch+Contracts → 2 Math core → 3 Steps → 4 Graph engine
  → 5 UI (premium) → 6 AI tutor → 7 Teacher tools → 8 Packaging/hardening
```

Current position: **Phase 1a done** (engine bootstrap + linear slice). See
`lifecycle-log.md` for the dated gate record.

Inside a phase: `inspect → plan → smallest coherent change → test → review →
fix → document decision → report + next step` (AGENTS.md working agreements).

## 2. Phase gates (definition of done)

| Gate | Exit criteria |
|------|---------------|
| G0 requirements | `requirements.md` baselined, MVP gate §4 written, traceability to `product.md` |
| G1 architecture | `architecture.md` + `math-engine.md` contracts + ADRs merged; import rules test green |
| G2 math core (per solver) | solver + verifier + golden cases + property tests green; edge-matrix row covered |
| G3 steps | step schema test + educational tests (order/rule/wording) green |
| G4 graph | sampled renderer + discontinuity breaks + table-of-values tested (no UI needed) |
| G5 UI | premium design system + flows tested (equation entry, hints, practice, graph pan/zoom) |
| G6 AI | tutor grounded on verified DTOs; hallucination probes (unverifiable → honest refusal) green |
| G7 packaging | clean-install, startup, offline, migration tests on Windows |

No phase is "done" with failing/hidden tests or untested math. Correctness outranks speed.

## 3. Priority when conflicted

`math correctness > educational correctness > security > reliability > performance > maintainability > polish` (product.md §AGENT-OPERATING-MODE).

## 4. Git workflow (stakeholder requirement: commit every task/phase)

- Branch: `master` for now (single engineer + agents); feature branches when parallel work starts (`feat/<slug>`).
- Commit every coherent task; every phase gate is its own commit. Never bundle unrelated changes.
- Format: `type: short imperative` — `feat|fix|test|docs|chore|perf|refactor`.
  Examples: `feat: add linear equation solver`, `fix: handle negative inequality division`,
  `test: add quadratic regression cases`, `docs: baseline phase 0 SDLC`.
- Each commit: what + why (1–2 lines) + test evidence (`pytest -q` result) in the body for math changes.
- Tags: `phase-0`, `phase-1a`, … at gate commits.

## 5. Research-before-code rule (stakeholder requirement: facts, not guesses)

If the answer isn't in repo docs/config, search before implementing (SymPy docs,
Tauri docs, Cosmic Python/Clean sources). Store evidence in `docs/research/`,
cite sources in the ADR, never invent API signatures. Subagents may be used for
parallel evidence gathering; their raw output is archived, the ADR holds the synthesis.

## 6. Premium-UI rule (stakeholder requirement)

UI work is deferred to Phase 4 **by architectural design** (stable engine first),
not deprioritized. When it lands: design system + tokens first, Desmos-grade
interaction feel, keyboard-first, accessible. No placeholder-grade UI ships as "done".
