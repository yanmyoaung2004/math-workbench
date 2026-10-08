"""Tutor benchmark harness: latency + grounding quality per provider.

Runs a fixed sample of golden prompts through solve + ai_explain and reports
per-op timings and provider names. Offline-safe with the stub (baseline);
point WORKBENCH_AI_* at cloud or a local llama.cpp server to compare.
Usage: python tools/bench.py [--n 5]
"""

import json
import sys
import time
import urllib.request
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(ENGINE))

CASES = [
    ("solve_linear", {"op": "solve_linear", "input": "2x + 5 = 17"}),
    ("solve_quadratic", {"op": "solve_quadratic", "input": "x^2 - 5x + 6 = 0"}),
    ("solve_inequality", {"op": "solve_inequality", "input": "2x + 3 > 9"}),
]


def main() -> None:
    from workbench_math.entrypoints.json_cli import handle

    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 5
    print(f"{'op':<18}{'solve_ms':>10}{'explain_ms':>12}  provider")
    for name, req in CASES[:n]:
        t0 = time.perf_counter()
        solved = handle(dict(req))
        t1 = time.perf_counter()
        explained = handle({"op": "ai_explain", "solution": solved["result"],
                            "question": "Explain briefly."})
        t2 = time.perf_counter()
        provider = explained["result"]["provider"]
        ok = solved["ok"] and explained["ok"]
        print(f"{name:<18}{(t1 - t0) * 1000:>10.1f}{(t2 - t1) * 1000:>12.1f}  {provider}"
              f"{'' if ok else '  FAILED'}")


if __name__ == "__main__":
    main()
