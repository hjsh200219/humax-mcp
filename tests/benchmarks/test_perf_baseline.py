"""성능 baseline 측정 — accuracy-speed PRD 벤치마크 게이트 (advisory).

느슨한 상한(회귀 안전판)만 assert. 수치는 -s 실행 시 stdout으로 보고.
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import pytest

from tests.conftest import _build_workbook

pytestmark = pytest.mark.benchmark

_SANITY_CEILING_S = 30.0


@pytest.fixture(scope="module")
def large_26bp(tmp_path_factory) -> Path:
    # 4 BU x 3 대조직 x 3 중조직 x 2 소조직 x 14 = 1,008 소조직 행 + 총합계
    p = tmp_path_factory.mktemp("bench") / "large_26bp.xlsx"
    return _build_workbook(p, seed=7, rows_per_org=7)


async def test_bench_extract_cold_vs_warm(large_26bp: Path) -> None:
    from humax_excel_mcp.core import workbook_cache
    from humax_excel_mcp.tools.extract import extract_filtered

    workbook_cache.clear()
    t0 = time.perf_counter()
    await extract_filtered(str(large_26bp), "예산+실적")
    cold = time.perf_counter() - t0

    t0 = time.perf_counter()
    await extract_filtered(str(large_26bp), "예산+실적")
    warm = time.perf_counter() - t0

    print(f"\n[bench] extract cold={cold * 1000:.0f}ms warm={warm * 1000:.0f}ms")
    assert workbook_cache.stats["hits"] >= 1, "2회차 호출은 캐시 히트여야 한다 (US-S3)"
    assert warm <= cold
    assert cold < _SANITY_CEILING_S


async def test_bench_verify_sums(large_26bp: Path) -> None:
    from humax_excel_mcp.tools.verify import verify_sums

    t0 = time.perf_counter()
    res = await verify_sums(str(large_26bp), "예산+실적")
    dur = time.perf_counter() - t0
    print(f"\n[bench] verify_sums {dur * 1000:.0f}ms (levels={res.summary.total_checks})")
    assert res.summary.total_checks == 5
    assert dur < _SANITY_CEILING_S


def test_bench_aggregate(synthetic_raw_26bp_df: pd.DataFrame) -> None:
    from humax_excel_mcp.core.aggregator import aggregate_to_bp26

    big = pd.concat([synthetic_raw_26bp_df] * 100, ignore_index=True)  # 7,200 rows
    t0 = time.perf_counter()
    result = aggregate_to_bp26(big, target_month=3)
    dur = time.perf_counter() - t0
    print(
        f"\n[bench] aggregate {len(big)}rows {dur * 1000:.0f}ms "
        f"(reported={result.metadata['aggregation_ms']:.0f}ms)"
    )
    assert dur < _SANITY_CEILING_S
