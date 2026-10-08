# AI Architecture — provider seam, grounding rule, offline default

Binding rule (product.md §21): the deterministic engine is authoritative; AI
explains verified mathematics and never solves, overrides, or edits steps.

## Layers (`math-engine/.../ai/`, stdlib only, arch-test enforced)

| Module | Role |
|--------|------|
| `provider.py` | `ProviderPort.complete()` + `StubProvider` (deterministic, offline) |
| `openai_compat.py` | OpenAI-compatible REST via stdlib urllib (OpenAI/OpenRouter/local); key from `WORKBENCH_AI_KEY` |
| `mathpix.py` | Mathpix OCR provider (paid API, key at runtime); wire format loopback-proven, live key owed |
| `tutor.py` | `TutorService.explain()` builds grounded prompt (verified result + steps + attempt + mistake + hints-shown + level); provider failure → `provider="fallback"` deterministic summary |
| `hints.py` | L1 conceptual → L2 operational → L3 explicit → L4 next step → L5 full solution, from verified steps; L1–L3 never leak the answer (tested) |
| `mistakes.py` | `classify(expected_step, student_after, identical)` → bracket/sign/arithmetic/unparseable + minimal correction; `None` when correct |

## Provider selection

`WORKBENCH_AI_PROVIDER`: `stub` (default, offline) | `openai` | `openai_compat` |
`openrouter` | `local` (all REST via `WORKBENCH_AI_BASE_URL`, default OpenAI).
Cloud keys live in user env at runtime — never in the repo. Core math never
waits on AI: solve renders immediately, explanations generate after.

## Protocol ops

`ai_explain` (`solution` + `question` + `attempt?` + `mistake?` + `hints_shown?` +
`level?`, default `gcse`),
`ai_hint` (`solution` + `level` 1–5 + `step_index?`), `ai_mistake`
(`expected_step` + `student_after` → `correct` flag or classified correction).
`solution`/`expected_step` are objects copied from a solve response.

## Image input (OCR seam)

`ocr_parse` accepts `image_base64` (2 MB cap, data-URL tolerant) and returns
recognized text parsed to `{text, kind, interpretation}`. Only the stub backend
ships in V1, so it refuses honestly (`No OCR engine is configured…`) instead
of hallucinating text. Real engines register in `ai/ocr.py:ocr_provider()`
(on-device or cloud behind the same key pattern); the protocol is frozen.

## Tests

Unit (stub determinism, ladder secrecy, classification incl. the
`2(x+3)→2x+3` product example, stub/fallback providers), integration
(OpenAI wire format vs local loopback HTTP server — no internet), e2e
(hint/explain/mistake round-trips).
