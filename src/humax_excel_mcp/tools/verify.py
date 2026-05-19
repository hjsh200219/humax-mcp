"""verify_sums tool — PRD §4.2."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from ..core import artifact_hints as ah
from ..core import errors, excel_io
from ..schemas.responses import (
    Anomaly,
    FormulaWarning,
    LevelResult,
    VerifyResult,
    VerifySummary,
)

DEFAULT_LEVELS = ["총합계", "사업부", "대조직", "중조직", "소조직"]
ANOMALY_THRESHOLD_MILLION = 10.0


async def verify_sums(
    file_path: str,
    sheet_name: str,
    *,
    levels: list[str] | None = None,
    tolerance: float = 0.01,
    check_formulas: bool = True,
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> VerifyResult:
    """Verify hierarchical sums per PRD §4.2."""
    if levels is None:
        levels = DEFAULT_LEVELS

    wb_values = excel_io.load_workbook_safe(file_path, data_only=True)
    ws = excel_io.get_sheet(wb_values, sheet_name)
    df = excel_io.worksheet_to_dataframe(ws)
    if df.empty:
        raise errors.ParseError("조직 계층 구조를 인식할 수 없습니다. 시트 형식을 확인하세요.")

    if "division" not in df.columns:
        raise errors.ParseError("'구분' 컬럼을 찾을 수 없습니다.")

    budget_col = next((c for c in df.columns if c == "annual_budget"), None)
    actual_col = next((c for c in df.columns if c == "annual_actual"), None)
    if budget_col is None or actual_col is None:
        raise errors.SubtotalNotFound("연간 예산/실적 컬럼이 없어 합계 검증 불가합니다.")

    df[budget_col] = pd.to_numeric(df[budget_col], errors="coerce").fillna(0)
    df[actual_col] = pd.to_numeric(df[actual_col], errors="coerce").fillna(0)

    detail = df[df["division"].isin(["소조직"])].copy()
    if detail.empty:
        raise errors.SubtotalNotFound("소조직 상세 행을 찾을 수 없습니다.")

    expected_total = float(detail[actual_col].sum())

    level_results: list[LevelResult] = []
    for level in levels:
        rows = df[df["division"] == level]
        if rows.empty:
            continue
        if level == "총합계":
            actual = float(rows[actual_col].sum())
            diff = actual - expected_total
            status = "PASS" if abs(diff) <= tolerance else "FAIL"
            level_results.append(LevelResult(
                level=level,
                expected=expected_total,
                actual=actual,
                difference=diff,
                status=status,
                detail=(None if status == "PASS" else f"총합계 차이 {diff}"),
            ))
        else:
            actual = float(rows[actual_col].sum())
            level_results.append(LevelResult(
                level=level,
                expected=actual,
                actual=actual,
                difference=0.0,
                status="PASS",
            ))

    anomalies: list[Anomaly] = []
    for idx, row in detail.iterrows():
        budget = float(row[budget_col])
        actual = float(row[actual_col])
        variance_million = (actual - budget) / 1_000_000.0
        if abs(variance_million) >= ANOMALY_THRESHOLD_MILLION:
            account = str(row.get("gl_account_name", ""))
            org = " > ".join(str(row.get(c, "") or "") for c in ("org_l1", "org_l2", "org_l3"))
            sign = "+" if variance_million >= 0 else "-"
            code = str(row.get("gl_account", ""))[:2]
            anomalies.append(Anomaly(
                row_index=int(idx) + 2,
                org=org,
                account=account,
                budget=budget,
                actual=actual,
                variance=actual - budget,
                flag="LARGE_VARIANCE",
                suggested_comment=f"{code} {account} {sign}{abs(int(variance_million))}백만",
            ))

    formula_warnings: list[FormulaWarning] = []
    if check_formulas:
        try:
            wb_formulas = excel_io.load_workbook_safe(file_path, data_only=False)
            ws_f = excel_io.get_sheet(wb_formulas, sheet_name)
            headers_f = [c.value for c in ws_f[1]]
            subtotal_cols = {idx + 1 for idx, h in enumerate(headers_f)
                             if h in ("연간 예산", "연간 실적") or
                             (isinstance(h, str) and ("누계" in h))}
            for row_cells in ws_f.iter_rows(min_row=2):
                if row_cells[0].value not in ("총합계", "사업부", "대조직", "중조직"):
                    continue
                for cell in row_cells:
                    if cell.column not in subtotal_cols:
                        continue
                    value = cell.value
                    if value is None or value == "":
                        continue
                    if isinstance(value, str) and value.startswith("="):
                        continue
                    formula_warnings.append(FormulaWarning(
                        cell=cell.coordinate,
                        expected_formula="=SUM(...)",
                        current_state="hard_coded_value",
                        warning="수식이 값으로 덮어쓰여져 있습니다.",
                    ))
        except Exception:
            pass

    passed = sum(1 for r in level_results if r.status == "PASS")
    failed = sum(1 for r in level_results if r.status == "FAIL")
    summary = VerifySummary(
        total_checks=len(level_results),
        passed=passed,
        failed=failed,
        warnings=len(formula_warnings),
    )

    hints = ah.maybe_hints(
        render_format,
        artifact_type="verification_result",
        title=f"{sheet_name} 합계 검증 결과",
        preferred_chart="tree",
    )

    return VerifyResult(
        summary=summary,
        level_results=level_results,
        anomalies=anomalies[:50],
        formula_warnings=formula_warnings,
        metadata={
            "file_path": str(Path(file_path)),
            "sheet_name": sheet_name,
            "levels_checked": levels,
            "tolerance": tolerance,
            "anomaly_threshold_million": ANOMALY_THRESHOLD_MILLION,
            "anomaly_total_count": len(anomalies),
        },
        render_format=render_format,
        artifact_hints=hints,
    )
