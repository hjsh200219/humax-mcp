"""openpyxl wrappers with schema/lock validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from ..schemas import bp26
from . import errors


def assert_xlsx_path(path: str | Path) -> Path:
    p = Path(path)
    if not p.exists():
        raise errors.FileNotFound(f"파일을 찾을 수 없습니다: {p}")
    if p.suffix.lower() != ".xlsx":
        raise errors.FileNotFound(f"xlsx 확장자가 아닙니다: {p}")
    return p


def load_workbook_safe(
    path: str | Path,
    *,
    data_only: bool = True,
    read_only: bool = False,
) -> Workbook:
    p = assert_xlsx_path(path)
    try:
        return load_workbook(p, data_only=data_only, read_only=read_only)
    except PermissionError as exc:
        raise errors.FileLocked(
            f"파일이 다른 프로그램에서 열려 있습니다. Excel을 닫고 다시 시도하세요. ({p})"
        ) from exc
    except InvalidFileException as exc:
        raise errors.FileNotFound(f"유효한 xlsx 파일이 아닙니다: {p}") from exc


def get_sheet(wb: Workbook, sheet_name: str):
    if sheet_name not in wb.sheetnames:
        raise errors.SheetNotFound(
            f"시트를 찾을 수 없습니다: {sheet_name}. 사용 가능: {wb.sheetnames}"
        )
    return wb[sheet_name]


def worksheet_to_dataframe(ws, *, normalize: bool = True) -> pd.DataFrame:
    """Read a worksheet into a DataFrame using row 1 as headers."""
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return pd.DataFrame()
    raw_headers = [str(h) if h is not None else "" for h in rows[0]]
    headers = bp26.normalize_headers(raw_headers) if normalize else raw_headers
    seen: dict[str, int] = {}
    deduped: list[str] = []
    for h in headers:
        if h in seen:
            seen[h] += 1
            deduped.append(f"{h}__{seen[h]}")
        else:
            seen[h] = 0
            deduped.append(h)
    data = rows[1:]
    return pd.DataFrame(data, columns=deduped)


def validate_schema(
    headers: list[str],
    *,
    require_allocation_cols: bool = False,
    strict: bool = False,
) -> list[str]:
    diffs = bp26.validate_headers(headers)
    missing = [d for d in diffs if d.startswith("MISSING:")]
    if strict and missing:
        raise errors.SchemaMismatch(
            f"파일 헤더가 스키마 v{bp26.SCHEMA_VERSION}과 일치하지 않습니다. "
            f"변경된 컬럼: {missing}. schemas/bp26.py를 업데이트하세요."
        )
    if require_allocation_cols:
        needed = set(bp26.ALLOCATION_RATE_COLUMNS.keys())
        present = set(headers)
        absent = needed - present
        if absent:
            raise errors.SchemaMismatch(
                f"C30-C34 배부율 컬럼이 누락되었습니다. 스키마 v{bp26.SCHEMA_VERSION} 확인 필요. "
                f"누락: {sorted(absent)}"
            )
    return diffs


def cell_to_value(value: Any) -> Any:
    """Normalize openpyxl cell value (passthrough)."""
    return value
