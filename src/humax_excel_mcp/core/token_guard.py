"""Token / payload size guard + PII regex detection."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any

SOFT_LIMIT_KB = 50
HARD_LIMIT_KB = 100

_PII_PATTERNS = [
    re.compile(r"\b\d{6}-\d{7}\b"),  # 주민등록번호
    re.compile(r"\bRRN\b", re.IGNORECASE),
    re.compile(r"(?<!\d)0\d{1,2}-\d{3,4}-\d{4}(?!\d)"),  # KR 전화번호
    re.compile(r"\bemp\d{5,}\b", re.IGNORECASE),
    re.compile(r"\b사번[\s:#-]*\d{4,}\b"),
]


def estimate_size_kb(obj: Any) -> float:
    raw = json.dumps(obj, ensure_ascii=False, default=str)
    return len(raw.encode("utf-8")) / 1024.0


def estimate_tokens(obj: Any) -> int:
    """Rough estimate: 1 token ~= 3 bytes UTF-8 for mixed JA/KR text."""
    raw = json.dumps(obj, ensure_ascii=False, default=str)
    return max(1, len(raw.encode("utf-8")) // 3)


def detect_pii(text: str) -> bool:
    if not text:
        return False
    return any(p.search(text) for p in _PII_PATTERNS)


def scan_rows_for_pii(rows: Iterable[dict[str, Any]], *, columns: list[str] | None = None) -> bool:
    cols = set(columns) if columns else None
    for row in rows:
        for k, v in row.items():
            if cols is not None and k not in cols:
                continue
            if isinstance(v, str) and detect_pii(v):
                return True
    return False


def auto_truncate(
    rows: list[dict[str, Any]],
    *,
    max_rows: int,
    hard_limit_kb: float = HARD_LIMIT_KB,
) -> tuple[list[dict[str, Any]], bool]:
    """Truncate to max_rows, then shrink proportionally while serialized > hard_limit_kb.

    측정 크기 비례 축소로 전체 재직렬화 횟수를 1-2회로 제한 (US-S4).
    Returns (rows, truncated).
    """
    truncated = False
    if len(rows) > max_rows:
        rows = rows[:max_rows]
        truncated = True
    size_kb = estimate_size_kb(rows) if rows else 0.0
    while rows and size_kb > hard_limit_kb:
        keep = int(len(rows) * hard_limit_kb / size_kb * 0.9)
        keep = max(1, min(keep, len(rows) - 1))
        rows = rows[:keep]
        truncated = True
        size_kb = estimate_size_kb(rows)
    return rows, truncated
