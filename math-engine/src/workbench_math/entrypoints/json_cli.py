"""stdio JSON-lines seam — the exact protocol the Tauri sidecar will speak (ADR-0003).

One JSON request per stdin line, one JSON response per stdout line (UTF-8).
Tracebacks never reach stdout; unexpected failures log to stderr and return
INTERNAL_ERROR with a student-safe message.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from dataclasses import asdict
from pathlib import Path

from ..adapters.sqlite_history import SqliteHistory
from ..adapters.sympy_parser import SymPyParser
from ..adapters.sympy_solver import SymPySolver
from ..application.solve_inequality import solve_inequality
from ..application.solve_linear import solve_linear
from ..application.solve_quadratic import solve_quadratic
from ..application.solve_system import solve_system
from ..application.transform import transform_expression
from ..domain.exceptions import MathEngineError, ValidationError
from ..domain.models import Binding, Domain, DomainInfo, Solution, Step
from ..graph.analysis import analyze
from ..graph.intersections import intersect
from ..graph.models import SampleRequest
from ..graph.sampler import sample
from ..graph.tables import table_values
from ..ai.hints import hint as hint_at_level
from ..ai.mistakes import classify as classify_mistake
from ..ai.openai_compat import OpenAICompatibleProvider
from ..ai.provider import StubProvider
from ..ai.tutor import TutorService
from ..practice.generator import DIFFICULTIES, TOPICS, generate_questions
from ..practice.mastery import Attempt, recommend, topic_mastery

_OPS = {"solve_linear", "solve_quadratic", "solve_system", "solve_inequality",
        "simplify", "expand", "factorise", "parse",
        "sample_graph", "analyze_graph", "table_values", "solve_intersection",
        "history_list", "history_clear", "practice_generate", "practice_score",
        "ai_explain", "ai_hint", "ai_mistake"}

# Ops whose verified results are recorded in local history (calculation log).
_SAVED_OPS = {"solve_linear", "solve_quadratic", "solve_system", "solve_inequality",
              "simplify", "expand", "factorise"}


def data_dir() -> Path:
    """Local data root: $WORKBENCH_DATA_DIR or ~/.math-workbench (offline)."""
    override = os.environ.get("WORKBENCH_DATA_DIR", "").strip()
    return Path(override) if override else Path.home() / ".math-workbench"


def _solution_to_response(op: str, solution: Solution, raw: str) -> dict:
    payload = asdict(solution)
    if op in _SAVED_OPS:
        try:
            store = SqliteHistory(data_dir() / "history.db")
            store.save(op, raw, payload["interpretation"],
                       list(payload["exact"]), payload["verification"])
        except Exception:
            traceback.print_exc(file=sys.stderr)  # history never breaks math
    return {"ok": True, "op": op, "interpretation": solution.interpretation, "result": payload}


def _solution_from_dict(payload: dict) -> Solution:
    """Rebuild a verified Solution from a previous solve response (AI context)."""
    try:
        steps = tuple(Step(**s) for s in payload.get("steps", []))
        info = payload.get("domain_info", {"domain": "reals"})
        bindings = tuple(Binding(**b) for b in payload.get("bindings", []))
        return Solution(
            interpretation=str(payload["interpretation"]),
            exact=tuple(payload.get("exact", ())),
            approximate=tuple(payload.get("approximate", ())),
            steps=steps,
            verification=str(payload.get("verification", "unverifiable")),
            domain_info=DomainInfo(domain=str(info.get("domain", "reals")),
                                   excluded=tuple(info.get("excluded", ()))),
            bindings=bindings,
        )
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValidationError("ai ops need a solution object from a solve response.") from exc


def _provider():
    kind = os.environ.get("WORKBENCH_AI_PROVIDER", "stub").strip().lower()
    if kind in ("openai", "openai_compat", "openrouter", "local"):
        return OpenAICompatibleProvider()
    return StubProvider()


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
    if op not in ("solve_system", "solve_intersection", "history_list",
                  "history_clear", "practice_generate", "practice_score",
                  "ai_explain", "ai_hint", "ai_mistake") and (
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
            return _solution_to_response(op, solve_system(equations, parser, solver, domain), "; ".join(equations))
        if op == "solve_inequality":
            return _solution_to_response(op, solve_inequality(raw, parser, solver, domain), raw)
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
            return _solution_to_response(op, solve_linear(raw, parser, solver, domain), raw)
        if op == "solve_quadratic":
            method = request.get("method", "auto")
            if not isinstance(method, str):
                return _error_response(op, ValidationError.code, "Method must be a string.")
            return _solution_to_response(
                op, solve_quadratic(raw, parser, solver, domain, method), raw
            )
        if op in ("simplify", "expand", "factorise"):
            return _solution_to_response(op, transform_expression(raw, op, parser, solver), raw)
        if op == "history_list":
            try:
                limit = int(request.get("limit", 50))
            except (TypeError, ValueError):
                return _error_response(op, ValidationError.code, "limit must be an integer.")
            store = SqliteHistory(data_dir() / "history.db")
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"entries": [asdict(e) for e in store.list_recent(limit)]}}
        if op == "history_clear":
            store = SqliteHistory(data_dir() / "history.db")
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"cleared": store.clear()}}
        if op == "practice_generate":
            topic = request.get("topic", "")
            difficulty = request.get("difficulty", "")
            try:
                n = int(request.get("n", 5))
                seed = int(request.get("seed", 0))
            except (TypeError, ValueError):
                return _error_response(op, ValidationError.code, "n and seed must be integers.")
            if topic not in TOPICS or difficulty not in DIFFICULTIES:
                return _error_response(
                    op, ValidationError.code,
                    f"Choose topic in {list(TOPICS)} and difficulty in {list(DIFFICULTIES)}.")
            questions = generate_questions(topic, difficulty, n, seed, parser, solver)
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"questions": [asdict(q) for q in questions]}}
        if op == "practice_score":
            raw_attempts = request.get("attempts", [])
            if not isinstance(raw_attempts, list):
                return _error_response(op, ValidationError.code, "Send attempts as a list.")
            try:
                attempts = tuple(
                    Attempt(topic=str(a["topic"]), correct=bool(a["correct"]),
                            hints_used=int(a.get("hints_used", 0)))
                    for a in raw_attempts
                )
            except (KeyError, TypeError, ValueError, AttributeError):
                return _error_response(op, ValidationError.code, "Each attempt needs topic, correct, hints_used.")
            mastery = topic_mastery(attempts)
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"mastery": mastery, "recommendation": recommend(mastery)}}
        if op in ("ai_explain", "ai_hint"):
            payload = request.get("solution", {})
            if not isinstance(payload, dict):
                return _error_response(op, ValidationError.code, "Send solution as an object from a solve response.")
            solution = _solution_from_dict(payload)
            if op == "ai_hint":
                try:
                    level = int(request.get("level", 1))
                    index = int(request.get("step_index", 0))
                except (TypeError, ValueError):
                    return _error_response(op, ValidationError.code, "level and step_index must be integers.")
                text = hint_at_level(solution, level, index)
                return {"ok": True, "op": op, "interpretation": solution.interpretation,
                        "result": {"hint": text, "level": level}}
            reply = TutorService(_provider()).explain(
                solution,
                str(request.get("question", "")),
                attempt=str(request.get("attempt", "")),
                mistake=str(request.get("mistake", "")),
                hints_shown=int(request.get("hints_shown", 0) or 0),
                level=str(request.get("level", "gcse")),
            )
            return {"ok": True, "op": op, "interpretation": solution.interpretation,
                    "result": {"explanation": reply.explanation, "provider": reply.provider}}
        if op == "ai_mistake":
            payload = request.get("expected_step", {})
            student_after = request.get("student_after", "")
            if not isinstance(payload, dict) or not isinstance(student_after, str):
                return _error_response(op, ValidationError.code, "Send expected_step object and student_after string.")
            try:
                expected = Step(**payload)
            except (TypeError, AttributeError):
                return _error_response(op, ValidationError.code, "expected_step is malformed.")
            mistake = classify_mistake(expected, student_after, solver.check_identity)
            if mistake is None:
                return {"ok": True, "op": op, "interpretation": expected.after,
                        "result": {"correct": True}}
            return {"ok": True, "op": op, "interpretation": expected.after,
                    "result": {"correct": False, "category": mistake.category,
                               "explanation": mistake.explanation,
                               "correction": mistake.correction}}
        return _error_response(op, ValidationError.code, f"Unhandled op {op!r}.")
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
