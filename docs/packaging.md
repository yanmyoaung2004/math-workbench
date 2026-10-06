# Packaging — sidecar binary + desktop bundles

## Python sidecar (reproducible, committed as recipe; binary is gitignored)

From `math-engine/` with the venv active:

```powershell
uv pip install pyinstaller
pyinstaller --onefile --console --name workbench-engine --distpath dist-sidecar sidecar_entry.py
$triple = rustc --print host-tuple  # x86_64-pc-windows-msvc
Copy-Item dist-sidecar/workbench-engine.exe `
  ../src-tauri/binaries/workbench-engine-$triple.exe -Force
```

Verified: 30.1 MB onefile, protocol smoke test passes
(`solve_linear` → exact `6`; `sample_graph` → segments). Always smoke-test
with an isolated data dir so the real user history stays clean:

```powershell
$env:WORKBENCH_DATA_DIR = "$env:TEMP\sidecar-smoke"
'{"op": "solve_linear", "input": "2x + 5 = 17"}' | .\dist-sidecar\workbench-engine.exe
```

## Desktop app

Prerequisites (all verified present): Rust 1.98 + `x86_64-pc-windows-msvc`
target, VS 2022 BuildTools (linker via dev environment), WebView2 runtime,
Node 24 + npm registry.

```powershell
cd frontend
npm install                 # includes @tauri-apps/cli (devDep)
npm run build               # tsc strict + vite dist (Tauri frontendDist)
cd ../src-tauri
# MSVC env first (link.exe is not on PATH by default):
cmd /c '"C:\Program Files (x86)\...\VsDevCmd.bat" -arch=amd64 -host_arch=amd64 >nul && cargo build --release'
```

Verified: `math-workbench.exe` (12.7 MB) links clean; co-located
with the triple-named sidecar it launches, responds, and shows its window
(process alive + responding + titled, then closed). Capabilities load —
a malformed `capabilities/default.json` would fail this smoke test.

`tauri.conf.json` declares `externalBin: ["binaries/workbench-engine"]` — the
CLI bundles `src-tauri/binaries/workbench-engine-<triple>.exe` automatically.
Capabilities (`capabilities/default.json`) scope `shell:allow-spawn` and
`shell:allow-stdin-write` to that sidecar only (`shell:allow-kill` is
correctly unscoped).

### Not yet done (explicit gap)

- Installer bundles: neither NSIS (`makensis`) nor WiX (`candle`) is installed,
  so `tauri build` cannot produce `.nsis`/`.msi` here. Install one of them and
  rerun `npx tauri build` from `frontend/` for shippable installers.
- In-app sidecar spawn (frontend `Command.sidecar` → engine answers inside the
  window) is proven at `tauri dev`/bundle time, not by the launch smoke test.
  Run `npx tauri dev`, solve `2x + 5 = 17` in the Solver screen, and confirm
  `x = 6` with steps before release.

## Offline guarantees

The installed app needs no network: math (sidecar), UI (local dist), history
(SQLite) all ship inside. Network is used only for cloud AI providers, which
require user-supplied keys and degrade to the offline stub.
