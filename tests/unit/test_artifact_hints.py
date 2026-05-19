"""US-005 artifact_hints tests."""

from __future__ import annotations

from humax_excel_mcp.core.artifact_hints import build_hints, maybe_hints


def test_build_hints_basic() -> None:
    h = build_hints(
        "table_with_chart",
        "3월 본사 인건비",
        preferred_chart="bar",
        columns_for_chart=["a", "b"],
    )
    assert h.type == "table_with_chart"
    assert h.title == "3월 본사 인건비"
    assert h.preferred_chart == "bar"
    assert h.columns_for_chart == ["a", "b"]
    assert h.pii_redacted is False


def test_maybe_hints_excel_returns_none() -> None:
    assert maybe_hints("excel", artifact_type="table", title="t") is None


def test_maybe_hints_live_artifact_returns_hints() -> None:
    h = maybe_hints("live_artifact", artifact_type="table", title="t")
    assert h is not None
    assert h.type == "table"


def test_maybe_hints_both_returns_hints() -> None:
    h = maybe_hints("both", artifact_type="diff_cards", title="d", preferred_chart="bar")
    assert h is not None
    assert h.type == "diff_cards"
