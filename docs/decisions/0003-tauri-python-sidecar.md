# ADR-0003: Tauri 2 Python sidecar over stdio JSON-lines

Date: 2026-10-06 · Status: **accepted** · Sources: `../research/tauri-sidecar-facts.md`

## Context

Windows-first offline desktop needs SymPy without shipping a Python runtime
requirement to students. Options: sidecar binary, localhost HTTP server,
or porting math to Rust/JS.

## Decision

- Bundle the engine with **PyInstaller `--onefile`** as
  `src-tauri/binaries/workbench-engine-<target-triple>[.exe]`, declared in
  `bundle.externalBin`, spawned via `@tauri-apps/plugin-shell`
  `Command.sidecar` (`shell:allow-spawn`, `shell:allow-stdin-write`).
- Transport V1: **long-lived process + stdio JSON-lines** (one request/line,
  one response/line per `docs/math-engine.md`). Rationale: no TCP port to
  collide over, no localhost security surface (`tauri-plugin-localhost`
  explicitly warns of "considerable security risks"), trivially offline.
- Frontend↔Rust stays on built-in `invoke`/channels/events + asset protocol;
  only Rust↔Python crosses the sidecar boundary, bridged through a thin
  Tauri command. Localhost HTTP kept as documented fallback if profiling
  ever shows stdio as the bottleneck.

## Consequences

+ Offline by construction; no per-machine Python; no firewall prompts.
+ Contract tests run against the same `json_cli` binary path CI will ship.
− PyInstaller onefile startup cost (~100s of ms) — amortized by long-lived process + warmup call.
− Must build per-target triple on its own OS (no cross-compiling) — CI matrix job, Phase 7.
