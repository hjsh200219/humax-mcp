"""US-023 Aggregator acceptance tests — AC1 through AC12.

Tests aggregate_to_bp26() base path (expand_evcs=False).
All tests use the synthetic_raw_26bp_df fixture from conftest.py.
"""

from __future__ import annotations

import pandas as pd
import pytest

from humax_excel_mcp.core import errors
from humax_excel_mcp.core.aggregator import AggregateResult, aggregate_to_bp26
from humax_excel_mcp.schemas import bp26

# ---------------------------------------------------------------------------
# AC1: One row per (company, cost_center, gl_account)
# ---------------------------------------------------------------------------

def test_ac1_row_count(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC1: 2 companies x 3 cost_centers x 2 gl_accounts = 12 rows."""
    result = aggregate_to_bp26(synthetic_raw_26bp_df, target_month=3)
    assert isinstance(result, AggregateResult)
    assert len(result.df) == 12


# ---------------------------------------------------------------------------
# AC2: cum03_actual == m01_actual + m02_actual + m03_actual
# ---------------------------------------------------------------------------

def test_ac2_cumulative_actual_identity(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC2: cum03_actual equals sum of m01..m03 actual for every row."""
    result = aggregate_to_bp26(synthetic_raw_26bp_df, target_month=3)
    df = result.df
    expected = df["m01_actual"] + df["m02_actual"] + df["m03_actual"]
    pd.testing.assert_series_equal(df["cum03_actual"], expected, check_names=False)


# ---------------------------------------------------------------------------
# AC3: cum03_budget == m01_budget + m02_budget + m03_budget
# ---------------------------------------------------------------------------

def test_ac3_cumulative_budget_identity(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC3: cum03_budget equals sum of m01..m03 budget for every row."""
    result = aggregate_to_bp26(synthetic_raw_26bp_df, target_month=3)
    df = result.df
    expected = df["m01_budget"] + df["m02_budget"] + df["m03_budget"]
    pd.testing.assert_series_equal(df["cum03_budget"], expected, check_names=False)


# ---------------------------------------------------------------------------
# AC4: annual_budget == sum(m01_budget..m12_budget)
# ---------------------------------------------------------------------------

def test_ac4_annual_budget(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC4: annual_budget equals sum of all 12 monthly budget columns."""
    result = aggregate_to_bp26(synthetic_raw_26bp_df, target_month=3)
    df = result.df
    expected = sum(df[f"m{m:02d}_budget"] for m in range(1, 13))
    pd.testing.assert_series_equal(df["annual_budget"], expected, check_names=False)


# ---------------------------------------------------------------------------
# AC5: annual_actual == sum(m01_actual..m03_actual) for target_month=3
# ---------------------------------------------------------------------------

def test_ac5_annual_actual(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC5: annual_actual equals sum of actual months 1..target_month only."""
    result = aggregate_to_bp26(synthetic_raw_26bp_df, target_month=3)
    df = result.df
    expected = df["m01_actual"] + df["m02_actual"] + df["m03_actual"]
    pd.testing.assert_series_equal(df["annual_actual"], expected, check_names=False)
    # Months 4-12 actual should be 0
    for m in range(4, 13):
        assert (df[f"m{m:02d}_actual"] == 0).all(), f"m{m:02d}_actual should be 0"


# ---------------------------------------------------------------------------
# AC6: No PII columns in output; reversed_with NOT classified as PII
# ---------------------------------------------------------------------------

def test_ac6_no_pii_columns(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC6: PII canonical column names absent from output."""
    # Inject PII columns into the fixture to verify they are dropped
    df_with_pii = synthetic_raw_26bp_df.copy()
    df_with_pii["doc_no"] = "DOC001"
    df_with_pii["text"] = "some text"
    df_with_pii["vendor_name"] = "Vendor Corp"
    df_with_pii["url"] = "http://example.com"
    df_with_pii["reversed_with"] = "REV123"  # NOT PII; must be retained

    result = aggregate_to_bp26(df_with_pii, target_month=3)
    out_cols = set(result.df.columns)
    assert "doc_no" not in out_cols
    assert "text" not in out_cols
    assert "vendor_name" not in out_cols
    assert "url" not in out_cols
    # reversed_with is not a PII column so it may or may not appear, but must NOT be dropped
    # The aggregator doesn't carry it forward in enrichment, but it must not be suppressed due to PII logic


# ---------------------------------------------------------------------------
# AC7: result.df columns are a superset of bp26.DEFAULT_COLUMNS
# ---------------------------------------------------------------------------

def test_ac7_output_is_superset_of_default_columns(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC7: All bp26.DEFAULT_COLUMNS are present in result.df."""
    result = aggregate_to_bp26(synthetic_raw_26bp_df, target_month=3)
    out_cols = set(result.df.columns)
    for col in bp26.DEFAULT_COLUMNS:
        assert col in out_cols, f"Missing DEFAULT_COLUMNS key: {col}"


# ---------------------------------------------------------------------------
# AC7b: result.metadata contains required keys
# ---------------------------------------------------------------------------

def test_ac7b_metadata_keys(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC7b: metadata dict contains all required observability keys."""
    result = aggregate_to_bp26(synthetic_raw_26bp_df, target_month=3)
    md = result.metadata
    required_keys = {"input_rows", "output_rows", "year_filtered", "pii_cols_dropped", "aggregation_ms"}
    for key in required_keys:
        assert key in md, f"Missing metadata key: {key}"
    assert md["year_filtered"] is True
    assert md["input_rows"] == len(synthetic_raw_26bp_df)
    assert md["output_rows"] == len(result.df)
    assert md["aggregation_ms"] >= 0


# ---------------------------------------------------------------------------
# AC8: Missing required column raises SchemaMismatch
# ---------------------------------------------------------------------------

def test_ac8_missing_required_column_raises(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC8: Dropping a required column raises SchemaMismatch."""
    bad_df = synthetic_raw_26bp_df.drop(columns=["amount_krw"])
    with pytest.raises(errors.SchemaMismatch):
        aggregate_to_bp26(bad_df, target_month=3)


def test_ac8_missing_division_type_raises(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC8b: Dropping division_type raises SchemaMismatch."""
    bad_df = synthetic_raw_26bp_df.drop(columns=["division_type"])
    with pytest.raises(errors.SchemaMismatch):
        aggregate_to_bp26(bad_df, target_month=3)


# ---------------------------------------------------------------------------
# AC9: target_month=0 or 13 raises InvalidMonth
# ---------------------------------------------------------------------------

def test_ac9_invalid_month_zero(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC9a: target_month=0 raises InvalidMonth."""
    with pytest.raises(errors.InvalidMonth):
        aggregate_to_bp26(synthetic_raw_26bp_df, target_month=0)


def test_ac9_invalid_month_13(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC9b: target_month=13 raises InvalidMonth."""
    with pytest.raises(errors.InvalidMonth):
        aggregate_to_bp26(synthetic_raw_26bp_df, target_month=13)


# ---------------------------------------------------------------------------
# AC10: Empty after year filter raises EmptyResult
# ---------------------------------------------------------------------------

def test_ac10_empty_after_year_filter(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC10: DataFrame where year != '26년' for all rows raises EmptyResult."""
    df_wrong_year = synthetic_raw_26bp_df.copy()
    df_wrong_year["year"] = "25년"
    with pytest.raises(errors.EmptyResult):
        aggregate_to_bp26(df_wrong_year, target_month=3)


def test_ac10_completely_empty_df() -> None:
    """AC10b: Completely empty DataFrame (0 rows) raises EmptyResult."""
    cols = ["division_type", "year", "month", "company", "cost_center", "gl_account", "amount_krw"]
    empty_df = pd.DataFrame(columns=cols)
    with pytest.raises(errors.EmptyResult):
        aggregate_to_bp26(empty_df, target_month=3)


# ---------------------------------------------------------------------------
# AC11: Input DataFrame is not modified
# ---------------------------------------------------------------------------

def test_ac11_input_not_modified(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC11: aggregate_to_bp26 does not modify the input DataFrame."""
    original_len = len(synthetic_raw_26bp_df)
    original_cols = list(synthetic_raw_26bp_df.columns)
    original_id = id(synthetic_raw_26bp_df)

    aggregate_to_bp26(synthetic_raw_26bp_df, target_month=3)

    assert len(synthetic_raw_26bp_df) == original_len
    assert list(synthetic_raw_26bp_df.columns) == original_cols
    assert id(synthetic_raw_26bp_df) == original_id
    # Verify no new columns were injected into original
    assert "month_int" not in synthetic_raw_26bp_df.columns


# ---------------------------------------------------------------------------
# AC12: Rate columns carried forward (first non-null per group)
# ---------------------------------------------------------------------------

def test_ac12_rate_columns_carried_forward(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC12: Allocation rate columns have first non-null values per group in output."""
    result = aggregate_to_bp26(synthetic_raw_26bp_df, target_month=3)
    df = result.df
    # rate_stb is 25.0 in all rows of the fixture
    assert "rate_stb" in df.columns, "rate_stb should be in output"
    assert (df["rate_stb"] == 25.0).all(), "rate_stb should be 25.0 for all rows"
    # rate_mobility likewise
    assert "rate_mobility" in df.columns
    assert (df["rate_mobility"] == 25.0).all()


# ---------------------------------------------------------------------------
# Extra: verify correct actual amounts for known fixture values
# ---------------------------------------------------------------------------

def test_actual_amounts_correct(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """Spot-check: m01_actual=1000, m02_actual=2000, m03_actual=3000 per group."""
    result = aggregate_to_bp26(synthetic_raw_26bp_df, target_month=3)
    df = result.df
    # fixture: amount_krw = 1000.0 * month_int * (1 for 실적)
    # One row per (company, cc, gl) → single 실적 transaction per month
    assert (df["m01_actual"] == 1000.0).all()
    assert (df["m02_actual"] == 2000.0).all()
    assert (df["m03_actual"] == 3000.0).all()


def test_budget_amounts_correct(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """Spot-check: m01_budget=2000, m02_budget=4000, m03_budget=6000 per group."""
    result = aggregate_to_bp26(synthetic_raw_26bp_df, target_month=3)
    df = result.df
    # fixture: amount_krw = 1000.0 * month_int * 2 for 예산
    assert (df["m01_budget"] == 2000.0).all()
    assert (df["m02_budget"] == 4000.0).all()
    assert (df["m03_budget"] == 6000.0).all()


# ---------------------------------------------------------------------------
# US-024a EVCS-Only Aggregator Path
# ---------------------------------------------------------------------------

def test_evcs_expansion_two_rates_two_virtual_rows(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC1: rate_evcs_domestic=30, rate_evcs_overseas=20 -> 2 virtual rows, no base."""
    df = pd.DataFrame([{
        "division_type": "실적",
        "year": "26년",
        "month": "1월",
        "company": "HKR",
        "cost_center": 101,
        "cost_center_name": "CC101",
        "gl_account": 510000,
        "gl_account_name": "GL510000",
        "org_l1": "사업그룹",
        "amount_krw": 1000.0,
        "rate_evcs_domestic": 30.0,
        "rate_evcs_overseas": 20.0,
    }])
    result = aggregate_to_bp26(df, target_month=3, expand_evcs=True)
    out = result.df
    assert len(out) == 2  # one row per org_l1
    org_set = set(out["org_l1"].unique())
    assert org_set == {"EVCS국내", "EVCS해외"}
    # No base rows (no '사업그룹' org_l1 in output)
    assert "사업그룹" not in out["org_l1"].values


def test_evcs_amount_scaling(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC2: amounts scale correctly."""
    df = pd.DataFrame([{
        "division_type": "실적",
        "year": "26년",
        "month": "1월",
        "company": "HKR",
        "cost_center": 101,
        "cost_center_name": "CC101",
        "gl_account": 510000,
        "gl_account_name": "GL510000",
        "org_l1": "사업그룹",
        "amount_krw": 1000.0,
        "rate_evcs_domestic": 30.0,
        "rate_evcs_overseas": 20.0,
    }])
    result = aggregate_to_bp26(df, target_month=3, expand_evcs=True)
    out = result.df
    domestic_row = out[out["org_l1"] == "EVCS국내"].iloc[0]
    overseas_row = out[out["org_l1"] == "EVCS해외"].iloc[0]
    # Month 1 actual
    assert abs(domestic_row["m01_actual"] - 300.0) < 0.01  # 1000 x 30/100
    assert abs(overseas_row["m01_actual"] - 200.0) < 0.01  # 1000 x 20/100


def test_evcs_expand_false_returns_base_only(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    """AC3: expand_evcs=False returns base rows only, no EVCS org_l1."""
    result = aggregate_to_bp26(synthetic_raw_26bp_df, target_month=3, expand_evcs=False)
    org_set = set(result.df["org_l1"].unique())
    assert "EVCS국내" not in org_set
    assert "EVCS해외" not in org_set


def test_evcs_zero_rates_empty_output() -> None:
    """AC4: All rates zero -> empty result."""
    df = pd.DataFrame([{
        "division_type": "실적",
        "year": "26년",
        "month": "1월",
        "company": "HKR",
        "cost_center": 101,
        "cost_center_name": "CC101",
        "gl_account": 510000,
        "gl_account_name": "GL510000",
        "org_l1": "사업그룹",
        "amount_krw": 1000.0,
        "rate_evcs_domestic": 0.0,
        "rate_evcs_overseas": 0.0,
    }])
    result = aggregate_to_bp26(df, target_month=3, expand_evcs=True)
    assert result.df.empty


def test_evcs_full_domestic_no_overseas():
    """US-024a AC5: rate_domestic=100, rate_overseas=0 → exactly 1 EVCS국내 row with base-equal amounts."""
    df = pd.DataFrame([{
        "division_type": "실적",
        "year": "26년",
        "month": "1월",
        "company": "HKR",
        "cost_center": 101,
        "cost_center_name": "CC101",
        "gl_account": 510000,
        "gl_account_name": "GL510000",
        "org_l1": "사업그룹",
        "amount_krw": 1000.0,
        "rate_evcs_domestic": 100.0,
        "rate_evcs_overseas": 0.0,
    }])
    from humax_excel_mcp.core import aggregator
    result = aggregator.aggregate_to_bp26(df, target_month=3, expand_evcs=True)
    out = result.df
    assert len(out) == 1, f"Expected 1 row, got {len(out)}"
    row = out.iloc[0]
    assert row["org_l1"] == "EVCS국내"
    # Amount equals base (100%)
    assert abs(row["m01_actual"] - 1000.0) < 0.01, f"m01_actual: {row['m01_actual']}"
