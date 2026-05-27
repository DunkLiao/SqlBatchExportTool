from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SQL_ENCODINGS = ("utf-8-sig", "utf-8", "cp950", "big5")


@dataclass(frozen=True, slots=True)
class SqlFile:
    path: Path
    name: str
    stem: str


class SqlService:
    def list_sql_files(self, folder: Path) -> list[SqlFile]:
        if not folder.exists() or not folder.is_dir():
            raise FileNotFoundError(f"SQL folder does not exist: {folder}")

        files = sorted(
            (path for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".sql"),
            key=lambda path: path.name.lower(),
        )
        return [SqlFile(path=path, name=path.name, stem=path.stem) for path in files]

    def read_sql(self, sql_file: SqlFile) -> str:
        last_error: UnicodeDecodeError | None = None
        for encoding in SQL_ENCODINGS:
            try:
                return sql_file.path.read_text(encoding=encoding)
            except UnicodeDecodeError as exc:
                last_error = exc
        raise UnicodeDecodeError(
            last_error.encoding if last_error else "unknown",
            last_error.object if last_error else b"",
            last_error.start if last_error else 0,
            last_error.end if last_error else 0,
            f"Unable to decode SQL file using supported encodings: {', '.join(SQL_ENCODINGS)}",
        )
