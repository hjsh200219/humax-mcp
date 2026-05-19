"""US-004 excel_io tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

from humax_excel_mcp.core import errors, excel_io


def test_assert_xlsx_path_missing(tmp_path: Path) -> None:
    with pytest.raises(errors.FileNotFound):
        excel_io.assert_xlsx_path(tmp_path / "missing.xlsx")


def test_assert_xlsx_path_wrong_ext(tmp_path: Path) -> None:
    p = tmp_path / "data.csv"
    p.write_text("a,b\n1,2", encoding="utf-8")
    with pytest.raises(errors.FileNotFound):
        excel_io.assert_xlsx_path(p)


def test_load_workbook_safe_ok(sample_26bp_path: Path) -> None:
    wb = excel_io.load_workbook_safe(sample_26bp_path)
    assert "예산+실적" in wb.sheetnames


def test_get_sheet_missing(sample_26bp_path: Path) -> None:
    wb = excel_io.load_workbook_safe(sample_26bp_path)
    with pytest.raises(errors.SheetNotFound):
        excel_io.get_sheet(wb, "없는시트")


def test_worksheet_to_dataframe(sample_26bp_path: Path) -> None:
    wb = excel_io.load_workbook_safe(sample_26bp_path)
    ws = excel_io.get_sheet(wb, "예산+실적")
    df = excel_io.worksheet_to_dataframe(ws)
    assert "division" in df.columns
    assert "company" in df.columns
    assert "m01_budget" in df.columns
    assert len(df) > 5


def test_validate_schema_strict_missing_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["구분", "Company"])  # missing tons of cols
    wb.save(p)
    wb2 = excel_io.load_workbook_safe(p)
    ws2 = excel_io.get_sheet(wb2, wb2.sheetnames[0])
    headers = [c.value for c in ws2[1]]
    with pytest.raises(errors.SchemaMismatch):
        excel_io.validate_schema(headers, strict=True)


def test_validate_schema_non_strict_returns_diffs(tmp_path: Path) -> None:
    diffs = excel_io.validate_schema(["구분"], strict=False)
    assert any(d.startswith("MISSING:") for d in diffs)


def test_validate_schema_allocation_cols_required(tmp_path: Path) -> None:
    with pytest.raises(errors.SchemaMismatch):
        excel_io.validate_schema(["구분", "Company"], require_allocation_cols=True)
