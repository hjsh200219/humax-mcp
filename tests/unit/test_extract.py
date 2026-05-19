"""US-006 extract_filtered tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from humax_excel_mcp.core import errors
from humax_excel_mcp.tools.extract import extract_filtered

pytestmark = pytest.mark.asyncio


async def test_basic_extract(sample_26bp_path: Path) -> None:
    res = await extract_filtered(str(sample_26bp_path), "예산+실적")
    assert res.success
    assert res.metadata.total_rows > 0
    assert res.data_classification == "INTERNAL"


async def test_company_filter(sample_26bp_path: Path) -> None:
    res = await extract_filtered(str(sample_26bp_path), "예산+실적", company="HMX")
    for row in res.data:
        assert row.get("company") == "HMX"


async def test_invalid_company(sample_26bp_path: Path) -> None:
    with pytest.raises(errors.InvalidCompany):
        await extract_filtered(str(sample_26bp_path), "예산+실적", company="ZZZ")


async def test_columns_filter(sample_26bp_path: Path) -> None:
    res = await extract_filtered(
        str(sample_26bp_path),
        "예산+실적",
        columns=["division", "company", "gl_account_name"],
    )
    assert res.data
    for row in res.data:
        assert set(row.keys()) <= {"division", "company", "gl_account_name", "variance"}


async def test_invalid_column(sample_26bp_path: Path) -> None:
    with pytest.raises(errors.InvalidColumn):
        await extract_filtered(str(sample_26bp_path), "예산+실적", columns=["zzz_unknown"])


async def test_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(errors.FileNotFound):
        await extract_filtered(str(tmp_path / "missing.xlsx"), "예산+실적")


async def test_sheet_not_found(sample_26bp_path: Path) -> None:
    with pytest.raises(errors.SheetNotFound):
        await extract_filtered(str(sample_26bp_path), "없는시트")


async def test_max_rows_truncation(sample_26bp_path: Path) -> None:
    res = await extract_filtered(str(sample_26bp_path), "예산+실적", max_rows=5)
    assert res.metadata.returned_rows <= 5
    assert res.metadata.truncated is True


async def test_metadata_fields(sample_26bp_path: Path) -> None:
    res = await extract_filtered(str(sample_26bp_path), "예산+실적", company="HMX")
    m = res.metadata
    assert m.sort_order == "variance_abs_desc"
    assert m.filters_applied.get("company") == "HMX"
    assert m.estimated_tokens > 0


async def test_live_artifact_hints(sample_26bp_path: Path) -> None:
    res = await extract_filtered(
        str(sample_26bp_path), "예산+실적", render_format="live_artifact"
    )
    assert res.artifact_hints is not None
    assert res.artifact_hints.type == "table_with_chart"
    assert res.artifact_hints.preferred_chart == "bar"


async def test_excel_render_no_hints(sample_26bp_path: Path) -> None:
    res = await extract_filtered(str(sample_26bp_path), "예산+실적", render_format="excel")
    assert res.artifact_hints is None


async def test_month_filter_with_company(sample_26bp_path: Path) -> None:
    res = await extract_filtered(
        str(sample_26bp_path), "예산+실적", month="2026-03", company="HMX", max_rows=20
    )
    for row in res.data:
        assert "budget_amount" in row or "m03_budget" in row or row == {}


async def test_org_level_filter(sample_26bp_path: Path) -> None:
    res = await extract_filtered(str(sample_26bp_path), "예산+실적", org_level="소조직")
    for row in res.data:
        assert row.get("division") == "소조직"


async def test_account_group_filter(sample_26bp_path: Path) -> None:
    res = await extract_filtered(
        str(sample_26bp_path), "예산+실적", account_group="인건비"
    )
    for row in res.data:
        name = str(row.get("gl_account_name", ""))
        assert any(k in name for k in ("급여", "상여", "복리후생"))


async def test_output_format_csv(sample_26bp_path: Path) -> None:
    res = await extract_filtered(
        str(sample_26bp_path), "예산+실적", max_rows=3, output_format="csv"
    )
    assert res.success
