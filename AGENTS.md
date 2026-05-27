# Repository Guidelines

## Project Structure & Module Organization

This repository contains a Python desktop application for batch-running Oracle SQL files and exporting results to Excel.

- `main.py`: root entry point used by PyInstaller.
- `app/main.py`: application startup.
- `app/ui/`: PySide6 GUI code, including the main window and worker threads.
- `app/services/`: business logic for Oracle access, SQL loading, Excel export, and logging.
- `app/models/`: typed configuration models.
- `app/utils/`: shared path and file helpers.
- `config/config.json`: default and last-used local settings.
- `sql/`: sample SQL files.
- `output/`: generated Excel files.
- `logs/`: runtime logs.

No test suite exists yet. Add tests under `tests/` when introducing test coverage.

## Build, Test, and Development Commands

Create and install the local environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the app:

```powershell
.\run_app.bat
```

Build the Windows executable:

```powershell
.\build_exe.bat
```

Run a syntax check:

```powershell
.\.venv\Scripts\python.exe -m compileall app main.py
```

## Coding Style & Naming Conventions

Use Python 3.12+ style with full type hints for new code. Use 4-space indentation and keep GUI code separate from service logic. Prefer small service classes and dataclasses for structured data. Use `snake_case` for functions, variables, and modules; use `PascalCase` for classes.

Avoid putting Oracle, Excel, or file-system logic directly in UI event handlers. Keep long-running work in `QThread` workers.

## Testing Guidelines

When adding tests, use `pytest` under `tests/`. Name files `test_*.py` and test functions `test_*`. Prioritize coverage for sheet-name cleanup, SQL file sorting/encoding, config load/save, and Excel export behavior. Mock Oracle connections instead of requiring a live database in automated tests.

## Commit & Pull Request Guidelines

This directory currently has no Git history, so no repository-specific commit convention can be inferred. Use concise imperative commit messages, for example:

```text
Add Oracle connection test button
Fix Excel sheet name collision handling
```

Pull requests should include a short summary, verification steps, affected UI behavior, and screenshots for visible GUI changes. Link related issues when available.

## Security & Configuration Tips

`config/config.json` may contain database credentials. Do not commit real production credentials. Prefer sample or blank passwords in shared changes. Generated logs, build artifacts, virtual environments, and exported Excel files are ignored by `.gitignore`.
