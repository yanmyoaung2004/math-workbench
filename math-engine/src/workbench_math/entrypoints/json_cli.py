"""stdio JSON-lines seam — the exact protocol the Tauri sidecar will speak (ADR-0003).

One JSON request per stdin line, one JSON response per stdout line (UTF-8).
Tracebacks never reach stdout; unexpected failures log to stderr and return
INTERNAL_ERROR with a student-safe message.
"""

from __future__ import annotations

import json
import sys
import traceback
from dataclasses import asdict

from ..adapters.sympy_parser import SymPyParser
from ..adapters.sympy_solver import SymPySolver
from ..application.solve_inequality import solve_inequality
from ..application.solve_linear import solve_linear
from ..application.solve_quadratic import solve_quadratic
from ..application.solve_system import solve_system
from ..application.transform import transform_expression
from ..domain.exceptions import MathEngineError, ValidationError
from ..domain.models import Domain, Solution
from ..graph.analysis import analyze
from ..graph.intersections import intersect
from ..graph.models import SampleRequest
from ..graph.sampler import sample
from ..graph.tables import table_values

_OPS = {"solve_linear", "solve_quadratic", "solve_system", "solve_inequality",
        "simplify", "expand", "factorise", "parse",
        "sample_graph", "analyze_graph", "table_values", "solve_intersection"}


def _solution_to_response(op: str, solution: Solution) -> dict:
    payload = asdict(solution)
    return {"ok": True, "op": op, "interpretation": solution.interpretation, "result": payload}


def _error_response(op: str, code: str, message: str) -> dict:
    return {"ok": False, "op": op, "error": {"code": code, "message": message}}


def handle(request: dict) -> dict:
    op = request.get("op")
    if op not in _OPS:
        return _error_response(
            str(op), ValidationError.code,
            f"Unknown op {op!r}. Choose one of: {', '.join(sorted(_OPS))}.",
        )
    raw = request.get("input", "")
    if op not in ("solve_system", "solve_intersection") and (
        not isinstance(raw, str) or not raw.strip()
    ):
        return _error_response(op, ValidationError.code, "Please enter a mathematical expression or equation.")
    domain_raw = request.get("domain", "reals")
    try:
        domain = Domain(domain_raw)
    except ValueError:
        return _error_response(op, ValidationError.code, f"Unknown domain {domain_raw!r}. Choose reals or complex.")

    parser, solver = SymPyParser(), SymPySolver()
    try:
        if op == "parse":
            expr = parser.parse(raw)
            return {"ok": True, "op": op, "interpretation": expr.canonical,
                    "result": {"kind": expr.kind}}
        if op == "solve_system":
            equations = request.get("equations", [])
            if not isinstance(equations, list):
                return _error_response(op, ValidationError.code, "Send equations as a list of two strings.")
            return _solution_to_response(op, solve_system(equations, parser, solver, domain))
        if op == "solve_inequality":
            return _solution_to_response(op, solve_inequality(raw, parser, solver, domain))
        if op == "sample_graph":
            try:
                req = SampleRequest(
                    expression=raw,
                    x_min=float(request.get("x_min", -10.0)),
                    x_max=float(request.get("x_max", 10.0)),
                    n_points=int(request.get("n", 400)),
                )
            except (TypeError, ValueError):
                return _error_response(op, ValidationError.code, "x_min/x_max must be numbers and n an integer.")
            return {"ok": True, "op": op, "interpretation": raw,
                    "result": asdict(sample(req, parser))}
        if op == "analyze_graph":
            return {"ok": True, "op": op, "interpretation": raw,
                    "result": asdict(analyze(raw, parser))}
        if op == "table_values":
            start, end, step = (request.get(k, "") for k in ("start", "end", "step"))
            if not all(isinstance(v, str) for v in (start, end, step)):
                return _error_response(op, ValidationError.code, "Send start/end/step as strings.")
            return {"ok": True, "op": op, "interpretation": raw,
                    "result": asdict(table_values(raw, start, end, step, parser))}
        if op == "solve_intersection":
            inputs = request.get("inputs", [])
            if not isinstance(inputs, list) or len(inputs) != 2:
                return _error_response(op, ValidationError.code, "Send inputs as a list of two functions.")
            points = intersect(inputs[0], inputs[1], parser)
            return {"ok": True, "op": op, "interpretation": " ; ".join(inputs),
                    "result": {"points": [asdict(p) for p in points]}}
        if op == "solve_linear":
            return _solution_to_response(op, solve_linear(raw, parser, solver, domain))
        if op == "solve_quadratic":
            method = request.get("method", "auto")
            if not isinstance(method, str):
                return _error_response(op, ValidationError.code, "Method must be a string.")
            return _solution_to_response(
                op, solve_quadratic(raw, parser, solver, domain, method)
            )
        return _solution_to_response(op, transform_expression(raw, op, parser, solver))
    except MathEngineError as exc:
        return _error_response(op, exc.code, str(exc))
    except Exception:  # noqa: BLE001 — boundary: never leak internals to the student UI
        traceback.print_exc(file=sys.stderr)
        return _error_response(op, "INTERNAL_ERROR", "Something went wrong on our side. Try a simpler input.")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps(_error_response("unknown", ValidationError.code, "Each request must be one JSON object per line.")), flush=True)
            continue
        if not isinstance(request, dict):
            print(json.dumps(_error_response("unknown", ValidationError.code, "Each request must be a JSON object.")), flush=True)
            continue
        print(json.dumps(handle(request)), flush=True)


if __name__ == "__main__":
    main()
