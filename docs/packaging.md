# Packaging — sidecar binary + desktop bundles

## Python sidecar (reproducible, committed as recipe; binary is gitignored)

From `math-engine/` with the venv active:

```powershell
uv pip install pyinstaller
pyinstaller --onefile --console --name workbench-engine sidecar_entry.py
$triple = rustc --print host-tuple  # x86_64-pc-windows-msvc
Copy-Item dist-sidecar/workbench-engine.exe `
  ../src-tauri/binaries/workbench-engine-$triple.exe -Force
```

Verified 2026-10-06: 30 MB onefile, protocol smoke test passes
(`solve_linear` → exact `6`; `sample_graph` → segments). Build on the OS you
ship (PyInstaller is not a cross-compiler). The sidecar stays `--console` so
stdio pipes work; Tauri spawns it hidden.

## Desktop app

Prerequisites (all verified present): Rust 1.98 + `x86_64-pc-windows-msvc`
target, VS 2022 BuildTools (linker via dev environment), WebView2 runtime,
Node 24 + npm registry.

```powershell
cd frontend
npm install
npm run build          # tsc strict + vite dist (Tauri frontendDist)
cd ../src-tauri
cargo tauri build      # needs @tauri-apps/cli; NSIS/WiX for installers
```

`tauri.conf.json` declares `externalBin: ["binaries/workbench-engine"]` — the
CLI bundles `src-tauri/binaries/workbench-engine-<triple>.exe` automatically.
Capabilities (`capabilities/default.json`) scope `shell:allow-spawn`,
`shell:allow-stdin-write`, and `shell:allow-kill` to that sidecar only.

## Offline guarantees

The installed app needs no network: math (sidecar), UI (local dist), history
(SQLite) all ship inside. Network is used only for cloud AI providers, which
require user-supplied keys and degrade to the offline stub.
