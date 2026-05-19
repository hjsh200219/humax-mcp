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
    """Truncate to max_rows, then shrink further if serialized > hard_limit_kb.

    Returns (rows, truncated).
    """
    truncated = False
    if len(rows) > max_rows:
        rows = rows[:max_rows]
        truncated = True
    while rows and estimate_size_kb(rows) > hard_limit_kb:
        rows = rows[: max(1, int(len(rows) * 0.75))]
        truncated = True
    return rows, truncated
