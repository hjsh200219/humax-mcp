"""Session-scoped parsed-workbook cache — accuracy-speed PRD US-S3.

Key = (resolved path, mtime_ns, size, sheet, schema, header_row, normalize).
File modification changes mtime_ns/size → stale entries never match (self-invalidating).
Returned DataFrames are copies; callers may mutate freely.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

import pandas as pd

from . import excel_io

_MAX_ENTRIES = 16

_cache: OrderedDict[tuple, pd.DataFrame] = OrderedDict()
stats = {"hits": 0, "misses": 0}


def _file_signature(path: str | Path) -> tuple[str, int, int]:
    p = excel_io.assert_xlsx_path(path)
    st = p.stat()
    return (str(p.resolve()), st.st_mtime_ns, st.st_size)


def get_dataframe(
    path: str | Path,
    sheet_name: str,
    *,
    schema_module: str = "bp26",
    header_row: int | None = None,
    normalize: bool = True,
) -> pd.DataFrame:
    """Load a worksheet as DataFrame with read_only parsing + LRU cache."""
    sig = _file_signature(path)
    key = (*sig, sheet_name, schema_module, header_row, normalize)
    if key in _cache:
        _cache.move_to_end(key)
        stats["hits"] += 1
        return _cache[key].copy()

    stats["misses"] += 1
    wb = excel_io.load_workbook_safe(path, data_only=True, read_only=True)
    try:
        ws = excel_io.get_sheet(wb, sheet_name)
        df = excel_io.worksheet_to_dataframe(
            ws, header_row=header_row, schema_module=schema_module, normalize=normalize
        )
    finally:
        wb.close()

    _cache[key] = df
    while len(_cache) > _MAX_ENTRIES:
        _cache.popitem(last=False)
    return df.copy()


def invalidate(path: str | Path) -> None:
    """Drop all cached entries for a path (write/restore 후 호출)."""
    target = str(Path(path).resolve())
    for key in [k for k in _cache if k[0] == target]:
        _cache.pop(key, None)


def clear() -> None:
    _cache.clear()
    stats["hits"] = 0
    stats["misses"] = 0
