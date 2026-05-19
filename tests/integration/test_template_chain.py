"""US-020 integration: extract → apply_golden_template → verify_sums → diff chain."""

from __future__ import annotations

from pathlib import Path

import pytest

from humax_excel_mcp.tools.diff import generate_diff_candidates
from humax_excel_mcp.tools.extract import extract_filtered
from humax_excel_mcp.tools.report import generate_report
from humax_excel_mcp.tools.restore import restore_backup
from humax_excel_mcp.tools.template_engine import apply_golden_template
from humax_excel_mcp.tools.verify import verify_sums

pytestmark = pytest.mark.asyncio

ROOT = Path(__file__).resolve().parents[2]
FIX_DIR = ROOT / "fixtures" / "templates"


async def test_extract_then_apply_template_then_restore(
    sample_26bp_path: Path, tmp_path: Path
) -> None:
    # 1) extract a slice for sanity
    extract_res = await extract_filtered(
        str(sample_26bp_path), "예산+실적", company="HMX", max_rows=50
    )
    assert extract_res.success

    # 2) apply golden template via report orchestrator
    report_out = tmp_path / "humax_account_chain.xlsx"
    report_res = await generate_report(
        source_file=str(sample_26bp_path),
        report_type="humax_account",
        output_path=str(report_out),
        month=3,
        verify_after=False,
    )
    assert report_res.success
    assert report_out.exists()

    # 3) restore (round-trip): copy report_out to side-file
    restored = tmp_path / "restored.xlsx"
    restore_res = await restore_backup(
        backup_path=str(report_out),
        output_path=str(restored),
    )
    assert restore_res.success
    assert restore_res.backup_sha256 == restore_res.restored_sha256


async def test_all_three_template_types_via_chain(
    sample_26bp_path: Path, tmp_path: Path
) -> None:
    for ttype in ("humax_allocation", "humax_account", "evcs_account"):
        out = tmp_path / f"{ttype}_out.xlsx"
        res = await apply_golden_template(
            source_file=str(sample_26bp_path),
            template_path=str(FIX_DIR / f"{ttype}.xlsx"),
            template_type=ttype,
            output_path=str(out),
            month=3,
        )
        assert res.success, f"{ttype} chain failed"
        assert out.exists()


async def test_extract_apply_verify_diff_chain(
    sample_26bp_path: Path, prev_month_path: Path, tmp_path: Path
) -> None:
    """US-020 AC5: extract → apply_golden_template → verify_sums → generate_diff_candidates chain."""
    # 1) extract
    extract_res = await extract_filtered(
        str(sample_26bp_path), "예산+실적", company="HMX", max_rows=30
    )
    assert extract_res.success

    # 2) apply_golden_template
    template_out = tmp_path / "applied.xlsx"
    apply_res = await apply_golden_template(
        source_file=str(sample_26bp_path),
        template_path=str(FIX_DIR / "humax_account.xlsx"),
        template_type="humax_account",
        output_path=str(template_out),
        month=3,
    )
    assert apply_res.success

    # 3) verify_sums on source (the output xlsx is the report template, not a 26BP)
    verify_res = await verify_sums(str(sample_26bp_path), "예산+실적")
    assert verify_res.success

    # 4) generate_diff_candidates between prev and curr
    diff_res = await generate_diff_candidates(
        str(prev_month_path),
        str(sample_26bp_path),
        prev_sheet="예산+실적",
        curr_sheet="예산+실적",
        threshold_million=0.001,
    )
    assert diff_res.success


async def test_template_chain_raw_to_aggregated_then_template(tmp_path: Path) -> None:
    """US-024: Build a row-3-header file in-memory, run generate_report with source_format='auto',
    confirm output non-empty."""
    from openpyxl import Workbook

    p = tmp_path / "raw_like.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "예산+실적"
    ws.append(["title"])
    ws.append(["subtitle"])
    ws.append([
        "구분", "Year", "Month", "Company\nCode", "본사/법인", "Company",
        "Posting Date", "Doc no.", "Cost Center", "Cost Ctr Name", "대조직",
        "배부조직", "보고용", "보고용(re)", "G/L Account", "소계정", "대계정",
        "대계정(re)", "구분", "분류", "통화\n(Doc)", "Amount\n(Doc)",
        "통화\n(KRW)", "Amount\n(KRW)", "Text", "Reversed\nwith", "Vendor\nName",
        "URL", "비고", "배부기준",
        "STB\n(배부율)", "Mobility\n(배부율)", "EVCS(국내)\n(배부율)",
        "EVCS(해외)\n(배부율)", "공통\n(배부율)", "건물\n(배부율)",
        "H.Mobility\n(배부율)", "H.EV\n(배부율)", "하이파킹\n(배부율)",
        "피플카\n(배부율)", "위너콤\n(배부율)", "홀딩스\n(배부율)",
        "H.Networks\n(배부율)", "TOTAL\n(배부율)",
    ])
    # 2 data rows
    base = [
        "실적", "26년", "1월", 1000, "본사", "HKR", None, None, 101, "CC101",
        "사업그룹", None, None, None, 510000, "GL510000", "대계정A", None,
        "실적", "분류A", "KRW", 1000, "KRW", 1000.0,
        None, None, None, None, None, None,
        25.0, 25.0, 30.0, 20.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100.0,
    ]
    ws.append(base)
    ws.append(base)
    wb.save(p)

    out = tmp_path / "report_out.xlsx"
    result = await generate_report(
        source_file=str(p),
        report_type="humax_account",
        output_path=str(out),
        month=1,
        source_format="auto",
        verify_after=False,
    )
    assert result.output_path is not None
    assert out.exists()


async def test_template_chain_explicit_aggregated_on_synthetic(
    sample_26bp_path: Path, tmp_path: Path
) -> None:
    """US-024: Synthetic fixture (row 1 headers) with source_format='auto' works."""
    out = tmp_path / "synth_out.xlsx"
    result = await generate_report(
        source_file=str(sample_26bp_path),
        report_type="humax_account",
        output_path=str(out),
        month=3,
        source_format="auto",
        verify_after=False,
    )
    assert result.output_path is not None


def test_explicit_aggregated_on_raw_data_raises_schema_mismatch(tmp_path):
    """US-024 AC9: source_format='aggregated' on raw-header file → SchemaMismatch."""
    import asyncio

    from openpyxl import Workbook

    from humax_excel_mcp.core import errors

    p = tmp_path / "raw_like.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "예산+실적"
    ws.append(["title"])  # row 1 — not headers
    ws.append(["subtitle"])  # row 2
    ws.append([
        "구분", "Year", "Month", "Company\nCode", "본사/법인", "Company",
        "Posting Date", "Doc no.", "Cost Center", "Cost Ctr Name", "대조직",
        "G/L Account", "Amount\n(KRW)",
    ])  # row 3 — actual headers
    ws.append(["실적", "26년", "1월", 1000, "본사", "HKR", None, None, 101, "CC101",
                "사업그룹", 510000, 1000.0])
    wb.save(p)

    out = tmp_path / "out.xlsx"
    with pytest.raises(errors.SchemaMismatch):
        asyncio.run(generate_report(
            source_file=str(p),
            report_type="humax_account",
            output_path=str(out),
            month=1,
            source_format="aggregated",  # explicit, should fail because row 1 is title not headers
            verify_after=False,
        ))
