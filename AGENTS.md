# Repository Guidelines

## Project Structure & Module Organization
- `token_tracker.py`: main Tkinter desktop app, token parser, chart rendering, and SQLite persistence.
- `requirements.txt`: Python dependencies (`pywebview`, `pyinstaller`).
- `run.bat`: local launcher for development.
- `build_exe.bat` and `token-tracker.spec`: Windows packaging entry points.
- `build/`, `dist/`, `__pycache__/`: generated artifacts; treat as build output, not source.
- Runtime user data is stored under `%APPDATA%\\token-tracker\\` (for example `config.json`, `tracker.db`).

## Build, Test, and Development Commands
- Install deps: `python -m pip install -r requirements.txt`
- Run locally: `python token_tracker.py` (or `run.bat`)
- Build executable: `build_exe.bat`
- Direct PyInstaller example:
  `python -m PyInstaller --noconfirm --clean --windowed --onefile --name token-tracker --add-data "web;web" token_tracker.py`

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation and type hints (current codebase uses typed signatures).
- Use `snake_case` for functions/variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.
- Keep parser/storage/UI concerns separated by class (`TokenParser`, `LocalSQLiteStore`, `TokenTrackerApp`).
- Prefer small, focused methods over adding more logic to `main()`.

## Testing Guidelines
- No automated test suite is committed yet.
- For new logic, add `pytest` tests under `tests/` using `test_*.py` naming.
- Prioritize parser and aggregation behavior (incremental token math, date bucketing, dedupe of events/files).
- Before opening a PR, run manual smoke checks: load sample `.jsonl`, refresh stats, and export CSV.

## Commit & Pull Request Guidelines
- This checkout does not include `.git` history, so existing commit conventions cannot be inferred here.
- Use clear, imperative commit subjects (for example: `fix parser fallback for token_count payload`).
- Keep commits scoped to one change and include rationale in the body when behavior changes.
- PRs should include: summary, test evidence (manual/automated), linked issue (if any), and UI screenshots for visual changes.

## Security & Configuration Tips
- Do not hardcode personal paths; rely on user-selected directories and `%APPDATA%`.
- Do not commit local databases, exported CSVs, or generated executables.

