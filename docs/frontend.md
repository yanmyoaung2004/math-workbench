# Frontend Architecture

Vite + React 19 + TypeScript strict + Tailwind v4 + Zustand + TanStack Query.
Plotly via `plotly.js-dist-min` (5 MB bundle — accepted for offline desktop;
lazy-load on the roadmap). No math logic in components: screens call the
engine service and render DTOs.

## Engine wiring

- `src/engine/types.ts` — DTO mirrors of `docs/math-engine.md`.
- `src/engine/protocol.ts` — FIFO `JsonLinesSession` over an injected
  transport (unit-tested with a fake; chunk framing requires `\n` terminators).
- `src/engine/TauriEngineService.ts` — production transport: `Command.sidecar(
  "binaries/workbench-engine").spawn()` with stream events on the **Command**
  (plugin-shell v2 attaches `stdout`/`stderr` there, not on the child).
- `src/engine/MockEngineService.ts` — canned verified DTOs for browser dev.
- Selection (`src/engine/index.ts`): explicit setting wins, else Tauri runtime
  (`__TAURI_INTERNALS__`/protocol/host) → sidecar, else mock with console
  warning on sidecar failure.

## State and data

Zustand holds screen/theme/engine-kind only. Server state (solutions, plots,
history) lives in TanStack Query mutations/queries keyed per screen.

## Screens

Solver (7 modes: linear/quadratic/inequality/system/simplify/expand/factorise,
interpretation echo, steps with why-notes, L1–L5 hints, mistake panel with
reflection gate, markdown copy, image import), Graph (Plotly + analysis +
Fraction-exact table + parameter sliders), Practice (generate/reveal/self-mark/
score with attempt recording, exam timer mode, worksheet builder),
Progress (mastery, unlocks, mistake patterns, review queue, streaks,
assignments), Reference (glossary, spec points, verified examples, spec
worksheets), History (list/clear), Settings (theme, engine, connection test).

Math rendering: `src/ui/Math.tsx` typesets the backend `*_latex` fields with
KaTeX (fonts bundled, offline-safe) and falls back to the plain canonical
string when LaTeX is missing or unusable — programmer notation (`*`, `**`)
never reaches students.

## Checks

`npx tsc -b` (strict, noUnusedLocals/Parameters) + `npm run build` +
`npx vitest run` (protocol framing, mock mapping, error codes).
