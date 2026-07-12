"""US-023: Transaction-to-Aggregated Aggregator (base path, no EVCS).
US-024a: EVCS-Only Aggregator Path.

Aggregates raw 26BP transaction rows (raw_bp26 canonical keys) into
bp26-compatible pivoted DataFrame with monthly budget/actual columns,
cumulative columns, and annual totals.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from ..schemas import bp26, raw_bp26
from . import errors

# Canonical names of PII columns after normalize_headers
_PII_CANONICAL: list[str] = ["text", "vendor_name", "url", "doc_no"]

# Required canonical columns that must be present in raw_df
_REQUIRED_CANONICAL: list[str] = [
    "year",
    "month",
    "company",
    "cost_center",
    "gl_account",
    "amount_krw",
    "division_type",
]

# Rate columns to carry forward (first non-null per group)
_RATE_COLUMNS: list[str] = [
    "rate_stb",
    "rate_mobility",
    "rate_evcs_domestic",
    "rate_evcs_overseas",
    "rate_common",
    "rate_building",
    "rate_h_mobility",
    "rate_h_ev",
    "rate_hiparking",
    "rate_peoplecar",
    "rate_winnercom",
    "rate_holdings",
    "rate_h_networks",
    "rate_total",
]

# Base group key columns (without org_l1)
_GROUP_KEYS: list[str] = ["company", "cost_center", "gl_account"]

# US-A6: month 파싱 실패율 경고 임계 (silent drop 방지)
_MONTH_PARSE_WARN_RATIO = 0.01

# Enrichment columns carried forward (first non-null per group)
_ENRICHMENT_COLS: list[str] = [
    "gl_account_name",
    "org_l1",
    "cost_center_name",
]


@dataclass
class AggregateResult:
    """Return type for aggregate_to_bp26."""

    df: pd.DataFrame
    metadata: dict[str, Any] = field(default_factory=dict)


def aggregate_to_bp26(
    raw_df: pd.DataFrame,
    target_month: int,
    *,
    expand_evcs: bool = False,
) -> AggregateResult:
    """Aggregate raw 26BP transaction rows into bp26-compatible pivoted DataFrame.

    Args:
        raw_df: DataFrame with normalized canonical keys (output of
            excel_io.worksheet_to_dataframe(..., schema_module='raw_bp26')).
        target_month: Integer 1-12. Only months 1..target_month are aggregated.
        expand_evcs: When False (default), produces base aggregation (rows per
            company/cost_center/gl_account). When True, produces EVCS-only
            virtual rows scaled by rate_evcs_domestic / rate_evcs_overseas.

    Returns:
        AggregateResult with .df (DataFrame) and .metadata (dict).

    Raises:
        InvalidMonth: target_month outside 1-12.
        SchemaMismatch: required columns missing from raw_df.
        EmptyResult: zero matching rows after year filter (base path only).
    """
    t0 = time.perf_counter()

    # Step 1: Validate target_month
    if not (1 <= target_month <= 12):
        raise errors.InvalidMonth(
            f"target_month must be 1-12, got {target_month}",
            code="INVALID_MONTH",
        )

    # Step 2: Required columns check
    missing = [col for col in _REQUIRED_CANONICAL if col not in raw_df.columns]
    if missing:
        raise errors.SchemaMismatch(
            f"Missing required columns: {missing}",
            code="SCHEMA_MISMATCH",
            missing_columns=missing,
        )

    # Step 3: Copy — never modify input
    work = raw_df.copy()

    # Step 4: Drop PII columns (canonical names present in work)
    pii_cols_dropped = [col for col in _PII_CANONICAL if col in work.columns]
    if pii_cols_dropped:
        work = work.drop(columns=pii_cols_dropped)

    # Step 5: EVCS branch
    if expand_evcs:
        evcs_df = _build_evcs_only_rows(work, target_month)
        aggregation_ms = (time.perf_counter() - t0) * 1000.0
        metadata: dict[str, Any] = {
            "input_rows": len(raw_df),
            "output_rows": len(evcs_df),
            "year_filtered": True,
            "pii_cols_dropped": pii_cols_dropped,
            "aggregation_ms": aggregation_ms,
            "month_parse_failed": 0,
            "expand_evcs": True,
            "evcs_rows": len(evcs_df),
        }
        return AggregateResult(df=evcs_df, metadata=metadata)

    # --- Base path ---

    # Step 6: Year filter — keep "26년"
    work = work[work["year"] == "26년"]
    if len(work) == 0:
        raise errors.EmptyResult(
            "No rows matching year='26년' after year filter",
            code="EMPTY_RESULT",
        )

    # Step 7: Month parsing — convert "1월" etc. to int; drop unparseable silently
    work["month_int"] = work["month"].map(raw_bp26.MONTH_MAP)
    month_parse_failed = int(work["month_int"].isna().sum())
    work = work.dropna(subset=["month_int"])
    work["month_int"] = work["month_int"].astype(int)

    # Step 8: Month filter — keep months <= target_month
    work = work[work["month_int"] <= target_month]

    # Step 9: Aggregate using shared pivot helper (base group keys)
    base = _aggregate_pivot(work, target_month, group_keys=_GROUP_KEYS)

    aggregation_ms = (time.perf_counter() - t0) * 1000.0

    # US-A6: silent drop 방지 — 파싱 실패율 1% 초과 시 경고 표면화
    parse_fail_ratio = month_parse_failed / max(1, len(raw_df))
    month_parse_warning = (
        f"월 파싱 실패 {month_parse_failed}행 ({parse_fail_ratio:.1%}) — 원본 month 값 확인 필요"
        if parse_fail_ratio > _MONTH_PARSE_WARN_RATIO
        else None
    )

    metadata = {
        "input_rows": len(raw_df),
        "output_rows": len(base),
        "year_filtered": True,
        "pii_cols_dropped": pii_cols_dropped,
        "aggregation_ms": aggregation_ms,
        "month_parse_failed": month_parse_failed,
        "month_parse_warning": month_parse_warning,
    }

    return AggregateResult(df=base, metadata=metadata)


def _build_evcs_only_rows(raw_df: pd.DataFrame, target_month: int) -> pd.DataFrame:
    """Generate EVCS-virtual rows from raw transactions.

    For each raw row, emit up to 2 virtual rows:
    - If rate_evcs_domestic > 0: org_l1='EVCS국내', amount = base x rate / 100
    - If rate_evcs_overseas > 0: org_l1='EVCS해외', amount = base x rate / 100

    Aggregates by (company, cost_center, gl_account, org_l1) into bp26 pivot.
    """
    work = raw_df.copy()

    # Year filter
    if "year" in work.columns:
        work = work[work["year"] == "26년"]
    if work.empty:
        return pd.DataFrame()

    # Month parsing
    if "month" in work.columns:
        work["month_int"] = work["month"].map(raw_bp26.MONTH_MAP)
        work = work[work["month_int"].notna()]
        work["month_int"] = work["month_int"].astype(int)
        work = work[work["month_int"] <= target_month]

    if work.empty:
        return pd.DataFrame()

    # EVCS row expansion via concat of two filtered+scaled views
    virtual_dfs = []

    for org_name, rate_col in [
        ("EVCS국내", "rate_evcs_domestic"),
        ("EVCS해외", "rate_evcs_overseas"),
    ]:
        if rate_col not in work.columns:
            continue
        slice_df = work[work[rate_col].fillna(0) > 0].copy()
        if slice_df.empty:
            continue
        slice_df["org_l1"] = org_name
        # Scale amount_krw by rate / 100.
        # 반올림 정책 (US-A4): 행 단위 원(KRW) 단위 round-half-even (banker's rounding).
        slice_df["amount_krw"] = (slice_df["amount_krw"] * slice_df[rate_col] / 100.0).round(0)
        virtual_dfs.append(slice_df)

    if not virtual_dfs:
        return pd.DataFrame()

    expanded = pd.concat(virtual_dfs, ignore_index=True)

    # Aggregate using shared pivot helper; org_l1 is a group key here
    evcs_group_keys = _GROUP_KEYS + ["org_l1"]
    return _aggregate_pivot(expanded, target_month, group_keys=evcs_group_keys)


def _aggregate_pivot(
    work: pd.DataFrame,
    target_month: int,
    group_keys: list[str],
) -> pd.DataFrame:
    """Pivot and aggregate a pre-filtered DataFrame into bp26-shaped output.

    Args:
        work: DataFrame already filtered for year and months <= target_month.
              Must have month_int column (int).
        target_month: Used for annual_actual and cum columns.
        group_keys: Columns to group by. For base path: _GROUP_KEYS.
                    For EVCS path: _GROUP_KEYS + ['org_l1'].

    Returns:
        bp26-shaped DataFrame with DEFAULT_COLUMNS as leading columns.
    """
    # Enrichment columns: carry forward first non-null per group.
    # Exclude any col that is already a group key (e.g., org_l1 in EVCS path).
    enrichment_present = [c for c in _ENRICHMENT_COLS if c in work.columns and c not in group_keys]
    rates_present = [c for c in _RATE_COLUMNS if c in work.columns]

    carry_cols = enrichment_present + rates_present
    if carry_cols:
        enrichment_df = work.groupby(group_keys)[carry_cols].first().reset_index()
    else:
        enrichment_df = work[group_keys].drop_duplicates().reset_index(drop=True)

    # Pivot budget and actual for each month 1..12
    budget_df = work[work["division_type"] == "예산"]
    actual_df = work[work["division_type"] == "실적"]

    budget_monthly = _pivot_monthly(budget_df, "budget", group_keys=group_keys)
    actual_monthly = _pivot_monthly(
        actual_df, "actual", max_month=target_month, group_keys=group_keys
    )

    # Merge group keys into a base frame
    all_groups = work[group_keys].drop_duplicates().reset_index(drop=True)

    base = all_groups.copy()
    base = base.merge(budget_monthly, on=group_keys, how="left")
    base = base.merge(actual_monthly, on=group_keys, how="left")

    # Fill missing monthly values with 0
    month_cols_budget = [f"m{m:02d}_budget" for m in range(1, 13)]
    month_cols_actual = [f"m{m:02d}_actual" for m in range(1, 13)]
    all_month_cols = month_cols_budget + month_cols_actual
    for col in all_month_cols:
        if col not in base.columns:
            base[col] = 0.0
    base[all_month_cols] = base[all_month_cols].fillna(0.0)

    # Cumulative columns via cumsum across columns
    budget_arr = base[[f"m{m:02d}_budget" for m in range(1, 13)]].values
    actual_arr = base[[f"m{m:02d}_actual" for m in range(1, 13)]].values

    budget_cum = np.cumsum(budget_arr, axis=1)
    actual_cum = np.cumsum(actual_arr, axis=1)

    for i, m in enumerate(range(1, 13)):
        base[f"cum{m:02d}_budget"] = budget_cum[:, i]
        base[f"cum{m:02d}_actual"] = actual_cum[:, i]

    # Annual columns
    base["annual_budget"] = base["cum12_budget"]
    base["annual_actual"] = base[f"cum{target_month:02d}_actual"]

    # Merge enrichment + rates
    base = base.merge(enrichment_df, on=group_keys, how="left")

    # Add division column (default "소조직")
    base["division"] = "소조직"

    # Add org_l2, org_l3 as empty strings (not in raw data)
    base["org_l2"] = ""
    base["org_l3"] = ""

    # Add org_l1 as empty string if not already present (base path case)
    if "org_l1" not in base.columns:
        base["org_l1"] = ""

    # Add text/remark/allocation_basis columns if missing
    for col in ["text_summary", "remark", "allocation_basis"]:
        if col not in base.columns:
            if "allocation_basis" in work.columns and col == "allocation_basis":
                ab = work.groupby(group_keys)["allocation_basis"].first().reset_index()
                base = base.merge(ab, on=group_keys, how="left")
            else:
                base[col] = ""

    # Ensure all bp26.DEFAULT_COLUMNS keys are present
    for col in bp26.DEFAULT_COLUMNS:
        if col not in base.columns:
            base[col] = (
                0
                if col
                not in (
                    "division",
                    "text_summary",
                    "remark",
                    "allocation_basis",
                    "org_l2",
                    "org_l3",
                )
                else ""
            )

    # Reorder: DEFAULT_COLUMNS first, then any extra rate columns
    extra_cols = [c for c in base.columns if c not in bp26.DEFAULT_COLUMNS]
    output_cols = bp26.DEFAULT_COLUMNS + extra_cols
    base = base[output_cols]

    # Fill any remaining NaN in numeric columns
    numeric_cols = base.select_dtypes(include="number").columns
    base[numeric_cols] = base[numeric_cols].fillna(0.0)

    return base


def _pivot_monthly(
    df: pd.DataFrame,
    suffix: str,
    max_month: int = 12,
    group_keys: list[str] | None = None,
) -> pd.DataFrame:
    """Pivot a budget or actual sub-DataFrame into monthly amount columns.

    Returns a DataFrame with group_keys + m01_{suffix}..m12_{suffix}.
    Months > max_month are set to 0.
    """
    if group_keys is None:
        group_keys = _GROUP_KEYS

    if df.empty:
        cols = group_keys + [f"m{m:02d}_{suffix}" for m in range(1, 13)]
        return pd.DataFrame(columns=cols)

    # Pivot: group by (group_keys + month_int), sum amount_krw
    pivot = df.groupby(group_keys + ["month_int"])["amount_krw"].sum().reset_index()

    # Unstack month_int into columns
    pivot = pivot.pivot_table(
        index=group_keys,
        columns="month_int",
        values="amount_krw",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    # Flatten column names: int -> f"m{m:02d}_{suffix}"
    new_cols = []
    for c in pivot.columns:
        if c in group_keys:
            new_cols.append(c)
        else:
            month_num = int(c)
            new_cols.append(f"m{month_num:02d}_{suffix}")
    pivot.columns = new_cols

    # Ensure all 12 month columns exist, zero-fill if absent
    for m in range(1, 13):
        col = f"m{m:02d}_{suffix}"
        if col not in pivot.columns:
            pivot[col] = 0.0
        elif m > max_month:
            # For actual, months beyond target_month should be 0
            pivot[col] = 0.0

    return pivot
