"""PyInstaller entry point for the Tauri sidecar binary.

Absolute import (not `python -m`) so PyInstaller's module graph resolves the
package cleanly. Build (from math-engine/, venv active):

    pyinstaller --onefile --console --name workbench-engine sidecar_entry.py

Then copy dist/workbench-engine.exe to
src-tauri/binaries/workbench-engine-x86_64-pc-windows-msvc.exe
(triple from `rustc --print host-tuple`). See docs/packaging.md.
"""

from workbench_math.entrypoints.json_cli import main

if __name__ == "__main__":
    main()
