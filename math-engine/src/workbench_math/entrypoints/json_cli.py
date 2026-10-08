"""stdio JSON-lines seam — the exact protocol the Tauri sidecar will speak (ADR-0003).

One JSON request per stdin line, one JSON response per stdout line (UTF-8).
Tracebacks never reach stdout; unexpected failures log to stderr and return
INTERNAL_ERROR with a student-safe message.
"""

from __future__ import annotations

import json
import os
from datetime import date
import sys
import traceback
from dataclasses import asdict
from pathlib import Path

from ..adapters.sqlite_history import SqliteHistory
from ..adapters.sqlite_practice import SqlitePractice
from ..adapters.latexing import (
    latex_analysis,
    latex_of,
    latex_point,
    latex_solution,
    latex_table,
)
from ..adapters.sympy_parser import SymPyParser
from ..adapters.sympy_solver import SymPySolver
from ..application.calculus import differentiate_expression, integrate_expression
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
from ..linalg.matrices import (
    cross as vector_cross,
    determinant as matrix_determinant,
    dot as vector_dot,
    inverse as matrix_inverse,
    magnitude as vector_magnitude,
    multiply as matrix_multiply,
)
from ..ai.hints import hint as hint_at_level
from ..ai.mistakes import classify as classify_mistake
from ..ai.ocr import decode_image, ocr_provider
from ..ai.openai_compat import OpenAICompatibleProvider
from ..ai.provider import AIProviderError, StubProvider
from ..ai.tutor import TutorService
from ..practice.at_risk import detect as detect_risk
from ..practice.bkt import BKTParams, track as bkt_track, update as bkt_update
from ..practice.concepts import concept_for
from ..practice.examples import examples_for
from ..practice.generator import DIFFICULTIES, TOPICS, generate_questions
from ..practice.glossary import GLOSSARY
from ..practice.reviews import next_review, quality_for, streak_days
from ..practice.specmap import SPEC_POINTS, resolve_spec
from ..practice.worksheet import build_worksheet
from ..practice.mastery import (
    Attempt,
    bkt_gated_levels,
    recommend,
    topic_mastery,
    unlocked_difficulties,
)
from ..practice.next import choose_difficulty, solve_rates

_OPS = {"solve_linear", "solve_quadratic", "solve_system", "solve_inequality",
        "simplify", "expand", "factorise", "parse",
        "sample_graph", "analyze_graph", "table_values", "solve_intersection",
        "history_list", "history_clear", "practice_generate", "practice_score",
        "ai_explain", "ai_hint", "ai_mistake", "ai_reflect",
        "practice_record", "practice_dashboard", "review_due", "review_answer",
        "progress_streak", "assignment_create", "assignment_list", "practice_override",
        "practice_next",
        "worksheet_generate", "spec_map", "concept_note", "practice_examples",
        "glossary_list", "glossary_get", "ocr_parse",
        "differentiate", "integrate", "definite_integrate",
        "matrix_multiply", "matrix_determinant", "matrix_inverse",
        "vector_dot", "vector_cross", "vector_magnitude"}

# Ops whose verified results are recorded in local history (calculation log).
_SAVED_OPS = {"solve_linear", "solve_quadratic", "solve_system", "solve_inequality",
              "simplify", "expand", "factorise",
              "differentiate", "integrate", "definite_integrate"}


def _today() -> str:
    return date.today().isoformat()


def data_dir() -> Path:
    """Local data root: $WORKBENCH_DATA_DIR or ~/.math-workbench (offline)."""
    override = os.environ.get("WORKBENCH_DATA_DIR", "").strip()
    return Path(override) if override else Path.home() / ".math-workbench"


