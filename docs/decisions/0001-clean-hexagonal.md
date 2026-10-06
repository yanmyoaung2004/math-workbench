# ADR-0001: Clean + Hexagonal for the math engine

Date: 2026-10-06 · Status: **accepted** · Sources: `../research/hexagonal-facts.md`

## Context

`product.md` sketches `math-engine/{parser,solvers,verification,steps,…}` but
doesn't fix dependency direction. Stakeholder requires Clean + Hexagonal for
scalability (new solvers, graph engine, AI providers, SQLite persistence must
not ripple into tested core). SymPy must stay swappable; domain/steps must be
testable without SymPy.

## Decision

Adopt Cosmic-Python-style hexagonal layering inside `math-engine/src/workbench_math/`:

- `domain/` — pure value objects + exceptions + verification functions (stdlib only).
- `ports/` — `ParserPort`, `SolverPort`, `VerifierPort` ABCs (dependency inversion).
- `application/` — use-cases orchestrating ports (`solve_linear`, `simplify_expression`).
- `adapters/` — `sympy_parser`, `sympy_solver` (ONLY layer importing `sympy`).
- `entrypoints/` — `json_cli` (thin JSON shape validation + status codes, the future Tauri sidecar).

Enforce with `tests/unit/test_architecture.py` import assertions (module-level
`import sympy` forbidden outside `adapters/`).

## Consequences

+ SymPy/DB/UI replaceable behind ports; fast SymPy-free unit tier via fakes.
+ Step schema and verification logic live in domain — stable for UI/AI contracts.
− More files than a flat script; editable `src/`-layout install required for dev.
− Discipline needed: contributors must route new I/O through a port, not ad-hoc imports.

## Alternatives rejected

- Flat `solver.py` calling SymPy directly: fastest day-one, but every new
  backend (NumPy numeric, SQLite history) would tangle into tested logic.
- Full DDD tactical stack (aggregates, UoW, event bus): overkill for a
  stateless equation engine; revisit only if teacher-mode persistence demands it.
