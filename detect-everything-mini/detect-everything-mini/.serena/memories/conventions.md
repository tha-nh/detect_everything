# Conventions
- Keep code straightforward and stdlib-heavy; GUI is a single `DetectEverythingApp` Tkinter class.
- Use type hints for function signatures and class attributes where practical.
- Vietnamese UI/user-facing strings are used throughout; keep source UTF-8 and avoid reintroducing mojibake.
- GUI detection runs in a daemon background `threading.Thread`; UI updates are marshalled through `root.after` helpers.
- Do not change detection behavior when making GUI presentation edits unless requested.