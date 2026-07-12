"""US-012 get_exchange_rates tests. Uses pytest-httpx — no live API calls."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import pytest

from humax_excel_mcp.core import errors
from humax_excel_mcp.tools import exchange as exchange_mod
from humax_excel_mcp.tools.exchange import get_exchange_rates

URL_RE = re.compile(r".*exchangeJSON.*")
pytestmark = pytest.mark.asyncio

KST = timezone(timedelta(hours=9))


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("EXCHANGE_RATE_API_KEY", "test-key-xxx")
    exchange_mod._clear_state_for_tests()
    yield
    exchange_mod._clear_state_for_tests()


def _today() -> str:
    return datetime.now(KST).strftime("%Y%m%d")


def _ok_payload(usd: str = "1,393.00", jpy: str = "899.45") -> list[dict]:
    return [
        {
            "result": 1,
            "cur_unit": "USD",
            "cur_nm": "미국 달러",
            "deal_bas_r": usd,
            "ttb": "1,378.50",
            "tts": "1,407.50",
            "kftc_deal_bas_r": usd,
        },
        {
            "result": 1,
            "cur_unit": "JPY(100)",
            "cur_nm": "일본 옌",
            "deal_bas_r": jpy,
            "ttb": "890.54",
            "tts": "908.36",
            "kftc_deal_bas_r": jpy,
        },
    ]


async def test_api_success_returns_rates(httpx_mock) -> None:
    httpx_mock.add_response(method="GET", url=URL_RE, json=_ok_payload())
    res = await get_exchange_rates(search_date=_today())
    assert res.success
    assert len(res.data.rates) == 2
    assert res.metadata["cached"] is False


async def test_jpy_normalization(httpx_mock) -> None:
    httpx_mock.add_response(method="GET", url=URL_RE, json=_ok_payload())
    res = await get_exchange_rates(search_date=_today())
    jpy = next(r for r in res.data.rates if r.cur_unit == "JPY(100)")
    assert jpy.unit_multiplier == 100
    assert jpy.cur_unit_normalized == "JPY"
    assert jpy.deal_bas_r_per_unit is not None
    assert abs(jpy.deal_bas_r_per_unit - 8.9945) < 0.0001


async def test_target_currencies_filter(httpx_mock) -> None:
    httpx_mock.add_response(method="GET", url=URL_RE, json=_ok_payload())
    res = await get_exchange_rates(search_date=_today(), target_currencies=["USD"])
    assert len(res.data.rates) == 1
    assert res.data.rates[0].cur_unit == "USD"


async def test_invalid_currency() -> None:
    with pytest.raises(errors.InvalidCurrency):
        await get_exchange_rates(search_date=_today(), target_currencies=["XYZ"])


async def test_api_key_missing(monkeypatch) -> None:
    monkeypatch.delenv("EXCHANGE_RATE_API_KEY", raising=False)
    # Block config.get from reading .env file in repo (which sets the key)
    from humax_excel_mcp import config as cfg

    monkeypatch.setattr(cfg, "load_env", lambda *a, **k: None)
    with pytest.raises(errors.ApiKeyMissing):
        await get_exchange_rates(search_date=_today())


async def test_invalid_date_format() -> None:
    with pytest.raises(errors.InvalidDateFormat):
        await get_exchange_rates(search_date="2026-05-19")
    with pytest.raises(errors.InvalidDateFormat):
        await get_exchange_rates(search_date="2026051x")


async def test_future_date() -> None:
    future = (datetime.now(KST) + timedelta(days=10)).strftime("%Y%m%d")
    with pytest.raises(errors.FutureDate):
        await get_exchange_rates(search_date=future)


async def test_empty_with_no_fallback(httpx_mock) -> None:
    httpx_mock.add_response(method="GET", url=URL_RE, json=[])
    with pytest.raises(errors.NoDataForDate):
        await get_exchange_rates(search_date=_today(), fallback_to_previous=False)


async def test_fallback_finds_previous(httpx_mock) -> None:
    """S-1: fallback은 D-1..D-7 병렬 조회 — 날짜별 응답 등록으로 최근접 선택 검증."""
    today = _today()
    now = datetime.now(KST)
    httpx_mock.add_response(method="GET", url=re.compile(f".*searchdate={today}.*"), json=[])
    d1 = (now - timedelta(days=1)).strftime("%Y%m%d")
    httpx_mock.add_response(
        method="GET", url=re.compile(f".*searchdate={d1}.*"), json=_ok_payload()
    )
    for back in range(2, 8):
        dt = (now - timedelta(days=back)).strftime("%Y%m%d")
        httpx_mock.add_response(method="GET", url=re.compile(f".*searchdate={dt}.*"), json=[])
    res = await get_exchange_rates(search_date=today)
    assert res.metadata["fallback_used"] is True
    assert res.metadata["fallback_days_back"] == 1


async def test_fallback_exhausted(httpx_mock) -> None:
    # 1 initial + 7 fallback attempts = 8 total empty responses
    for _ in range(8):
        httpx_mock.add_response(method="GET", url=URL_RE, json=[])
    with pytest.raises(errors.FallbackExhausted):
        await get_exchange_rates(search_date=_today())


async def test_cache_hit_on_second_call(httpx_mock) -> None:
    httpx_mock.add_response(method="GET", url=URL_RE, json=_ok_payload())
    res1 = await get_exchange_rates(search_date=_today())
    res2 = await get_exchange_rates(search_date=_today())
    assert res1.metadata["cached"] is False
    assert res2.metadata["cached"] is True


async def test_api_timeout(httpx_mock) -> None:
    import httpx as _httpx

    httpx_mock.add_exception(_httpx.ReadTimeout("timeout"))
    with pytest.raises(errors.ApiRequestFailed):
        await get_exchange_rates(search_date=_today())


async def test_rate_limit(httpx_mock) -> None:
    httpx_mock.add_response(method="GET", url=URL_RE, status_code=429, json={})
    with pytest.raises(errors.ApiRateLimit):
        await get_exchange_rates(search_date=_today())


async def test_sanity_warning_on_20pct_jump(httpx_mock) -> None:
    """전 영업일 대비 20% 초과 변동 감지 (US-A2: 같은 날짜끼리 비교하던 dead code 교체)."""
    prev_day = (datetime.now(KST) - timedelta(days=1)).strftime("%Y%m%d")
    httpx_mock.add_response(method="GET", url=URL_RE, json=_ok_payload(usd="1,000.00"))
    await get_exchange_rates(search_date=prev_day)
    httpx_mock.add_response(method="GET", url=URL_RE, json=_ok_payload(usd="2,000.00"))
    res2 = await get_exchange_rates(search_date=_today())
    usd = next(r for r in res2.data.rates if r.cur_unit == "USD")
    assert usd.sanity_warning is True


async def test_sanity_compares_previous_business_day(httpx_mock) -> None:
    """US-A2: 전 영업일 대비 20% 초과 변동 시 sanity_warning. 캐시 경로에서도 유지."""
    prev_day = (datetime.now(KST) - timedelta(days=1)).strftime("%Y%m%d")
    httpx_mock.add_response(method="GET", url=URL_RE, json=_ok_payload(usd="1,000.00"))
    await get_exchange_rates(search_date=prev_day)

    httpx_mock.add_response(method="GET", url=URL_RE, json=_ok_payload(usd="1,300.00"))
    res = await get_exchange_rates(search_date=_today())
    usd = next(r for r in res.data.rates if r.cur_unit == "USD")
    assert usd.sanity_warning is True

    res2 = await get_exchange_rates(search_date=_today())
    assert res2.metadata["cached"] is True
    usd2 = next(r for r in res2.data.rates if r.cur_unit == "USD")
    assert usd2.sanity_warning is True


async def test_fetch_is_async() -> None:
    """US-S1: 이벤트루프 블로킹 금지 — _fetch는 코루틴이어야 한다."""
    import asyncio

    assert asyncio.iscoroutinefunction(exchange_mod._fetch)


async def test_live_artifact_hints(httpx_mock) -> None:
    httpx_mock.add_response(method="GET", url=URL_RE, json=_ok_payload())
    res = await get_exchange_rates(search_date=_today(), render_format="live_artifact")
    assert res.artifact_hints is not None
    assert res.artifact_hints.type == "rates_dashboard"
