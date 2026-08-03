# Task Completion
- For code changes, at minimum run `rtk .\.venv\Scripts\python.exe -m py_compile app.py detector.py gui.py` when Python is available.
- For GUI work, instantiate the app when possible to catch Tkinter/style errors; avoid running long detection as verification.
- Check `rtk git status --short` before final response and mention unrelated dirty files if present.
- Serena memory references can be sanity-checked by the user with `serena memories check` from project root.