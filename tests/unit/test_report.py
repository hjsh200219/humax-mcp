"""US-017 generate_report tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from humax_excel_mcp.core import errors
from humax_excel_mcp.tools.report import generate_report

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("report_type", ["humax_allocation", "humax_account", "evcs_account"])
async def test_happy_path_per_report_type(
    report_type: str, sample_26bp_path: Path, tmp_path: Path
) -> None:
    out = tmp_path / f"{report_type}_report.xlsx"
    res = await generate_report(
        source_file=str(sample_26bp_path),
        report_type=report_type,
        output_path=str(out),
        month=3,
        verify_after=False,
    )
    assert res.success
    assert res.report_type == report_type
    assert out.exists()
    assert res.template_used.endswith(f"{report_type}.xlsx")


async def test_dry_run_no_write(sample_26bp_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.xlsx"
    res = await generate_report(
        source_file=str(sample_26bp_path),
        report_type="humax_account",
        output_path=str(out),
        month=3,
        dry_run=True,
    )
    assert res.dry_run is True
    assert not out.exists()
    assert res.output_path is None


async def test_verify_after_runs_when_true(
    sample_26bp_path: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out.xlsx"
    res = await generate_report(
        source_file=str(sample_26bp_path),
        report_type="humax_account",
        output_path=str(out),
        month=3,
        verify_after=True,
    )
    assert res.success


async def test_month_validation(sample_26bp_path: Path, tmp_path: Path) -> None:
    with pytest.raises(errors.InvalidMonth):
        await generate_report(
            source_file=str(sample_26bp_path),
            report_type="humax_account",
            output_path=str(tmp_path / "out.xlsx"),
            month=0,
        )


async def test_source_file_missing(tmp_path: Path) -> None:
    with pytest.raises(errors.FileNotFound):
        await generate_report(
            source_file=str(tmp_path / "missing.xlsx"),
            report_type="humax_account",
            output_path=str(tmp_path / "out.xlsx"),
            month=3,
        )


async def test_template_not_found_for_bogus_template_dir(
    sample_26bp_path: Path, tmp_path: Path
) -> None:
    with pytest.raises(errors.TemplateNotFound):
        await generate_report(
            source_file=str(sample_26bp_path),
            report_type="humax_account",
            output_path=str(tmp_path / "out.xlsx"),
            month=3,
            template_dir=str(tmp_path / "no-templates"),
        )
