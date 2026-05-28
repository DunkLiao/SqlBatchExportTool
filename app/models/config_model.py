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
        db = _load_db_config(data)
        return cls(
            db=db,
            last_sql_folder=str(data.get("last_sql_folder", data.get("sql_folder_path", ""))),
            last_output_excel=str(data.get("last_output_excel", data.get("output_excel_path", ""))),
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


def _load_db_config(data: dict[str, Any]) -> DbConfig:
    db_data = data.get("db") if isinstance(data.get("db"), dict) else {}
    if db_data:
        return DbConfig(
            host=str(db_data.get("host", "127.0.0.1")),
            port=_to_int(db_data.get("port", 1521), 1521),
            service_name=str(db_data.get("service_name", "ORCL")),
            username=str(db_data.get("username", "system")),
            password=str(db_data.get("password", "")),
        )

    legacy_data = data.get("database") if isinstance(data.get("database"), dict) else {}
    if legacy_data:
        host, port, service_name = _parse_legacy_dsn(str(legacy_data.get("dsn", "")))
        return DbConfig(
            host=host,
            port=port,
            service_name=service_name,
            username=str(legacy_data.get("username", "system")),
            password=str(legacy_data.get("password", "")),
        )

    return DbConfig()


def _parse_legacy_dsn(dsn: str) -> tuple[str, int, str]:
    host = "127.0.0.1"
    port = 1521
    service_name = "ORCL"

    dsn = dsn.strip()
    if not dsn:
        return host, port, service_name

    host_port, separator, service = dsn.partition("/")
    if separator and service:
        service_name = service

    parsed_host, separator, parsed_port = host_port.partition(":")
    if parsed_host:
        host = parsed_host
    if separator:
        port = _to_int(parsed_port, 1521)

    return host, port, service_name
