# Research evidence — Tauri 2 Python sidecar (gathered 2026-10-06, subagent)

Synthesis in `../decisions/0003-tauri-python-sidecar.md`. All facts from official docs.

## Sidecar mechanism

- Sidecar = external binary (any language, e.g. Python CLI/API server via pyinstaller)
  so users install no extra dependencies. Sources: https://tauri.app/develop/sidecar ·
  https://v2.tauri.app/develop/sidecar/
- Declare in `src-tauri/tauri.conf.json` → `bundle.externalBin: string[]`
  (relative to `src-tauri/`, e.g. `binaries/my-sidecar`).
- Target-triple suffix required: `binaries/my-sidecar-<triple>` (host triple via
  `rustc --print host-tuple`; Windows rename adds `.exe`).
- Rust: `tauri-plugin-shell`, `.plugin(tauri_plugin_shell::init())`, `ShellExt`,
  `app.shell().sidecar("my-sidecar")` + `.args().spawn()/.output()/.execute()`,
  `CommandEvent::Stdout/Stderr`, `child.write()` for stdin.
- JS (v2): `@tauri-apps/plugin-shell`, `Command.sidecar('binaries/my-sidecar')`
  (string must EXACTLY match an `externalBin` entry; Rust side uses bare filename).
  v1 `@tauri-apps/api/shell` must NOT be used in v2.
- Capabilities (`src-tauri/capabilities/default.json`): `shell:allow-execute`
  (`.execute()`) / `shell:allow-spawn` (`.spawn()`) + `shell:allow-stdin-write`,
  `shell:allow-kill`; scope `{name, cmd, sidecar: true, args}`.
- IPC options per docs: localhost server vs stdin/stdout vs local sockets —
  "each has their own advantages, drawbacks and security concerns"; short-lived =
  argv in/stdout out; long-lived → alternative IPC. Sources:
  https://v2.tauri.app/learn/sidecar-nodejs · https://v2.tauri.app/plugin/shell/

## Python packaging (Windows)

- Docs name `pyinstaller` for Python sidecars. `PyInstaller bundles a Python
  application and all its dependencies into a single package… without installing
  a Python interpreter`. Flags `-F/--onefile`, `-D/--onedir` (default).
  Not a cross-compiler: build Windows binaries on Windows. Sources:
  https://pyinstaller.org/en/stable/index.html · https://github.com/pyinstaller/pyinstaller
- Windows path: `src-tauri/binaries/<name>-<triple>.exe`; triples
  `x86_64-pc-windows-msvc` (default 64-bit), `i686-…`, `aarch64-…`.
  Sources: https://tauri.app/distribute/windows-installer · https://v2.tauri.app/start/prerequisites

## Offline + ports

- Sidecar spawn is a local child process — no network requirement.
- Localhost HTTP (if ever used) binds loopback only; avoid fixed ports with
  `portpicker::pick_unused_port()` (docs example fixed `9527`).
  Sources: https://v2.tauri.app/plugin/localhost · https://github.com/tauri-apps/tauri-plugin-localhost

## Alternatives

- Default UI↔Rust: `#[tauri::command]` + `invoke()` from `@tauri-apps/api/core`,
  streaming via `Channel`/`Response`, events API. Assets via custom protocol;
  `tauri-plugin-localhost` carries an explicit "considerable security risks" caution.
  Use sidecar only for non-Rust/JS binaries. Sources:
  https://v2.tauri.app/develop/calling-rust/ · https://v2.tauri.app/plugin/localhost
