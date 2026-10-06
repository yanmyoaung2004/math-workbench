"""Architecture enforcement (ADR-0001): dependency direction is tested, not hoped for.

Rules:
- domain/      → stdlib + intra-domain relative imports only
- ports/       → stdlib + domain only
- application/ → stdlib + domain + ports only
- adapters/    → anything (ONLY layer allowed to touch sympy)
- entrypoints/ → stdlib + domain + ports + application + adapters (wiring)
"""

import ast
import sys
from pathlib import Path

import workbench_math

ROOT = Path(workbench_math.__file__).parent
STDLIB = set(sys.stdlib_module_names)

ALLOWED = {
    "domain": {"domain"},
    "ports": {"ports", "domain"},
    "application": {"application", "ports", "domain"},
    "adapters": None,  # unrestricted (sympy lives here)
    # graph/ is an engine-internal subdomain under the same discipline: it may
    # use domain/ports plus the shared sympy plumbing in adapters/_sympy_common,
    # but never adapter classes, application use-cases, or entrypoints.
    "graph": {"graph", "domain", "ports", "adapters"},
    # practice/ orchestrates application use-cases with a seeded stdlib RNG.
    "practice": {"practice", "application", "ports", "domain"},
    # ai/ explains verified DTOs; stdlib only (provider HTTP via urllib).
    "ai": {"ai", "domain", "ports"},
    "entrypoints": {"entrypoints", "adapters", "application", "ports", "domain", "graph", "practice", "ai"},
}
# Third-party distributions each layer may import (stdlib always allowed).
# Only adapters (None = any) and graph opt in; every other layer is stdlib-only.
THIRD_PARTY = {
    "adapters": None,  # any (sympy, numpy, ...)
    "graph": {"sympy", "numpy"},
}


def _resolve_relative(path: Path, level: int, module: str | None) -> tuple[str, ...]:
    """Resolve `from <level dots><module> import` to package-relative segments."""
    containing = path.relative_to(ROOT).parts[:-1]  # e.g. ("adapters",)
    up = level - 1
    base = containing[: len(containing) - up] if up <= len(containing) else ()
    extra = tuple(module.split(".")) if module else ()
    return base + extra


def test_import_direction():
    violations: list[str] = []
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if rel.parts[0] not in ALLOWED or "__pycache__" in rel.parts:
            continue
        layer = rel.parts[0]
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top == "workbench_math":
                        violations.append(f"{path}: absolute intra-package import")
                    elif top not in STDLIB and top != "__future__":
                        allowed_tp = THIRD_PARTY.get(layer, set())
                        if allowed_tp is None:
                            continue  # unrestricted layer (adapters)
                        if top not in allowed_tp:
                            violations.append(f"{path}: non-stdlib import {top!r}")
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    target = _resolve_relative(path, node.level, node.module)
                    if not target:
                        continue  # `from .. import x` → package root, harmless
                    dep_layer = target[0]
                    allowed = ALLOWED[layer]
                    if allowed is not None and dep_layer not in allowed:
                        violations.append(
                            f"{path}: {layer} must not depend on {dep_layer}"
                        )
                    # graph/ may only touch shared plumbing, never adapter classes
                    if layer == "graph" and dep_layer == "adapters":
                        if target[1:2] != ("_sympy_common",):
                            violations.append(
                                f"{path}: graph may only use adapters._sympy_common"
                            )
                elif node.module:
                    top = node.module.split(".")[0]
                    if top == "workbench_math":
                        rest = node.module.split(".")
                        dep_layer = rest[1] if len(rest) > 1 else ""
                        allowed = ALLOWED[layer]
                        if allowed is not None and dep_layer not in allowed:
                            violations.append(
                                f"{path}: {layer} must not depend on {dep_layer}"
                            )
                    elif top not in STDLIB and top != "__future__":
                        allowed_tp = THIRD_PARTY.get(layer, set())
                        if allowed_tp is None:
                            continue  # unrestricted layer (adapters)
                        if top not in allowed_tp:
                            violations.append(f"{path}: non-stdlib import {top!r}")
    assert not violations, "\n".join(violations)


def test_sympy_confined_to_engine_layers():
    """Only adapters/ and graph/ may import sympy or numpy (AST-precise)."""
    offenders: list[str] = []
    for path in sorted(ROOT.rglob("*.py")):
        parts = path.relative_to(ROOT).parts
        if "adapters" in parts or "graph" in parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(a.name.split(".")[0] == "sympy" for a in node.names):
                    offenders.append(str(path))
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".")[0] == "sympy":
                    offenders.append(str(path))
    assert not offenders, f"sympy/numpy leaked outside adapters+graph: {offenders}"
