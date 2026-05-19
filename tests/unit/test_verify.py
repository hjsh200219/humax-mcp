"""US-007 verify_sums tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import load_workbook

from humax_excel_mcp.core import errors
from humax_excel_mcp.tools.verify import verify_sums

pytestmark = pytest.mark.asyncio


async def test_basic_verify(sample_26bp_path: Path) -> None:
    res = await verify_sums(str(sample_26bp_path), "예산+실적")
    assert res.success
    assert res.summary.total_checks >= 1


async def test_total_matches_detail(sample_26bp_path: Path) -> None:
    res = await verify_sums(str(sample_26bp_path), "예산+실적")
    total_check = next((r for r in res.level_results if r.level == "총합계"), None)
    assert total_check is not None
    assert total_check.status == "PASS"


async def test_tolerance_breach_detected(sample_26bp_path: Path, tmp_path: Path) -> None:
    bad = tmp_path / "bad.xlsx"
    bad.write_bytes(sample_26bp_path.read_bytes())
    wb = load_workbook(bad)
    ws = wb["예산+실적"]
    headers = [c.value for c in ws[1]]
    annual_actual_idx = headers.index("연간 실적") + 1
    total_row_idx = None
    for ridx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if row[0] == "총합계":
            total_row_idx = ridx
            break
    assert total_row_idx is not None
    ws.cell(row=total_row_idx, column=annual_actual_idx).value = 0
    wb.save(bad)
    res = await verify_sums(str(bad), "예산+실적", tolerance=0.01)
    total_check = next((r for r in res.level_results if r.level == "총합계"), None)
    assert total_check is not None
    assert total_check.status == "FAIL"
    assert res.summary.failed >= 1


async def test_anomaly_detection(sample_26bp_path: Path, tmp_path: Path) -> None:
    bad = tmp_path / "anomaly.xlsx"
    bad.write_bytes(sample_26bp_path.read_bytes())
    wb = load_workbook(bad)
    ws = wb["예산+실적"]
    headers = [c.value for c in ws[1]]
    ab_idx = headers.index("연간 예산") + 1
    aa_idx = headers.index("연간 실적") + 1
    for ridx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if row[0] == "소조직":
            ws.cell(row=ridx, column=ab_idx).value = 1_000_000_000
            ws.cell(row=ridx, column=aa_idx).value = 100_000_000
            break
    wb.save(bad)
    res = await verify_sums(str(bad), "예산+실적")
    assert res.anomalies
    a = res.anomalies[0]
    assert a.flag == "LARGE_VARIANCE"
    assert "백만" in a.suggested_comment


async def test_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(errors.FileNotFound):
        await verify_sums(str(tmp_path / "missing.xlsx"), "예산+실적")


async def test_sheet_not_found(sample_26bp_path: Path) -> None:
    with pytest.raises(errors.SheetNotFound):
        await verify_sums(str(sample_26bp_path), "없는시트")


async def test_live_artifact_hints(sample_26bp_path: Path) -> None:
    res = await verify_sums(
        str(sample_26bp_path), "예산+실적", render_format="live_artifact"
    )
    assert res.artifact_hints is not None
    assert res.artifact_hints.type == "verification_result"
    assert res.artifact_hints.preferred_chart == "tree"
