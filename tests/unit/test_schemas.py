"""US-002 schema acceptance tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from humax_excel_mcp.schemas import bp26
from humax_excel_mcp.schemas.requests import (
    AllocationUpdate,
    AllocGetRequest,
    AllocSetRequest,
    CellUpdate,
    DiffRequest,
    ExchangeRequest,
    ExtractRequest,
    VerifyRequest,
    WriteRequest,
)
from humax_excel_mcp.schemas.responses import (
    ArtifactHints,
    ExtractMetadata,
    ExtractResult,
    VerifySummary,
    WriteSummary,
    WriteVerification,
)


def test_schema_version() -> None:
    assert bp26.SCHEMA_VERSION == "2026.05"
    assert "2026.05" in bp26.CHANGELOG


def test_column_map_contains_structure_and_monthly() -> None:
    assert bp26.COLUMN_MAP["구분"] == "division"
    assert bp26.COLUMN_MAP["Company"] == "company"
    assert bp26.COLUMN_MAP["G/L Account"] == "gl_account"
    assert bp26.COLUMN_MAP["1월 예산"] == "m01_budget"
    assert bp26.COLUMN_MAP["12월 실적"] == "m12_actual"
    assert bp26.COLUMN_MAP["3월 누계 예산"] == "cum03_budget"
    assert bp26.COLUMN_MAP["연간 실적"] == "annual_actual"
    assert bp26.COLUMN_MAP["배부기준"] == "allocation_basis"


def test_default_columns_listed() -> None:
    assert "division" in bp26.DEFAULT_COLUMNS
    assert "company" in bp26.DEFAULT_COLUMNS
    assert "annual_budget" in bp26.DEFAULT_COLUMNS


def test_validate_headers_match() -> None:
    headers = list(bp26.COLUMN_MAP.keys()) + list(bp26.ALLOCATION_RATE_COLUMNS.keys())
    assert bp26.validate_headers(headers) == []


def test_validate_headers_diff() -> None:
    diffs = bp26.validate_headers(["구분", "UNKNOWN_COL"])
    assert any(d.startswith("MISSING:") for d in diffs)
    assert "UNKNOWN:UNKNOWN_COL" in diffs


def test_cell_update_valid() -> None:
    cu = CellUpdate(cell="D5", value=125000)
    assert cu.cell == "D5"
    assert cu.skip_if_formula is True


def test_cell_update_invalid_cell_address() -> None:
    with pytest.raises(ValidationError):
        CellUpdate(cell="5D", value=1)
    with pytest.raises(ValidationError):
        CellUpdate(cell="A0", value=1)


def test_extract_request_defaults() -> None:
    req = ExtractRequest(file_path="x.xlsx", sheet_name="예산+실적")
    assert req.max_rows == 500
    assert req.sort_by == "variance_abs_desc"
    assert req.render_format == "excel"


def test_extract_request_invalid_company() -> None:
    with pytest.raises(ValidationError):
        ExtractRequest(file_path="x.xlsx", sheet_name="S", company="ZZZ")


def test_extract_request_invalid_month() -> None:
    with pytest.raises(ValidationError):
        ExtractRequest(file_path="x.xlsx", sheet_name="S", month="2026/03")


def test_verify_request_defaults() -> None:
    req = VerifyRequest(file_path="x.xlsx", sheet_name="S")
    assert req.tolerance == 0.01
    assert req.check_formulas is True


def test_write_request_requires_updates() -> None:
    with pytest.raises(ValidationError):
        WriteRequest(file_path="x.xlsx", sheet_name="S", updates=[])


def test_write_request_max_updates() -> None:
    updates = [CellUpdate(cell=f"A{i}", value=i) for i in range(1, 6)]
    req = WriteRequest(file_path="x.xlsx", sheet_name="S", updates=updates)
    assert len(req.updates) == 5
    assert req.dry_run is False


def test_diff_request_defaults() -> None:
    req = DiffRequest(prev_file="a.xlsx", curr_file="b.xlsx")
    assert req.prev_sheet == "누계"
    assert req.threshold_million == 10.0
    assert req.max_candidates == 100


def test_alloc_get_request_month_range() -> None:
    AllocGetRequest(file_path="x.xlsx", month=1)
    AllocGetRequest(file_path="x.xlsx", month=12)
    with pytest.raises(ValidationError):
        AllocGetRequest(file_path="x.xlsx", month=0)
    with pytest.raises(ValidationError):
        AllocGetRequest(file_path="x.xlsx", month=13)


def test_alloc_set_request_requires_output_path() -> None:
    upd = AllocationUpdate(
        cost_center="102401",
        allocation_basis="경영지원부문",
        new_rates={"STB": 40.0, "Mobility": 0.0, "EVCS_domestic": 30.0, "EVCS_overseas": 30.0},
    )
    req = AllocSetRequest(
        file_path="x.xlsx",
        month=3,
        updates=[upd],
        output_path="x_edited.xlsx",
    )
    assert req.rate_tolerance == 0.01


def test_exchange_request_date_format() -> None:
    ExchangeRequest(search_date="20260519")
    ExchangeRequest(search_date=None)
    with pytest.raises(ValidationError):
        ExchangeRequest(search_date="2026-05-19")
    with pytest.raises(ValidationError):
        ExchangeRequest(search_date="20260519X")


def test_artifact_hints_construct() -> None:
    h = ArtifactHints(
        type="table_with_chart",
        title="3월 본사 인건비",
        preferred_chart="bar",
        columns_for_chart=["gl_account_name", "budget", "actual"],
    )
    assert h.type == "table_with_chart"
    assert h.pii_redacted is False


def test_extract_result_construct() -> None:
    meta = ExtractMetadata(
        total_rows=10,
        filtered_rows=5,
        returned_rows=5,
        truncated=False,
        filters_applied={"month": "2026-03"},
        sort_order="variance_abs_desc",
        estimated_tokens=100,
        file_path="x.xlsx",
        sheet_name="예산+실적",
    )
    r = ExtractResult(data=[], metadata=meta)
    assert r.data_classification == "INTERNAL"
    assert r.status == "ok"


def test_summary_models() -> None:
    s = VerifySummary(total_checks=10, passed=9, failed=1, warnings=0)
    assert s.total_checks == 10
    ws = WriteSummary(total_updates=5, applied=5, skipped_formula=0, skipped_invalid=0, warnings=0)
    assert ws.applied == 5
    wv = WriteVerification(verified=True)
    assert wv.mismatches == []