def _solution_to_response(op: str, solution: Solution, raw: str) -> dict:
    payload = asdict(latex_solution(solution))
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
                  "ai_explain", "ai_hint", "ai_mistake", "ai_reflect",
                  "practice_record", "practice_dashboard", "review_due",
                  "review_answer", "progress_streak", "assignment_create",
                  "assignment_list", "practice_override", "practice_next", "worksheet_generate", "spec_map",
                  "concept_note", "practice_examples", "glossary_list",
                  "glossary_get", "ocr_parse", "differentiate", "integrate",
                  "definite_integrate", "matrix_multiply", "matrix_determinant",
                  "matrix_inverse", "vector_dot", "vector_cross",
                  "vector_magnitude") and (
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
        if op == "differentiate":
            return _solution_to_response(op, differentiate_expression(raw, parser, solver), raw)
        if op == "integrate":
            return _solution_to_response(op, integrate_expression(raw, parser, solver), raw)
        if op == "definite_integrate":
            a = request.get("a", "")
            b = request.get("b", "")
            if not isinstance(a, str) or not isinstance(b, str):
                return _error_response(op, ValidationError.code, "Send bounds a and b as strings.")
            return _solution_to_response(op, integrate_expression(raw, parser, solver, a, b), raw)
        if op in ("matrix_multiply", "matrix_determinant", "matrix_inverse",
                  "vector_dot", "vector_cross", "vector_magnitude"):
            matrix_a = request.get("matrix_a", [])
            matrix_b = request.get("matrix_b", [])
            vector_a = request.get("vector_a", [])
            vector_b = request.get("vector_b", [])
            try:
                if op == "matrix_multiply":
                    res = matrix_multiply(matrix_a, matrix_b)
                elif op == "matrix_determinant":
                    res = matrix_determinant(matrix_a)
                elif op == "matrix_inverse":
                    res = matrix_inverse(matrix_a)
                elif op == "vector_dot":
                    res = vector_dot(vector_a, vector_b)
                elif op == "vector_cross":
                    res = vector_cross(vector_a, vector_b)
                else:
                    res = vector_magnitude(vector_a)
            except MathEngineError as exc:
                return _error_response(op, exc.code, str(exc))
            return {"ok": True, "op": op, "interpretation": res.input_display,
                    "result": asdict(res)}
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
                    "result": asdict(latex_analysis(analyze(raw, parser)))}
        if op == "table_values":
            start, end, step = (request.get(k, "") for k in ("start", "end", "step"))
            if not all(isinstance(v, str) for v in (start, end, step)):
                return _error_response(op, ValidationError.code, "Send start/end/step as strings.")
            return {"ok": True, "op": op, "interpretation": raw,
                    "result": asdict(latex_table(table_values(raw, start, end, step, parser)))}
        if op == "solve_intersection":
            inputs = request.get("inputs", [])
            if not isinstance(inputs, list) or len(inputs) != 2:
                return _error_response(op, ValidationError.code, "Send inputs as a list of two functions.")
            points = intersect(inputs[0], inputs[1], parser)
            return {"ok": True, "op": op, "interpretation": " ; ".join(inputs),
                    "result": {"points": [asdict(latex_point(p)) for p in points]}}
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
            entries = []
            for entry in store.list_recent(limit):
                payload = asdict(entry)
                payload["interpretation_latex"] = latex_of(entry.interpretation)
                payload["exact_latex"] = [latex_of(e) for e in entry.exact]
                entries.append(payload)
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"entries": entries}}
        if op == "history_clear":
            store = SqliteHistory(data_dir() / "history.db")
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"cleared": store.clear()}}
        practice = SqlitePractice(data_dir() / "practice.db")
        if op == "practice_record":
            topic = str(request.get("topic", ""))
            difficulty = str(request.get("difficulty", ""))
            if topic not in TOPICS or difficulty not in DIFFICULTIES:
                return _error_response(op, ValidationError.code, "Unknown topic or difficulty.")
            try:
                hints = int(request.get("hints_used", 0))
            except (TypeError, ValueError):
                return _error_response(op, ValidationError.code, "hints_used must be an integer.")
            correct = bool(request.get("correct", False))
            row = practice.record_attempt(
                topic, difficulty, correct, hints, str(request.get("mistake", "")))
            prior_p, prior_n = practice.get_bkt(topic)
            practice.set_bkt(topic, bkt_update(prior_p, correct), prior_n + 1)
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"recorded": row}}
        if op == "practice_dashboard":
            attempts = practice.recent_attempts()
            scored = tuple(
                Attempt(topic=a.topic, correct=a.correct, hints_used=a.hints_used,
                        difficulty=a.difficulty) for a in attempts)
            mastery = topic_mastery(scored)
            by_mistake: dict[str, int] = {}
            for a in attempts:
                if a.mistake:
                    by_mistake[a.mistake] = by_mistake.get(a.mistake, 0) + 1
            topics = sorted({a.topic for a in scored}) or list(TOPICS)
            bkt: dict[str, float] = {}
            gates: dict[str, list[str]] = {}
            for topic in topics:
                if topic == "mixed":
                    continue
                p, n = practice.get_bkt(topic)
                bkt[topic] = round(p, 4)
                gates[topic] = bkt_gated_levels(p, n)
            counts: dict[tuple[str, str], list] = {}
            for a in attempts:
                key = (a.topic, a.difficulty or "basic")
                entry = counts.setdefault(key, [0, 0])
                entry[0] += int(a.correct)
                entry[1] += 1
            rates = solve_rates({k: (v[0], v[1]) for k, v in counts.items()})
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"mastery": mastery,
                               "recommendation": recommend(mastery),
                               "unlocked": {t: unlocked_difficulties(t, scored)
                                            for t in sorted({a.topic for a in scored})},
                               "bkt": bkt,
                               "bkt_gates": gates,
                               "difficulty_rates": rates,
                               "by_mistake": by_mistake,
                               "at_risk": [asdict(f) for f in detect_risk(attempts)],
                               "attempts": len(attempts)}}
        if op == "review_due":
            today = str(request.get("today", ""))
            if not today:
                today = _today()
            try:
                limit = int(request.get("limit", 20))
            except (TypeError, ValueError):
                return _error_response(op, ValidationError.code, "limit must be an integer.")
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"due": [asdict(r) for r in practice.due_reviews(today, limit)]}}
        if op == "review_answer":
            prompt = str(request.get("prompt", ""))
            topic = str(request.get("topic", ""))
            if not prompt or topic not in TOPICS:
                return _error_response(op, ValidationError.code, "Send prompt and a known topic.")
            try:
                hints = int(request.get("hints_used", 0))
                ease = float(request.get("ease", 2.5))
                interval = int(request.get("interval_days", 0))
            except (TypeError, ValueError):
                return _error_response(op, ValidationError.code, "hints_used, ease and interval_days must be numbers.")
            today = str(request.get("today", ""))
            if not today:
                today = _today()
            quality = quality_for(bool(request.get("correct", False)), hints)
            due, new_interval, new_ease = next_review(ease, interval, quality, today)
            practice.upsert_review(prompt, topic, due, new_interval, new_ease)
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"next_due": due, "interval_days": new_interval, "ease": new_ease}}
        if op == "progress_streak":
            dates = tuple(a.timestamp for a in practice.recent_attempts(1000))
            today = str(request.get("today", ""))
            if not today:
                today = _today()
            streak, active = streak_days(dates, today)
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"streak_days": streak, "active_today": active}}
        if op == "assignment_create":
            title = str(request.get("title", "")).strip()
            topic = str(request.get("topic", ""))
            difficulty = str(request.get("difficulty", ""))
            if not title or topic not in TOPICS or difficulty not in DIFFICULTIES:
                return _error_response(op, ValidationError.code, "Send title and known topic/difficulty.")
            try:
                n = int(request.get("n", 5))
                seed = int(request.get("seed", 0))
            except (TypeError, ValueError):
                return _error_response(op, ValidationError.code, "n and seed must be integers.")
            if not 1 <= n <= 50:
                return _error_response(op, ValidationError.code, "Ask for 1–50 questions.")
            row = practice.create_assignment(title, topic, difficulty, n, seed)
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"created": row}}
        if op == "assignment_list":
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"assignments": [asdict(a) for a in practice.list_assignments()]}}
        if op == "practice_next":
            topic = str(request.get("topic", ""))
            if topic not in ("linear", "quadratic"):
                return _error_response(op, ValidationError.code, "practice_next needs topic linear or quadratic.")
            try:
                seed = int(request.get("seed", 0))
            except (TypeError, ValueError):
                return _error_response(op, ValidationError.code, "seed must be an integer.")
            attempts = practice.recent_attempts(1000)
            tallies: dict[tuple[str, str], list] = {}
            totals: dict[str, dict[str, int]] = {}
            for a in attempts:
                key = (a.topic, a.difficulty or "basic")
                cell = tallies.setdefault(key, [0, 0])
                cell[0] += int(a.correct)
                cell[1] += 1
                totals.setdefault(a.topic, {}).setdefault(a.difficulty or "basic", 0)
                totals[a.topic][a.difficulty or "basic"] += 1
            rates = solve_rates({k: (v[0], v[1]) for k, v in tallies.items()})
            p, n = practice.get_bkt(topic)
            difficulty = choose_difficulty(topic, bkt_gated_levels(p, n), rates, totals)
            question = generate_questions(topic, difficulty, 1, seed, parser, solver)[0]
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"topic": topic, "difficulty": difficulty,
                               "prompt": question.prompt, "expected": list(question.expected),
                               "prompt_latex": latex_of(question.prompt),
                               "expected_latex": [latex_of(e) for e in question.expected]}}
        if op == "practice_override":
            try:
                attempt_id = int(request.get("attempt_id", 0))
            except (TypeError, ValueError):
                return _error_response(op, ValidationError.code, "attempt_id must be an integer.")
            changed = practice.record_override(attempt_id, bool(request.get("correct", False)))
            if not changed:
                return _error_response(op, ValidationError.code, f"No attempt with id {attempt_id}.")
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"overridden": attempt_id}}
        if op == "worksheet_generate":
            topic = str(request.get("topic", ""))
            difficulty = str(request.get("difficulty", ""))
            spec = str(request.get("spec", "")).strip()
            if spec:
                try:
                    topic, difficulty, _label = resolve_spec(spec)
                except KeyError:
                    return _error_response(op, ValidationError.code, f"Unknown spec code {spec!r}.")
            if topic not in TOPICS or difficulty not in DIFFICULTIES:
                return _error_response(op, ValidationError.code, "Send known topic/difficulty or a spec code.")
            try:
                n = int(request.get("n", 10))
                seed = int(request.get("seed", 0))
            except (TypeError, ValueError):
                return _error_response(op, ValidationError.code, "n and seed must be integers.")
            if not 1 <= n <= 50:
                return _error_response(op, ValidationError.code, "Ask for 1–50 questions.")
            sheet = build_worksheet(
                topic, difficulty, n, seed, bool(request.get("with_answers", True)),
                str(request.get("title", "")), parser, solver)
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"title": sheet.title, "topic": sheet.topic,
                               "difficulty": sheet.difficulty, "seed": sheet.seed,
                               "prompts": list(sheet.prompts),
                               "answer_key": [list(a) for a in sheet.answer_key]}}
        if op == "spec_map":
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"spec_points": [
                        {"code": code, **entry} for code, entry in SPEC_POINTS.items()]}}
        if op == "concept_note":
            rule = str(request.get("rule", ""))
            try:
                note = concept_for(rule)
            except KeyError:
                return _error_response(op, ValidationError.code, f"No concept note for rule {rule!r}.")
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"rule": rule, "note": note}}
        if op == "practice_examples":
            topic = str(request.get("topic", "all"))
            solved = []
            for t, prompt, op_name in examples_for(topic):
                if op_name == "solve_linear":
                    sol = solve_linear(prompt, parser, solver, Domain.REALS)
                elif op_name == "solve_quadratic":
                    sol = solve_quadratic(prompt, parser, solver, Domain.REALS)
                elif op_name == "solve_inequality":
                    sol = solve_inequality(prompt, parser, solver, Domain.REALS)
                else:
                    sol = transform_expression(prompt, op_name, parser, solver)
                if sol.verification != "verified":
                    return _error_response(op, "INTERNAL_ERROR", f"Example failed verification: {prompt!r}.")
                solved.append({"topic": t, "prompt": prompt,
                               "exact": list(sol.exact),
                               "prompt_latex": latex_of(prompt),
                               "exact_latex": [latex_of(e) for e in sol.exact]})
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"examples": solved}}
        if op == "glossary_list":
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"terms": sorted(GLOSSARY)}}
        if op == "glossary_get":
            term = str(request.get("term", "")).strip().lower()
            if term not in GLOSSARY:
                return _error_response(op, ValidationError.code, f"No glossary entry for {term!r}.")
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"term": term, "definition": GLOSSARY[term]}}
        if op == "ocr_parse":
            image = request.get("image_base64", "")
            if not isinstance(image, str) or not image.strip():
                return _error_response(op, ValidationError.code, "Send image_base64.")
            try:
                raw_bytes = decode_image(image)
                text = ocr_provider().extract_text(raw_bytes)
            except AIProviderError as exc:
                return _error_response(op, ValidationError.code, str(exc))
            try:
                expr = parser.parse(text)
            except MathEngineError as exc:
                return _error_response(op, exc.code, f"Read {text!r}, but {exc}")
            return {"ok": True, "op": op, "interpretation": expr.canonical,
                    "result": {"text": text, "kind": expr.kind,
                               "interpretation": expr.canonical}}
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
            enriched = [
                {**asdict(q), "prompt_latex": latex_of(q.prompt),
                 "expected_latex": [latex_of(e) for e in q.expected]}
                for q in questions
            ]
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"questions": enriched}}
        if op == "practice_score":
            raw_attempts = request.get("attempts", [])
            if not isinstance(raw_attempts, list):
                return _error_response(op, ValidationError.code, "Send attempts as a list.")
            try:
                attempts = tuple(
                    Attempt(topic=str(a["topic"]), correct=bool(a["correct"]),
                            hints_used=int(a.get("hints_used", 0)),
                            difficulty=str(a.get("difficulty", "")))
                    for a in raw_attempts
                )
            except (KeyError, TypeError, ValueError, AttributeError):
                return _error_response(op, ValidationError.code, "Each attempt needs topic, correct, hints_used.")
            mastery = topic_mastery(attempts)
            return {"ok": True, "op": op, "interpretation": "",
                    "result": {"mastery": mastery, "recommendation": recommend(mastery),
                               "unlocked": {t: unlocked_difficulties(t, attempts)
                                            for t in sorted({a.topic for a in attempts})}}}
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
        if op == "ai_reflect":
            payload = request.get("expected_step", {})
            student_after = request.get("student_after", "")
            reflection = request.get("reflection", "")
            if not isinstance(payload, dict) or not isinstance(student_after, str):
                return _error_response(op, ValidationError.code, "Send expected_step object and student_after string.")
            if not isinstance(reflection, str) or len(reflection.strip()) < 10:
                return _error_response(
                    op, ValidationError.code,
                    "Explain what went wrong in one full sentence before seeing the correction.")
            try:
                expected = Step(**payload)
            except (TypeError, AttributeError):
                return _error_response(op, ValidationError.code, "expected_step is malformed.")
            mistake = classify_mistake(expected, student_after, solver.check_identity)
            if mistake is None:
                return {"ok": True, "op": op, "interpretation": expected.after,
                        "result": {"accepted": True, "correct": True}}
            return {"ok": True, "op": op, "interpretation": expected.after,
                    "result": {"accepted": True, "correct": False,
                               "category": mistake.category,
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
