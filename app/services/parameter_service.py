from __future__ import annotations


class SqlParameterError(ValueError):
    pass


def parse_sql_parameters(text: str) -> dict[str, str]:
    parameters: dict[str, str] = {}

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if "=" not in line:
            raise SqlParameterError(f"Line {line_number} must use KEY=VALUE format.")

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise SqlParameterError(f"Line {line_number} has an empty parameter name.")
        if key in parameters:
            raise SqlParameterError(f"Duplicate SQL parameter: {key}")

        parameters[key] = value.strip()

    return parameters
