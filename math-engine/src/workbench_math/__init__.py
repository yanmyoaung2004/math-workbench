"""Math Workbench deterministic engine — hexagonal core.

Layering (see docs/architecture.md + ADR-0001):
  domain/       pure value objects + pedagogy (stdlib only — never import sympy here)
  ports/        ABCs (dependency inversion)
  application/  use-cases orchestrating ports
  adapters/     ONLY layer allowed to import sympy
  entrypoints/  thin JSON/stdin seam (future Tauri sidecar protocol)
"""

__version__ = "0.1.0"
