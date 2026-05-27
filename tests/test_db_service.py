from __future__ import annotations

from app.models.config_model import DbConfig
from app.services.db_service import OracleDbService


class FakeCursor:
    def __init__(self) -> None:
        self.description = [("ID",), ("NAME",)]
        self.executed_sql = ""
        self.executed_parameters: dict[str, str] | None = None

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        return None

    def execute(self, sql: str, parameters: dict[str, str]) -> None:
        self.executed_sql = sql
        self.executed_parameters = parameters

    def fetchall(self) -> list[tuple[int, str]]:
        return [(1, "Alice")]


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self._cursor = cursor

    def cursor(self) -> FakeCursor:
        return self._cursor


def test_execute_query_passes_parameters_and_cleans_trailing_semicolon() -> None:
    cursor = FakeCursor()
    service = OracleDbService(DbConfig())
    service._connection = FakeConnection(cursor)

    result = service.execute_query(
        "SELECT * FROM CUSTOMER WHERE DATA_DATE = :DATA_DATE;",
        {"DATA_DATE": "20260527"},
    )

    assert cursor.executed_sql == "SELECT * FROM CUSTOMER WHERE DATA_DATE = :DATA_DATE"
    assert cursor.executed_parameters == {"DATA_DATE": "20260527"}
    assert result.row_count == 1
    assert list(result.dataframe.columns) == ["ID", "NAME"]
