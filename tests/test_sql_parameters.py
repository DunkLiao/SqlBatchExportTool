from __future__ import annotations

import pytest

from app.services.parameter_service import SqlParameterError, parse_sql_parameters


def test_parse_single_parameter() -> None:
    assert parse_sql_parameters("DATA_DATE=20260527") == {"DATA_DATE": "20260527"}


def test_parse_multiple_parameters_and_blank_lines() -> None:
    text = """
    DATA_DATE = 20260527

    BRANCH_ID=001
    """

    assert parse_sql_parameters(text) == {
        "DATA_DATE": "20260527",
        "BRANCH_ID": "001",
    }


def test_parse_allows_equals_in_value() -> None:
    assert parse_sql_parameters("FILTER=A=B") == {"FILTER": "A=B"}


def test_parse_rejects_empty_parameter_name() -> None:
    with pytest.raises(SqlParameterError, match="empty parameter name"):
        parse_sql_parameters("=20260527")


def test_parse_rejects_missing_equals() -> None:
    with pytest.raises(SqlParameterError, match="KEY=VALUE"):
        parse_sql_parameters("DATA_DATE")


def test_parse_rejects_duplicate_parameter_name() -> None:
    with pytest.raises(SqlParameterError, match="Duplicate SQL parameter"):
        parse_sql_parameters("DATA_DATE=20260527\nDATA_DATE=20260528")
