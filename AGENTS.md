# Math Workbench — Agent Instructions

> V1 MVP complete (engine + graph + history + practice + AI + UI + Tauri shell).
> `product.md` is the product vision; `docs/` (requirements, architecture,
> math-engine contracts, testing, development, ai, frontend, packaging,
> roadmap-v1, decisions/) is the binding build record. Follow both; do not
> invent a different stack or scope.

## Non-negotiable architecture

- Deterministic math engine is authoritative: `input → parser → normalized repr → SymPy engine → verified result → step engine → AI explanation → UI`. LLM NEVER solves, overrides results, or edits verified steps; if engine can't solve, say so, don't hallucinate.
- Practice/question generation: generate parameters deterministically → solve + verify with engine → store expected answer → only then let LLM word it, and re-verify wording matches the math.
- AI tutor input must include verified result + steps + student attempt/mistakes/hints-shown; adapt language to GCSE/O-Level, no advanced terminology by default.

## Stack (don't substitute without measured reason)

- Desktop: Tauri 2, Windows-first, keep cross-platform structure. No microservices — local app + Python sidecar + SQLite only; move hot spots to Rust only if profiling proves it.
- Frontend: React 19 + TypeScript (strict, noUnusedLocals) + Vite + Tailwind v4 + hand-rolled tokens + Zustand (app state) + TanStack Query (async/data state) + KaTeX (bundled fonts) + Plotly.js. No math logic in components.
- Math: Python + SymPy (symbolic truth), NumPy (graph sampling only); no SciPy/Math.js until a proven need. Never duplicate solver logic client-side.
- Graphing: Plotly.js initially (normal plots sampled lines; WebGL/`scattergl` only for large datasets); keep renderer behind an abstraction so it can be replaced. Never connect segments across discontinuities/asymptotes; handle domain restrictions explicitly.
- Storage: local SQLite offline-first. Core (calculator, algebra, graphing, geometry/trig/stats, practice, history) must work offline; network only for cloud AI / sync / updates.
- AI: `ProviderPort` + stub (offline default) + OpenAI-compatible REST + `TutorService` (fallback) + deterministic hints + mistake classifier. Never block math UI on AI — solve and render immediately, generate explanations async.

## Build order (strict)

1. Phase 0: requirements + arch doc + engine API contracts + testing strategy. No UI.
2. Phase 1 math core before any complex UI: parser, simplifier, expand/factorise, linear → quadratics → systems/inequalities.
3. Step engine with explicit schema: `{operation, operand, before, after, rule, explanation, verification}` (+ optional `*_latex` twins) — steps rendered from this, not LLM prose.
4. Graph engine (parse, evaluate, sample, viewport/zoom/pan, table-of-values with user start/end/step).
5. UI around stable math APIs; no math logic inside components. Then AI tutor, then teacher tools, then packaging.
- V1/MVP scope only: expression input, linear+quadratic solvers, simplify/expand/factorise, steps, hints (L1 conceptual → L5 full solution, never auto-reveal), graphing + zoom/pan + table, history, basic practice, verification, offline, tests. Defer teacher analytics, adaptive ML (use transparent deterministic scoring), advanced modules.

## Math correctness conventions

- Verify every solver result by substitution into the original equation (exact semantics, not float where avoidable); flag/reject unverifiable results. Cross-check graph roots/intersections against engine.
- Always show exact + approximate separately (e.g. `√2` vs `1.414…`, `π/3` vs `1.047…`); never silently float-ify exacts.
- Curriculum mode: default to GCSE/O-Level; gate advanced analysis behind advanced flag.
- Mistake detector: compare student step vs expected transform → classify error → minimal correction + why (e.g. `2(x+3)→2x+6`), don't just say "wrong" or dump full solution.

## Testing (mandatory, write with code — not after)

- Unit (parser/normalizer/solver/steps/verify/stats/geometry), integration (`input→parse→engine→verify→steps→UI repr`), property (`substitute(solution)==True` for every solved equation), regression (every escaped math bug becomes a permanent test), UI (engine protocol + mock service tests, vitest).
- Golden corpus under `math-engine/tests/golden/*.yaml` with `input, exact/ops/error`. Always cover: zero, negatives, fractions/decimals, large/small coeffs, no/infinite/multiple solutions, division-by-zero, undefined/domain, discontinuities/asymptotes, malformed input.
- Pedagogical tests too: correct operation, order, terminology, difficulty-appropriateness — correct answer alone is not passing.
- Perf targets: startup ~<2s, simple solve ~<200ms, graph 60fps; debounce graph input, memoize/cache math, profile before optimizing.

## Working agreements

- Small coherent changes: inspect → plan → smallest change → test → review → report + next step. Never claim done with failing/hidden tests or untested math.
- Priority when conflicted: math correctness > educational correctness > security > reliability > performance > maintainability > polish.
- Code: small modules, strong types, no giant components/services, no magic numbers/hidden globals, no new deps without justification, no reimplementing symbolic math.
- Errors: user-friendly, no stack traces to students; internally log type/component/input/expression/timestamp, minimal student PII.
- Commits: `feat:|fix:|test:|perf:|docs:|chore:` scoped per feature (e.g. `feat: add linear equation solver`); docs to maintain: `README.md, docs/{architecture,math-engine,ai,testing,development,frontend,packaging}.md, docs/decisions/`.
