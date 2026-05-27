from __future__ import annotations

from pathlib import Path
import sys


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def ensure_xlsx_suffix(path: Path) -> Path:
    if path.suffix.lower() != ".xlsx":
        return path.with_suffix(".xlsx")
    return path


def resolve_app_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_absolute():
        return path
    return project_root() / path
