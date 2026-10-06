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
    "entrypoints": {"entrypoints", "adapters", "application", "ports", "domain"},
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
                        if layer != "adapters":
                            violations.append(f"{path}: non-stdlib import {top!r}")
    assert not violations, "\n".join(violations)


def test_sympy_confined_to_adapters():
    """Only adapters/ may import the sympy distribution (AST-precise)."""
    offenders: list[str] = []
    for path in sorted(ROOT.rglob("*.py")):
        if "adapters" in path.relative_to(ROOT).parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(a.name.split(".")[0] == "sympy" for a in node.names):
                    offenders.append(str(path))
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".")[0] == "sympy":
                    offenders.append(str(path))
    assert not offenders, f"sympy leaked outside adapters/: {offenders}"
