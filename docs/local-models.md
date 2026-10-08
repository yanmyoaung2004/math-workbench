# Local Tutor Models (V2.2)

Run the AI tutor fully offline with a small model on localhost. No protocol
changes needed: our `OpenAICompatibleProvider` already speaks the llama.cpp
server dialect — only `base_url` moves to localhost.

## Setup (verified pattern, model download at your discretion)

```powershell
# 1. Get llama.cpp (prebuilt Windows binary) and a 3-4B instruct model in GGUF
#    (e.g. Qwen3-4B-Instruct or Phi-4-mini, Q4_K_M quant).
# 2. Serve it OpenAI-compatibly:
llama-server -m tutor-4b-q4km.gguf --port 8080
# 3. Point the workbench at it:
$env:WORKBENCH_AI_PROVIDER = "local"
$env:WORKBENCH_AI_BASE_URL = "http://127.0.0.1:8080"
$env:WORKBENCH_AI_MODEL = "tutor"
```

Grounding rules don't change: prompts still carry verified interpretation +
steps, and the deterministic fallback still covers failures. The stub stays
the default — local models are opt-in.

## Before defaulting to local (owed evaluation)

1. Run `python math-engine/tools/bench.py` against stub, cloud, and local;
   compare solve+explain latency and read a sample of explanations.
2. Confirm hint-quality on the golden corpus (no invented steps/answers).
3. Measure RAM/VRAM and model size on a target student laptop; document the
   minimum spec in this file.

Until then: local models are supported, not recommended-by-default.
