"""E2E: stdio JSON-lines round-trips through the real sidecar entrypoint."""

import json
import subprocess
import sys

import pytest

CMD = [sys.executable, "-m", "workbench_math.entrypoints.json_cli"]


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
