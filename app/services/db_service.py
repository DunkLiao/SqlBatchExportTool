from __future__ import annotations

from dataclasses import dataclass
import re
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

        cleaned_sql, bind_parameters = _prepare_sql(sql, parameters or {})
        started_at = time.perf_counter()
        with self._connection.cursor() as cursor:
            cursor.execute(cleaned_sql, bind_parameters)
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


def _prepare_sql(sql: str, parameters: dict[str, str]) -> tuple[str, dict[str, str]]:
    cleaned_sql = _clean_sql(sql)
    substituted_sql = _substitute_ampersand_parameters(cleaned_sql, parameters)
    bind_parameters = _filter_bind_parameters(substituted_sql, parameters)
    return substituted_sql, bind_parameters


def _substitute_ampersand_parameters(sql: str, parameters: dict[str, str]) -> str:
    if not parameters or "&" not in sql:
        return sql

    lookup = _build_parameter_lookup(parameters)
    result: list[str] = []
    index = 0
    in_single_quote = False
    in_line_comment = False
    in_block_comment = False

    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ""

        if in_line_comment:
            result.append(char)
            if char in "\r\n":
                in_line_comment = False
            index += 1
            continue

        if in_block_comment:
            result.append(char)
            if char == "*" and next_char == "/":
                result.append(next_char)
                in_block_comment = False
                index += 2
            else:
                index += 1
            continue

        if not in_single_quote and char == "-" and next_char == "-":
            result.append(char)
            result.append(next_char)
            in_line_comment = True
            index += 2
            continue

        if not in_single_quote and char == "/" and next_char == "*":
            result.append(char)
            result.append(next_char)
            in_block_comment = True
            index += 2
            continue

        if char == "'":
            result.append(char)
            if in_single_quote and next_char == "'":
                result.append(next_char)
                index += 2
                continue
            in_single_quote = not in_single_quote
            index += 1
            continue

        if char == "&":
            name_start = index + 1
            if next_char == "&":
                name_start = index + 2

            name_end = name_start
            while name_end < len(sql) and re.match(r"[A-Za-z0-9_#$]", sql[name_end]):
                name_end += 1

            if name_end > name_start:
                name = sql[name_start:name_end]
                value = _get_parameter_value(lookup, name)
                result.append(value.replace("'", "''") if in_single_quote else value)
                index = name_end
                continue

        result.append(char)
        index += 1

    return "".join(result)


def _build_parameter_lookup(parameters: dict[str, str]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for key, value in parameters.items():
        stripped_key = key.strip()
        normalized_key = stripped_key[1:] if stripped_key.startswith("&") else stripped_key
        lookup[stripped_key] = value
        lookup[normalized_key] = value
        lookup[stripped_key.upper()] = value
        lookup[normalized_key.upper()] = value
    return lookup


def _get_parameter_value(lookup: dict[str, str], name: str) -> str:
    for candidate in (name, f"&{name}", name.upper(), f"&{name}".upper()):
        if candidate in lookup:
            return lookup[candidate]
    raise ValueError(f"Missing SQL parameter for &{name}.")


def _filter_bind_parameters(sql: str, parameters: dict[str, str]) -> dict[str, str]:
    if not parameters:
        return {}

    bind_names = _find_bind_names(sql)
    if not bind_names:
        return {}

    parameters_by_upper = {key.upper(): (key, value) for key, value in parameters.items()}
    filtered: dict[str, str] = {}
    for bind_name in bind_names:
        matched = parameters_by_upper.get(bind_name.upper())
        if matched is not None:
            original_key, value = matched
            filtered[original_key] = value
    return filtered


def _find_bind_names(sql: str) -> set[str]:
    names: set[str] = set()
    index = 0
    in_single_quote = False
    in_line_comment = False
    in_block_comment = False

    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ""

        if in_line_comment:
            if char in "\r\n":
                in_line_comment = False
            index += 1
            continue

        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                index += 2
            else:
                index += 1
            continue

        if not in_single_quote and char == "-" and next_char == "-":
            in_line_comment = True
            index += 2
            continue

        if not in_single_quote and char == "/" and next_char == "*":
            in_block_comment = True
            index += 2
            continue

        if char == "'":
            if in_single_quote and next_char == "'":
                index += 2
                continue
            in_single_quote = not in_single_quote
            index += 1
            continue

        if not in_single_quote and char == ":" and next_char and re.match(r"[A-Za-z0-9_]", next_char):
            name_start = index + 1
            name_end = name_start
            while name_end < len(sql) and re.match(r"[A-Za-z0-9_#$]", sql[name_end]):
                name_end += 1
            names.add(sql[name_start:name_end])
            index = name_end
            continue

        index += 1

    return names
