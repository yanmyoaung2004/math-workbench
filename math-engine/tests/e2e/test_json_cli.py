"""E2E: stdio JSON-lines round-trips through the real sidecar entrypoint."""

import json
import subprocess
import sys

import pytest

CMD = [sys.executable, "-m", "workbench_math.entrypoints.json_cli"]


@pytest.fixture(autouse=True)
def _isolated_data_dir(tmp_path, monkeypatch):
    """Never touch the real ~/.math-workbench from tests."""
    monkeypatch.setenv("WORKBENCH_DATA_DIR", str(tmp_path / "data"))


def run_requests(payloads):
    proc = subprocess.run(
        CMD, input="\n".join(json.dumps(p) for p in payloads) + "\n",
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    return [json.loads(line) for line in proc.stdout.strip().splitlines()]


def test_solve_parse_and_error_round_trip():
    responses = run_requests([
        {"op": "solve_linear", "input": "2x + 5 = 17"},
        {"op": "parse", "input": "2x + 5 = 17"},
        {"op": "solve_linear", "input": "2x + = 17"},
        {"op": "bogus", "input": "x"},
    ])
    ok, parsed, bad, unknown = responses
    assert ok["ok"] is True and ok["result"]["exact"] == ["6"]
    assert ok["result"]["verification"] == "verified"
    assert len(ok["result"]["steps"]) == 2
    assert parsed["ok"] is True and parsed["interpretation"] == "2*x + 5 = 17"
    assert bad["ok"] is False and bad["error"]["code"] == "PARSE_ERROR"
    assert unknown["ok"] is False and unknown["error"]["code"] == "VALIDATION_ERROR"


def test_system_round_trip():
    responses = run_requests([
        {"op": "solve_system", "equations": ["2x + y = 7", "x - y = 2"]},
        {"op": "solve_system", "equations": ["x + y = 1"]},
    ])
    ok, bad = responses
    assert ok["ok"] is True
    assert [(b["variable"], b["exact"]) for b in ok["result"]["bindings"]] == [("x", "3"), ("y", "1")]
    assert bad["ok"] is False and bad["error"]["code"] == "VALIDATION_ERROR"


def test_graph_ops_round_trip():
    responses = run_requests([
        {"op": "sample_graph", "input": "y = 1/x", "x_min": -5, "x_max": 5, "n": 200},
        {"op": "analyze_graph", "input": "y = x^2 - 4x + 3"},
        {"op": "table_values", "input": "y = x^2 - 2", "start": "-1", "end": "1", "step": "1"},
        {"op": "solve_intersection", "inputs": ["y = 2x + 4", "y = 10"]},
    ])
    sampled, analyzed, tabled, met = responses
    assert sampled["ok"] is True and len(sampled["result"]["segments"]) == 2
    assert sampled["result"]["excluded"] == [0.0]
    assert analyzed["ok"] is True
    assert [p["x"] for p in analyzed["result"]["roots"]] == [1.0, 3.0]
    assert tabled["ok"] is True and tabled["result"]["ys"] == ["-1", "-2", "-1"]
    assert met["ok"] is True and met["result"]["points"][0]["x"] == 3.0


def test_practice_ops_round_trip():
    responses = run_requests([
        {"op": "practice_generate", "topic": "linear", "difficulty": "basic",
         "n": 3, "seed": 11},
        {"op": "practice_score", "attempts": [
            {"topic": "linear", "correct": True, "hints_used": 0},
            {"topic": "linear", "correct": False, "hints_used": 3}]},
    ])
    generated, scored = responses
    assert generated["ok"] is True and len(generated["result"]["questions"]) == 3
    assert all(q["expected"] for q in generated["result"]["questions"])
    assert scored["ok"] is True
    assert scored["result"]["mastery"] == {"linear": 50.0}


def test_practice_store_ops_round_trip():
    recorded, dashboard, due, streak, created, listed = run_requests([
        {"op": "practice_record", "topic": "linear", "difficulty": "basic",
         "correct": True, "hints_used": 0},
        {"op": "practice_dashboard"},
        {"op": "review_answer", "prompt": "2x + 5 = 17", "topic": "linear",
         "correct": True, "hints_used": 0, "today": "2026-10-07"},
        {"op": "progress_streak"},
        {"op": "assignment_create", "title": "Friday set", "topic": "linear",
         "difficulty": "basic", "n": 5, "seed": 11},
        {"op": "assignment_list"},
    ])
    assert recorded["result"]["recorded"] == 1
    assert dashboard["result"]["mastery"] == {"linear": 100.0}
    assert dashboard["result"]["attempts"] == 1
    assert due["result"]["next_due"] == "2026-10-08"
    assert streak["result"]["streak_days"] >= 0
    assert created["result"]["created"] == 1
    assert listed["result"]["assignments"][0]["title"] == "Friday set"
    pending = run_requests([{"op": "review_due", "today": "2026-10-08"}])[0]
    assert len(pending["result"]["due"]) == 1


def test_content_ops_round_trip():
    sheet, spec, note, examples, terms, term = run_requests([
        {"op": "worksheet_generate", "topic": "linear", "difficulty": "basic",
         "n": 3, "seed": 4, "with_answers": True, "title": "T"},
        {"op": "spec_map"},
        {"op": "concept_note", "rule": "discriminant"},
        {"op": "practice_examples", "topic": "quadratic"},
        {"op": "glossary_list"},
        {"op": "glossary_get", "term": "surd"},
    ])
    assert len(sheet["result"]["prompts"]) == 3
    assert len(sheet["result"]["answer_key"]) == 3
    assert any(p["code"] == "ALG-QUAD-3" for p in spec["result"]["spec_points"])
    assert "roots" in note["result"]["note"]
    assert all(e["exact"] for e in examples["result"]["examples"])
    assert "discriminant" in terms["result"]["terms"]
    assert "unevaluated" in term["result"]["definition"]


def test_ai_ops_round_trip():
    solved = run_requests([{"op": "solve_linear", "input": "2x + 5 = 17"}])[0]
    solution = solved["result"]
    hinted, explained, judged = run_requests([
        {"op": "ai_hint", "solution": solution, "level": 1},
        {"op": "ai_explain", "solution": solution, "question": "Why subtract 5?"},
        {"op": "ai_mistake",
         "expected_step": solution["steps"][0], "student_after": "2*x + 3 = 14"},
    ])
    assert hinted["ok"] is True and "x = 6" not in hinted["result"]["hint"]
    assert explained["ok"] is True and explained["result"]["provider"] == "stub"
    assert judged["ok"] is True
    assert judged["result"]["correct"] is False
    assert judged["result"]["category"] == "sign"
    assert judged["result"]["correction"] == "2*x = 12"
    judged2 = run_requests([
        {"op": "ai_mistake", "expected_step": {
            "operation": "distribute", "operand": "2*(x + 3)",
            "before": "2*(x + 3) = 14", "after": "2*x + 6 = 14",
            "rule": "distributive_property", "explanation": "Expand.",
            "verification": "verified"},
         "student_after": "2*x + 3 = 14"}])[0]
    assert judged2["result"]["category"] == "bracket_distribution"


def test_reflect_gate_and_mixed_sets():
    reflected = run_requests([
        {"op": "ai_reflect", "expected_step": {
            "operation": "distribute", "operand": "2*(x + 3)",
            "before": "2*(x + 3) = 14", "after": "2*x + 6 = 14",
            "rule": "distributive_property", "explanation": "Expand.",
            "verification": "verified"},
         "student_after": "2*x + 3 = 14", "reflection": "short"},
    ])[0]
    assert reflected["ok"] is False  # reflection too short — gate holds
    ok = run_requests([
        {"op": "ai_reflect", "expected_step": {
            "operation": "distribute", "operand": "2*(x + 3)",
            "before": "2*(x + 3) = 14", "after": "2*x + 6 = 14",
            "rule": "distributive_property", "explanation": "Expand.",
            "verification": "verified"},
         "student_after": "2*x + 3 = 14",
         "reflection": "I only multiplied the first term inside the bracket."},
    ])[0]
    assert ok["result"]["accepted"] is True
    assert ok["result"]["category"] == "bracket_distribution"
    mixed = run_requests([
        {"op": "practice_generate", "topic": "mixed", "difficulty": "basic",
         "n": 6, "seed": 3},
    ])[0]
    topics = {q["topic"] for q in mixed["result"]["questions"]}
    assert topics == {"linear", "quadratic"}


def test_history_auto_save_and_list(tmp_path):
    import os

    env = dict(os.environ, WORKBENCH_DATA_DIR=str(tmp_path))
    solve = {"op": "solve_linear", "input": "2x + 5 = 17"}
    proc = subprocess.run(CMD, input=json.dumps(solve) + "\n",
                          capture_output=True, text=True, timeout=120, env=env)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout.strip())["ok"] is True
    listed = subprocess.run(
        CMD, input=json.dumps({"op": "history_list"}) + "\n",
        capture_output=True, text=True, timeout=120, env=env)
    entries = json.loads(listed.stdout.strip())["result"]["entries"]
    assert len(entries) == 1
    assert entries[0]["input"] == "2x + 5 = 17"
    assert entries[0]["exact"] == ["6"]
    cleared = subprocess.run(
        CMD, input=json.dumps({"op": "history_clear"}) + "\n",
        capture_output=True, text=True, timeout=120, env=env)
    assert json.loads(cleared.stdout.strip())["result"]["cleared"] == 1


def test_malformed_json_line_does_not_kill_stream():
    proc = subprocess.run(
        CMD, input='{"op": "solve_linear", "input": "x = 6"}\nnot json\n',
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0
    lines = [json.loads(line) for line in proc.stdout.strip().splitlines()]
    assert lines[0]["result"]["exact"] == ["6"]
    assert lines[1]["ok"] is False


@pytest.mark.skip(reason="sidecar binary packaging lands in Phase 7; protocol already frozen")
def test_pyinstaller_binary_parity():
    pass
