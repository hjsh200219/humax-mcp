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
