# Suggested Commands
- Local rule from `C:\Users\Admin\.codex\RTK.md`: prefix shell commands with `rtk`; for PowerShell cmdlets use `rtk proxy powershell -NoProfile -Command "..."` because `rtk Get-Content` does not resolve cmdlets directly.
- Run GUI: `rtk .\.venv\Scripts\python.exe gui.py` or double-click `run_gui.bat`.
- Run CLI: `rtk .\.venv\Scripts\python.exe app.py --source "input\test.jpg" --classes "person,laptop,phone"`.
- Install deps: `rtk .\.venv\Scripts\python.exe -m pip install -r requirements.txt` after venv exists.
- Quick syntax check: `rtk .\.venv\Scripts\python.exe -m py_compile app.py detector.py gui.py`.