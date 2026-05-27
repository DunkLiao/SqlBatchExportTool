from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DbConfig:
    host: str = "127.0.0.1"
    port: int = 1521
    service_name: str = "ORCL"
    username: str = "system"
    password: str = ""


@dataclass(slots=True)
class AppConfig:
    db: DbConfig = field(default_factory=DbConfig)
    last_sql_folder: str = ""
    last_output_excel: str = ""
    last_sql_parameters: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        db_data = data.get("db") if isinstance(data.get("db"), dict) else {}
        db = DbConfig(
            host=str(db_data.get("host", "127.0.0.1")),
            port=_to_int(db_data.get("port", 1521), 1521),
            service_name=str(db_data.get("service_name", "ORCL")),
            username=str(db_data.get("username", "system")),
            password=str(db_data.get("password", "")),
        )
        return cls(
            db=db,
            last_sql_folder=str(data.get("last_sql_folder", "")),
            last_output_excel=str(data.get("last_output_excel", "")),
            last_sql_parameters=str(data.get("last_sql_parameters", "")),
        )

    @classmethod
    def load(cls, path: Path) -> "AppConfig":
        if not path.exists():
            return cls()
        try:
            return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return cls()

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
