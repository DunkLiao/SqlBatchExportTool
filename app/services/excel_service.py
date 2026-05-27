from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
import re

from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
import pandas as pd


INVALID_SHEET_CHARS = re.compile(r"[\[\]:*?/\\]")
MAX_SHEET_NAME_LENGTH = 31
MAX_COLUMN_WIDTH = 60


class ExcelExportService(AbstractContextManager["ExcelExportService"]):
    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path
        self._writer: pd.ExcelWriter | None = None
        self._used_sheet_names: set[str] = set()
        self._has_sheet = False

    def __enter__(self) -> "ExcelExportService":
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._writer = pd.ExcelWriter(self.output_path, engine="openpyxl")
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        if self._writer is None:
            return
        if not self._has_sheet:
            pd.DataFrame({"Message": ["No SQL files found"]}).to_excel(
                self._writer,
                sheet_name="Summary",
                index=False,
            )
        self._writer.close()
        self._writer = None

    def write_dataframe(self, preferred_sheet_name: str, dataframe: pd.DataFrame) -> str:
        if self._writer is None:
            raise RuntimeError("Excel writer is not open.")

        sheet_name = make_unique_sheet_name(preferred_sheet_name, self._used_sheet_names)
        if dataframe.empty:
            pd.DataFrame([["No Data"]]).to_excel(
                self._writer,
                sheet_name=sheet_name,
                index=False,
                header=False,
            )
        else:
            dataframe.to_excel(self._writer, sheet_name=sheet_name, index=False)

        self._used_sheet_names.add(sheet_name)
        self._has_sheet = True
        self._format_sheet(sheet_name, dataframe.empty)
        return sheet_name

    def _format_sheet(self, sheet_name: str, no_data: bool) -> None:
        if self._writer is None:
            raise RuntimeError("Excel writer is not open.")

        worksheet = self._writer.book[sheet_name]
        worksheet.freeze_panes = "A2"
        if not no_data:
            for cell in worksheet[1]:
                cell.font = Font(bold=True)

        for column_cells in worksheet.columns:
            column_letter = get_column_letter(column_cells[0].column)
            max_length = 0
            for cell in column_cells:
                value = "" if cell.value is None else str(cell.value)
                max_length = max(max_length, len(value))
            worksheet.column_dimensions[column_letter].width = min(max(max_length + 2, 10), MAX_COLUMN_WIDTH)


def make_unique_sheet_name(preferred_name: str, used_names: set[str]) -> str:
    cleaned = INVALID_SHEET_CHARS.sub("_", preferred_name).strip("' ").strip()
    if not cleaned:
        cleaned = "Sheet"

    base = cleaned[:MAX_SHEET_NAME_LENGTH]
    if base not in used_names:
        return base

    index = 1
    while True:
        suffix = f"_{index}"
        candidate = f"{base[:MAX_SHEET_NAME_LENGTH - len(suffix)]}{suffix}"
        if candidate not in used_names:
            return candidate
        index += 1
