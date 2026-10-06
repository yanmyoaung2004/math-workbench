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
