"""extract_filtered tool — PRD §4.1 + accuracy-speed PRD US-S5/S-6."""

from __future__ import annotations

import re
from math import ceil
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from ..core import artifact_hints as ah
from ..core import errors, token_guard, workbook_cache
from ..schemas import bp26
from ..schemas.responses import ExtractMetadata, ExtractResult


async def extract_filtered(
    file_path: str,
    sheet_name: str,
    *,
    month: str | None = None,
    company: str | None = None,
    columns: list[str] | None = None,
    org_level: str | None = None,
    account_group: str | None = None,
    max_rows: int = 500,
    page: int = 1,
    page_size: int | None = None,
    sort_by: Literal["row_order", "variance_abs_desc", "amount_desc"] = "variance_abs_desc",
    output_format: Literal["json", "csv", "markdown"] = "json",
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> ExtractResult:
    """Filter rows from 26BP sheet. Returns ExtractResult."""
    if page < 1 or (page_size is not None and page_size < 1):
        raise errors.InvalidPagination(
            f"page/page_size는 1 이상이어야 합니다. page={page}, page_size={page_size}"
        )
    if company is not None and company not in bp26.VALID_COMPANIES:
        raise errors.InvalidCompany(
            f"잘못된 회사 코드: {company}. 사용 가능: {', '.join(bp26.VALID_COMPANIES)}"
        )

    df = workbook_cache.get_dataframe(file_path, sheet_name)
    total_rows = len(df)

    if columns:
        valid_cols = set(df.columns)
        for c in columns:
            if c not in valid_cols:
                raise errors.InvalidColumn(
                    f"잘못된 컬럼명: {c}. 사용 가능: {sorted(valid_cols)[:20]}..."
                )

    work = df
    filters_applied: dict[str, Any] = {}

    if month is not None:
        try:
            year_str, m_str = month.split("-")
            m = int(m_str)
        except ValueError as exc:
            raise errors.InvalidColumn(f"잘못된 month 형식: {month}") from exc
        budget_col = f"m{m:02d}_budget"
        actual_col = f"m{m:02d}_actual"
        filters_applied["month"] = month
        keep_cols = [
            c
            for c in work.columns
            if not c.startswith(("m", "cum")) or c in {budget_col, actual_col}
        ]
        keep_cols = [
            c for c in keep_cols if not (c.startswith("m") and c not in {budget_col, actual_col})
        ]
        keep_cols = [c for c in keep_cols if not c.startswith("cum")]
        work = work[keep_cols].copy()
        work = work.rename(columns={budget_col: "budget_amount", actual_col: "actual_amount"})

    if company is not None:
        work = work[work.get("company") == company]
        filters_applied["company"] = company

    if org_level is not None:
        work = work[work.get("division") == org_level]
        filters_applied["org_level"] = org_level

    if account_group is not None:
        ag_to_keywords = {
            "인건비": ["급여", "상여", "복리후생"],
            "경비": ["임차료", "지급수수료"],
            "감가상각비": ["감가상각비"],
        }
        kws = ag_to_keywords.get(account_group, [account_group])
        if "gl_account_name" in work.columns:
            pattern = "|".join(re.escape(kw) for kw in kws)
            mask = work["gl_account_name"].astype(str).str.contains(pattern, regex=True, na=False)
            work = work[mask]
        filters_applied["account_group"] = account_group

    if columns:
        present = [c for c in columns if c in work.columns]
        work = work[present]
        filters_applied["columns"] = columns
    else:
        present = [c for c in bp26.DEFAULT_COLUMNS if c in work.columns]
        if "budget_amount" in work.columns:
            present = [c for c in present if not c.startswith(("m", "cum"))]
            present.extend(["budget_amount", "actual_amount"])
        work = work[present]

    filtered_rows = len(work)

    if "budget_amount" in work.columns and "actual_amount" in work.columns:
        work = work.assign(
            variance=pd.to_numeric(work["actual_amount"], errors="coerce").fillna(0)
            - pd.to_numeric(work["budget_amount"], errors="coerce").fillna(0)
        )

    if sort_by == "variance_abs_desc" and "variance" in work.columns:
        work = work.reindex(work["variance"].abs().sort_values(ascending=False).index)
    elif sort_by == "amount_desc" and "actual_amount" in work.columns:
        work = work.sort_values(by="actual_amount", ascending=False)

    # US-S5: 사전 페이지네이션 — 사후 절단 전에 요청 페이지만 남긴다
    total_pages: int | None = None
    if page_size is not None:
        total_pages = max(1, ceil(filtered_rows / page_size))
        work = work.iloc[(page - 1) * page_size : page * page_size]

    rows = work.to_dict(orient="records")
    rows, truncated = token_guard.auto_truncate(rows, max_rows=max_rows)

    if not rows and filtered_rows == 0:
        raise errors.EmptyResult("필터 조건에 맞는 데이터가 없습니다.")

    if page_size is not None:
        filters_applied["page"] = page
        filters_applied["page_size"] = page_size

    if output_format != "json":
        if output_format == "csv":
            serialized: Any = pd.DataFrame(rows).to_csv(index=False)
        else:
            serialized = pd.DataFrame(rows).to_markdown(index=False)
        data_field: Any = serialized
    else:
        data_field = rows

    est_tokens = token_guard.estimate_tokens(data_field)
    if token_guard.estimate_size_kb(data_field) > token_guard.HARD_LIMIT_KB:
        raise errors.TokenLimitExceeded(
            f"응답 크기 초과. max_rows를 {max(1, max_rows // 2)}로 줄여주세요."
        )

    metadata = ExtractMetadata(
        total_rows=total_rows,
        filtered_rows=filtered_rows,
        returned_rows=len(rows),
        truncated=truncated,
        filters_applied=filters_applied,
        sort_order=sort_by,
        estimated_tokens=est_tokens,
        file_path=str(Path(file_path)),
        sheet_name=sheet_name,
        page=page if page_size is not None else None,
        page_size=page_size,
        total_pages=total_pages,
    )

    title_parts: list[str] = []
    if month:
        title_parts.append(month)
    if company:
        title_parts.append(company)
    if account_group:
        title_parts.append(account_group)
    title = " ".join(title_parts) or f"{sheet_name} 추출"

    hints = ah.maybe_hints(
        render_format,
        artifact_type="table_with_chart",
        title=f"26BP {title} 필터 결과",
        preferred_chart="bar",
        columns_for_chart=[
            c for c in ("gl_account_name", "budget_amount", "actual_amount") if c in work.columns
        ],
        highlight_threshold=10,
    )

    return ExtractResult(
        data=data_field if output_format == "json" else [],
        metadata=metadata,
        render_format=render_format,
        artifact_hints=hints,
    )
