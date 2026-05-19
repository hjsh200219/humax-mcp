"""generate_diff_candidates tool — PRD §4.4."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from ..core import artifact_hints as ah
from ..core import errors, excel_io
from ..schemas.responses import DiffCandidate, DiffResult, DiffSummary


def _load_sheet(path: str, sheet: str) -> pd.DataFrame:
    wb = excel_io.load_workbook_safe(path, data_only=True)
    if sheet not in wb.sheetnames:
        sheet = wb.sheetnames[0]
    ws = wb[sheet]
    return excel_io.worksheet_to_dataframe(ws)


def _severity(diff_pct: float) -> Literal["HIGH", "MEDIUM", "LOW"]:
    abs_p = abs(diff_pct)
    if abs_p >= 50:
        return "HIGH"
    if abs_p >= 20:
        return "MEDIUM"
    return "LOW"


async def generate_diff_candidates(
    prev_file: str,
    curr_file: str,
    *,
    prev_sheet: str = "누계",
    curr_sheet: str = "누계",
    threshold_million: float = 10.0,
    include_comment_draft: bool = True,
    max_candidates: int = 100,
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> DiffResult:
    """Compare prev/curr and surface variations above threshold."""
    excel_io.assert_xlsx_path(prev_file)
    excel_io.assert_xlsx_path(curr_file)

    prev_df = _load_sheet(prev_file, prev_sheet)
    curr_df = _load_sheet(curr_file, curr_sheet)

    structure_warnings: list[str] = []

    key_cols = ["company", "cost_center", "gl_account"]
    available_keys = [c for c in key_cols if c in prev_df.columns and c in curr_df.columns]
    if not available_keys:
        raise errors.StructureMismatch("공통 키 컬럼을 찾을 수 없습니다.")

    value_col = "annual_actual" if "annual_actual" in prev_df.columns else None
    if value_col is None or value_col not in curr_df.columns:
        raise errors.StructureMismatch("연간 실적 컬럼이 두 파일 모두에 없습니다.")

    if set(prev_df.columns) != set(curr_df.columns):
        structure_warnings.append(
            f"시트 구조가 다릅니다: 전월 {len(prev_df.columns)}열, 당월 {len(curr_df.columns)}열. 공통 부분만 비교합니다."
        )

    prev_keyed = prev_df.set_index(available_keys, drop=False)
    curr_keyed = curr_df.set_index(available_keys, drop=False)

    common_keys = prev_keyed.index.intersection(curr_keyed.index)
    total_cells_compared = len(common_keys)

    candidates: list[DiffCandidate] = []
    for key in common_keys:
        prev_row = prev_keyed.loc[key]
        curr_row = curr_keyed.loc[key]
        if isinstance(prev_row, pd.DataFrame):
            prev_row = prev_row.iloc[0]
        if isinstance(curr_row, pd.DataFrame):
            curr_row = curr_row.iloc[0]
        try:
            prev_val = float(prev_row[value_col] or 0)
            curr_val = float(curr_row[value_col] or 0)
        except (TypeError, ValueError):
            continue
        diff = curr_val - prev_val
        diff_million = diff / 1_000_000.0
        if abs(diff_million) < threshold_million:
            continue
        diff_pct = (diff / prev_val * 100.0) if prev_val else 0.0
        sev = _severity(diff_pct)
        code = str(curr_row.get("gl_account", ""))[:2]
        account = str(curr_row.get("gl_account_name", ""))
        sign = "+" if diff_million >= 0 else "-"
        comment_draft = None
        if include_comment_draft:
            comment = f"{code} {account} {sign}{abs(int(diff_million))}백만"
            if abs(diff_pct) >= 50:
                direction = "대폭 증가" if diff_million >= 0 else "대폭 감소"
                comment = f"{comment} ({direction}, {diff_pct:+.1f}%)"
            comment_draft = comment
        candidates.append(DiffCandidate(
            row_index=0,
            org=str(curr_row.get("org_l1", "")),
            sub_org=str(curr_row.get("org_l2", "")) or None,
            account_code=str(curr_row.get("gl_account", "")),
            account_name=account,
            prev_value=prev_val,
            curr_value=curr_val,
            diff=diff,
            diff_million=diff_million,
            diff_pct=diff_pct,
            comment_draft=comment_draft,
            severity=sev,
        ))

    candidates.sort(key=lambda c: abs(c.diff_million), reverse=True)
    truncated = len(candidates) > max_candidates
    returned = candidates[:max_candidates]

    summary = DiffSummary(
        total_cells_compared=total_cells_compared,
        candidates_found=len(candidates),
        candidates_returned=len(returned),
        truncated=truncated,
        largest_variance_million=max((abs(c.diff_million) for c in candidates), default=0.0),
        net_variance_million=sum(c.diff_million for c in candidates),
    )

    hints = ah.maybe_hints(
        render_format,
        artifact_type="diff_cards",
        title=f"전월 대비 Diff (threshold {threshold_million}백만)",
        preferred_chart="bar",
    )

    return DiffResult(
        summary=summary,
        candidates=returned,
        structure_warnings=structure_warnings,
        metadata={
            "prev_file": str(Path(prev_file)),
            "curr_file": str(Path(curr_file)),
            "prev_sheet": prev_sheet,
            "curr_sheet": curr_sheet,
            "threshold_million": threshold_million,
        },
        render_format=render_format,
        artifact_hints=hints,
    )
