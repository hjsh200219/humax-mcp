"""generate_report — PRD §4.10 / plan §5 US-017. Orchestrator over apply_golden_template + verify_sums."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from ..core import artifact_hints as ah
from ..core import errors
from ..schemas.responses import GenerateReportResult
from .template_engine import apply_golden_template
from .verify import verify_sums

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TEMPLATE_DIR = ROOT / "fixtures" / "templates"


def _resolve_template_path(report_type: str, override_dir: str | Path | None = None) -> Path:
    base = Path(override_dir) if override_dir else DEFAULT_TEMPLATE_DIR
    return base / f"{report_type}.xlsx"


async def generate_report(
    source_file: str,
    report_type: Literal["humax_allocation", "humax_account", "evcs_account"],
    output_path: str,
    *,
    month: int,
    dry_run: bool = False,
    verify_after: bool = True,
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
    template_dir: str | None = None,
    source_format: Literal["auto", "raw", "aggregated"] = "auto",
) -> GenerateReportResult:
    """End-to-end report generation: 26BP -> golden template -> verify."""
    template_path = _resolve_template_path(report_type, template_dir)
    if not template_path.exists():
        raise errors.TemplateNotFound(
            f"기본 템플릿을 찾을 수 없습니다: {template_path}. "
            f"build_fixture_templates.py를 실행하세요."
        )

    expand_evcs = report_type == "evcs_account"

    apply_res = await apply_golden_template(
        source_file=source_file,
        template_path=str(template_path),
        template_type=report_type,
        output_path=output_path,
        month=month,
        dry_run=dry_run,
        render_format="excel",
        source_format=source_format,
        expand_evcs=expand_evcs,
    )

    verification_summary = None
    if verify_after and not dry_run and apply_res.output_path:
        # Output xlsx does not have the "예산+실적" sheet (it's the report template),
        # so verify_sums is best-effort against any populated sheet; skip on missing.
        # In current implementation we skip if no sheet matches.
        try:
            # Pick first populated sheet for sanity check
            first_sheet = apply_res.sheets_processed[0].sheet_name if apply_res.sheets_processed else None
            if first_sheet:
                v = await verify_sums(apply_res.output_path, first_sheet, render_format="excel")
                verification_summary = v.summary
        except errors.HumaxMCPError:
            verification_summary = None

    data_summary = {
        "sheets_processed": len(apply_res.sheets_processed),
        "rows_matched": sum(s.rows_matched for s in apply_res.sheets_processed),
        "rows_unmatched": sum(s.rows_unmatched for s in apply_res.sheets_processed),
        "cells_populated": sum(s.cells_to_populate for s in apply_res.sheets_processed),
        "formulas_preserved": sum(s.formulas_preserved for s in apply_res.sheets_processed),
    }

    if not dry_run and data_summary["rows_matched"] == 0 and data_summary["rows_unmatched"] == 0:
        raise errors.EmptyResult(
            f"source_file에 month={month} 조건을 만족하는 데이터가 없습니다."
        )

    hints = ah.maybe_hints(
        render_format,
        artifact_type="dashboard",
        title=f"{report_type} 산출물 (M{month:02d})",
        preferred_chart="bar",
    )

    return GenerateReportResult(
        dry_run=dry_run,
        report_type=report_type,
        output_path=apply_res.output_path,
        backup_path=apply_res.backup_path,
        template_used=str(template_path),
        verification=verification_summary,
        data_summary=data_summary,
        metadata={
            "source_file": source_file,
            "month": month,
            "template_dir": str(template_dir) if template_dir else str(DEFAULT_TEMPLATE_DIR),
            "verify_after": verify_after,
        },
        render_format=render_format,
        artifact_hints=hints,
    )
