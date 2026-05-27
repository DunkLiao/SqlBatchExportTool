from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

import oracledb
import pandas as pd

from app.models.config_model import DbConfig


@dataclass(slots=True)
class QueryResult:
    dataframe: pd.DataFrame
    row_count: int
    elapsed_seconds: float


class OracleDbService:
    def __init__(self, config: DbConfig) -> None:
        self._config = config
        self._connection: Any | None = None

    def connect(self) -> None:
        dsn = oracledb.makedsn(
            self._config.host,
            self._config.port,
            service_name=self._config.service_name,
        )
        self._connection = oracledb.connect(
            user=self._config.username,
            password=self._config.password,
            dsn=dsn,
        )

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def execute_query(self, sql: str, parameters: dict[str, str] | None = None) -> QueryResult:
        if self._connection is None:
            raise RuntimeError("Database is not connected.")

        cleaned_sql = _clean_sql(sql)
        started_at = time.perf_counter()
        with self._connection.cursor() as cursor:
            cursor.execute(cleaned_sql, parameters or {})
            columns = [item[0] for item in cursor.description or []]
            rows = cursor.fetchall()

        elapsed = time.perf_counter() - started_at
        dataframe = pd.DataFrame.from_records(rows, columns=columns)
        return QueryResult(
            dataframe=dataframe,
            row_count=len(dataframe.index),
            elapsed_seconds=elapsed,
        )


def _clean_sql(sql: str) -> str:
    stripped = sql.strip()
    if stripped.endswith(";"):
        return stripped[:-1].rstrip()
    return stripped
