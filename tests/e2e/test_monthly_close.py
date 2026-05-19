"""US-014 E2E: full monthly-close chain."""

from __future__ import annotations

from pathlib import Path

import pytest

from humax_excel_mcp.schemas.requests import AllocationUpdate, CellUpdate
from humax_excel_mcp.tools.allocation_get import get_allocation_rates
from humax_excel_mcp.tools.allocation_set import update_allocation_rates
from humax_excel_mcp.tools.diff import generate_diff_candidates
from humax_excel_mcp.tools.extract import extract_filtered
from humax_excel_mcp.tools.verify import verify_sums
from humax_excel_mcp.tools.write import write_cells

pytestmark = pytest.mark.asyncio


async def test_full_monthly_close_chain(
    sample_26bp_path: Path,
    prev_month_path: Path,
    tmp_path: Path,
) -> None:
    # 1) Extract HMX 3월 data
    extract_res = await extract_filtered(
        str(sample_26bp_path),
        "예산+실적",
        month="2026-03",
        company="HMX",
        max_rows=50,
    )
    assert extract_res.success

    # 2) Verify
    verify_res = await verify_sums(str(sample_26bp_path), "예산+실적")
    assert verify_res.success
    total_check = next((r for r in verify_res.level_results if r.level == "총합계"), None)
    assert total_check is not None and total_check.status == "PASS"

    # 3) Write_cells (edit A2)
    write_out = tmp_path / "edited.xlsx"
    write_res = await write_cells(
        str(sample_26bp_path),
        "예산+실적",
        [CellUpdate(cell="A2", value="EDITED")],
        output_path=str(write_out),
    )
    assert write_res.success
    assert write_res.backup_path

    # 4) Diff against prev
    diff_res = await generate_diff_candidates(
        str(prev_month_path),
        str(sample_26bp_path),
        prev_sheet="예산+실적",
        curr_sheet="예산+실적",
        threshold_million=0.001,
    )
    assert diff_res.success

    # 5) get_allocation_rates(before)
    alloc_before = await get_allocation_rates(str(sample_26bp_path), month=3)
    assert alloc_before.metadata["rate_sum_violations"] == 0

    # 6) update_allocation_rates dry-run
    first = alloc_before.data[0]
    upd = AllocationUpdate(
        cost_center=first.cost_center,
        allocation_basis=first.allocation_basis,
        new_rates={"STB": 40.0, "Mobility": 10.0, "EVCS_domestic": 25.0, "EVCS_overseas": 25.0},
    )
    dry = await update_allocation_rates(
        str(sample_26bp_path),
        month=3,
        updates=[upd],
        output_path=str(tmp_path / "alloc_dry.xlsx"),
        dry_run=True,
    )
    assert dry.dry_run is True

    # 7) update_allocation_rates apply
    alloc_out = tmp_path / "alloc_applied.xlsx"
    apply_res = await update_allocation_rates(
        str(sample_26bp_path),
        month=3,
        updates=[upd],
        output_path=str(alloc_out),
    )
    assert apply_res.success
    assert apply_res.data.updates_applied >= 1

    # 8) get_allocation_rates(after) — confirm changes
    alloc_after = await get_allocation_rates(str(alloc_out), month=3)
    found = [r for r in alloc_after.data if r.cost_center == first.cost_center
             and r.allocation_basis == first.allocation_basis]
    assert any(abs(r.rates["STB"] - 40.0) < 0.01 for r in found)

    # 9) verify_sums on edited file
    verify_after = await verify_sums(str(alloc_out), "예산+실적")
    assert verify_after.success


async def test_steps_5_6_7_report_generation(
    sample_26bp_path: Path,
    tmp_path: Path,
) -> None:
    """E2E Steps 5/6/7 — generate all 3 reports via golden templates."""
    import time

    from humax_excel_mcp.tools.report import generate_report

    t0 = time.time()
    outputs = {}
    for ttype in ("humax_allocation", "humax_account", "evcs_account"):
        out = tmp_path / f"{ttype}_step.xlsx"
        res = await generate_report(
            source_file=str(sample_26bp_path),
            report_type=ttype,
            output_path=str(out),
            month=3,
            verify_after=False,
        )
        assert res.success
        assert out.exists()
        outputs[ttype] = out
    elapsed = time.time() - t0
    assert elapsed < 60, f"E2E took {elapsed:.1f}s (>60s)"
    assert len(outputs) == 3
