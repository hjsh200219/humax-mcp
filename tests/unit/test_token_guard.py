"""US-005 token_guard tests."""

from __future__ import annotations

from humax_excel_mcp.core import token_guard


def test_estimate_size_kb() -> None:
    obj = [{"x": "a" * 1000} for _ in range(10)]
    assert token_guard.estimate_size_kb(obj) > 5


def test_detect_pii_rrn() -> None:
    assert token_guard.detect_pii("주민번호 901231-1234567 확인")


def test_detect_pii_phone() -> None:
    assert token_guard.detect_pii("연락처 010-1234-5678")


def test_detect_pii_sabun() -> None:
    assert token_guard.detect_pii("사번 12345 김홍삼")


def test_detect_pii_none() -> None:
    assert not token_guard.detect_pii("그냥 적요 텍스트")


def test_auto_truncate_by_max_rows() -> None:
    rows = [{"i": i, "x": "y"} for i in range(1000)]
    out, truncated = token_guard.auto_truncate(rows, max_rows=50)
    assert len(out) == 50
    assert truncated is True


def test_auto_truncate_by_size() -> None:
    big = [{"x": "a" * 5000} for _ in range(200)]
    out, truncated = token_guard.auto_truncate(big, max_rows=1000, hard_limit_kb=100)
    assert truncated is True
    assert token_guard.estimate_size_kb(out) <= 100


def test_scan_rows_for_pii() -> None:
    rows = [{"text": "정상"}, {"text": "010-1234-5678 노출"}]
    assert token_guard.scan_rows_for_pii(rows)
    assert not token_guard.scan_rows_for_pii([{"text": "정상"}])
