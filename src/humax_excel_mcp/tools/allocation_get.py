"""get_allocation_rates tool — PRD §4.6."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from ..core import artifact_hints as ah
from ..core import errors, excel_io
from ..schemas import bp26
from ..schemas.responses import AllocationRateRow, AllocationRatesResult

RATE_KEYS = list(bp26.ALLOCATION_RATE_COLUMNS.values())
RATE_SUM_TOLERANCE = 0.01


async def get_allocation_rates(
    file_path: str,
    month: int,
    *,
    company: str | None = None,
    cost_center: str | None = None,
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> AllocationRatesResult:
    """Read C30 배부기준 + C31-C34 배부율 from 26BP raw."""
    if not 1 <= month <= 12:
        raise errors.InvalidMonth(f"month는 1-12 범위여야 합니다. 입력: {month}")
    if company is not None and company not in bp26.VALID_COMPANIES:
        raise errors.InvalidCompany(f"잘못된 회사 코드: {company}")

    wb = excel_io.load_workbook_safe(file_path, data_only=True)
    if "예산+실적" not in wb.sheetnames:
        raise errors.SheetNotFound("예산+실적 시트를 찾을 수 없습니다.")
    ws = wb["예산+실적"]
    df = excel_io.worksheet_to_dataframe(ws)

    missing = [k for k in RATE_KEYS if k not in df.columns]
    if missing or "allocation_basis" not in df.columns:
        raise errors.SchemaMismatch(
            f"C30-C34 배부율 컬럼이 누락되었습니다. 스키마 v{bp26.SCHEMA_VERSION} 확인 필요. 누락: {missing}"
        )

    if df.empty:
        return AllocationRatesResult(
            data=[],
            metadata={
                "file_path": str(Path(file_path)),
                "month": month,
                "filter_company": company,
                "filter_cc": cost_center,
                "rate_sum_violations": 0,
                "unique_rates_count": 0,
                "schema_version": bp26.SCHEMA_VERSION,
            },
            render_format=render_format,
        )

    detail = df[df.get("division") == "소조직"].copy()
    if company is not None and "company" in detail.columns:
        detail = detail[detail["company"] == company]
    if cost_center is not None and "cost_center" in detail.columns:
        detail = detail[detail["cost_center"].astype(str) == str(cost_center)]

    for k in RATE_KEYS:
        detail[k] = pd.to_numeric(detail[k], errors="coerce").fillna(0.0)

    rate_sum_violations = 0
    rows: list[AllocationRateRow] = []
    if not detail.empty:
        group_keys = ["cost_center", "allocation_basis", *RATE_KEYS]
        present_keys = [k for k in group_keys if k in detail.columns]
        grouped = detail.groupby(present_keys, dropna=False, sort=False)
        for key, sub in grouped:
            if not isinstance(key, tuple):
                key = (key,)
            keymap = dict(zip(present_keys, key))
            rates = {k: float(keymap.get(k, 0.0)) for k in RATE_KEYS}
            rsum = sum(rates.values())
            ok = abs(rsum - 100.0) <= RATE_SUM_TOLERANCE
            if not ok:
                rate_sum_violations += 1
            cc = str(keymap.get("cost_center", ""))
            basis = str(keymap.get("allocation_basis", ""))
            first = sub.iloc[0]
            rows.append(AllocationRateRow(
                cost_center=cc,
                cost_center_name=str(first.get("gl_account_name", "") or ""),
                allocation_basis=basis,
                rates=rates,
                rate_sum=rsum,
                rate_sum_ok=ok,
                row_count=len(sub),
            ))

    hints = ah.maybe_hints(
        render_format,
        artifact_type="table_with_chart",
        title=f"26.{month:02d} 배부율 조회",
        preferred_chart="stacked_bar",
        columns_for_chart=["cost_center", *RATE_KEYS],
    )

    return AllocationRatesResult(
        data=rows,
        metadata={
            "file_path": str(Path(file_path)),
            "month": month,
            "filter_company": company,
            "filter_cc": cost_center,
            "rate_sum_violations": rate_sum_violations,
            "unique_rates_count": len(rows),
            "schema_version": bp26.SCHEMA_VERSION,
        },
        render_format=render_format,
        artifact_hints=hints,
    )
