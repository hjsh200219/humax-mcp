"""get_exchange_rates tool — PRD §4.8 + accuracy-speed PRD US-A2/S-1.

Korea Eximbank API. httpx.AsyncClient (이벤트루프 비블로킹),
휴일 fallback은 D-1..D-7 병렬 조회 후 최근접 영업일 선택.
sanity check는 직전 영업일 매매기준율 대비 20% 초과 변동을 감지.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import httpx

from .. import config
from ..core import artifact_hints as ah
from ..core import errors
from ..schemas.responses import ExchangeRate, ExchangeRatesData, ExchangeRatesResult

API_URL = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"
TIMEOUT_SECONDS = 5.0
CACHE_TTL_SECONDS = 12 * 3600
FALLBACK_MAX_DAYS = 7
SANITY_LOOKBACK_MAX_DAYS = 7

KST = timezone(timedelta(hours=9))

UNIT_100_CURRENCIES = {"JPY(100)", "IDR(100)"}

SUPPORTED_CURRENCIES = {
    "USD",
    "EUR",
    "JPY(100)",
    "CNH",
    "GBP",
    "HKD",
    "CHF",
    "CAD",
    "AUD",
    "SGD",
    "THB",
    "SEK",
    "NZD",
    "BRL",
    "IDR(100)",
}

_cache: dict[tuple[str, tuple[str, ...] | None], tuple[float, dict]] = {}
_rates_by_date: dict[str, dict[str, float]] = {}


def _today_kst_yyyymmdd() -> str:
    return datetime.now(KST).strftime("%Y%m%d")


def _parse_numeric(value: Any) -> float:
    if value is None:
        raise ValueError("None")
    if isinstance(value, int | float):
        return float(value)
    text = str(value).replace(",", "").strip()
    if not text:
        return 0.0
    return float(text)


def _normalize_rate(raw: dict) -> ExchangeRate:
    fields = ["deal_bas_r", "ttb", "tts", "bkpr", "kftc_bkpr", "kftc_deal_bas_r"]
    parsed: dict[str, Any] = {}
    for f in fields:
        if f in raw:
            try:
                parsed[f] = _parse_numeric(raw[f])
            except (TypeError, ValueError) as exc:
                raise errors.ApiRequestFailed(f"PARSE_ERROR: {f}={raw.get(f)} — {exc}") from exc
    cur_unit = raw.get("cur_unit", "")
    unit_multiplier = None
    cur_unit_normalized = None
    deal_bas_r_per_unit = None
    if cur_unit in UNIT_100_CURRENCIES:
        unit_multiplier = 100
        cur_unit_normalized = cur_unit.split("(")[0]
        if "deal_bas_r" in parsed:
            deal_bas_r_per_unit = parsed["deal_bas_r"] / 100.0
    return ExchangeRate(
        cur_unit=cur_unit,
        cur_nm=raw.get("cur_nm"),
        deal_bas_r=parsed.get("deal_bas_r", 0.0),
        ttb=parsed.get("ttb"),
        tts=parsed.get("tts"),
        kftc_deal_bas_r=parsed.get("kftc_deal_bas_r"),
        cur_unit_normalized=cur_unit_normalized,
        unit_multiplier=unit_multiplier,
        deal_bas_r_per_unit=deal_bas_r_per_unit,
    )


async def _fetch(api_key: str, date: str) -> list[dict]:
    params = {"authkey": api_key, "searchdate": date, "data": "AP01"}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.get(API_URL, params=params)
    except httpx.HTTPError as exc:
        raise errors.ApiRequestFailed(
            f"한국수출입은행 API 요청 실패: network error — {exc}. timeout={TIMEOUT_SECONDS}s"
        ) from exc
    if resp.status_code == 429:
        raise errors.ApiRateLimit("한국수출입은행 API 일일 호출 한도(1,000건)를 초과했습니다.")
    if resp.status_code != 200:
        raise errors.ApiRequestFailed(
            f"한국수출입은행 API 요청 실패: {resp.status_code}. timeout={TIMEOUT_SECONDS}s"
        )
    try:
        data = resp.json()
    except ValueError as exc:
        raise errors.ApiRequestFailed(f"JSON 파싱 실패: {exc}") from exc
    if not isinstance(data, list):
        return []
    return [r for r in data if r.get("result", 0) == 1]


def _back_dates(from_date: str, max_days: int) -> list[str]:
    d = datetime.strptime(from_date, "%Y%m%d")
    return [(d - timedelta(days=b)).strftime("%Y%m%d") for b in range(1, max_days + 1)]


async def _fetch_fallback(api_key: str, search_date: str) -> tuple[list[dict], str, int]:
    """D-1..D-7 병렬 조회, 최근접 영업일 데이터 반환. 부수 결과도 sanity 저장소에 적재."""
    dates = _back_dates(search_date, FALLBACK_MAX_DAYS)
    results = await asyncio.gather(*(_fetch(api_key, dt) for dt in dates), return_exceptions=True)
    hit: tuple[list[dict], str, int] | None = None
    for back, (dt, res) in enumerate(zip(dates, results), start=1):
        if isinstance(res, list) and res:
            _store_rates(dt, res)
            if hit is None:
                hit = (res, dt, back)
    if hit is None:
        raise errors.FallbackExhausted(
            f"7일 이내 영업일 환율 데이터를 찾을 수 없습니다. 시작일: {search_date}"
        )
    return hit


def _store_rates(date: str, raw: list[dict]) -> None:
    parsed: dict[str, float] = {}
    for r in raw:
        try:
            parsed[r.get("cur_unit", "")] = _parse_numeric(r.get("deal_bas_r"))
        except (TypeError, ValueError):
            continue
    if parsed:
        _rates_by_date[date] = parsed


def _previous_day_rates(actual_date: str) -> dict[str, float] | None:
    """직전 영업일 환율 (세션 내 저장소 조회 전용 — 추가 API 호출 없음).

    fallback 병렬 조회 결과와 과거 날짜 조회 결과가 _rates_by_date에 적재되므로
    세션에서 이전 영업일을 본 적이 있으면 비교 가능. 없으면 sanity 검사 skip.
    """
    for dt in _back_dates(actual_date, SANITY_LOOKBACK_MAX_DAYS):
        if dt in _rates_by_date:
            return _rates_by_date[dt]
    return None


def _apply_sanity(rates: list[ExchangeRate], prev: dict[str, float] | None) -> bool:
    if not prev:
        return False
    triggered = False
    for r in rates:
        prev_val = prev.get(r.cur_unit)
        if prev_val and prev_val > 0:
            ratio = abs(r.deal_bas_r - prev_val) / prev_val
            if ratio > 0.20:
                r.sanity_warning = True
                triggered = True
    return triggered


def _cache_lookup(key: tuple[str, tuple[str, ...] | None]) -> dict | None:
    entry = _cache.get(key)
    if not entry:
        return None
    ts, payload = entry
    if time.time() - ts > CACHE_TTL_SECONDS:
        _cache.pop(key, None)
        return None
    return payload


def _cache_store(key: tuple[str, tuple[str, ...] | None], payload: dict) -> None:
    _cache[key] = (time.time(), payload)


def _clear_state_for_tests() -> None:
    _cache.clear()
    _rates_by_date.clear()


def _validate_inputs(search_date: str, today: str, target_currencies: list[str] | None) -> None:
    if len(search_date) != 8 or not search_date.isdigit():
        raise errors.InvalidDateFormat(
            f"search_date는 YYYYMMDD 8자리여야 합니다. 입력: {search_date}"
        )
    if search_date > today:
        raise errors.FutureDate(
            f"미래 날짜는 조회할 수 없습니다. 입력: {search_date}, 오늘: {today}"
        )
    if target_currencies:
        invalid = [c for c in target_currencies if c not in SUPPORTED_CURRENCIES]
        if invalid:
            raise errors.InvalidCurrency(
                f"지원하지 않는 통화 코드: {invalid[0]}. 부록 D 통화 코드 목록을 확인하세요."
            )


async def _build_payload(
    api_key: str,
    search_date: str,
    target_currencies: list[str] | None,
    fallback_to_previous: bool,
) -> dict:
    raw = await _fetch(api_key, search_date)
    actual_date = search_date
    fallback_used = False
    fallback_days = 0
    if not raw:
        if not fallback_to_previous:
            raise errors.NoDataForDate(
                "해당 날짜의 환율 데이터가 없습니다 (휴일/주말). fallback_to_previous=True로 재시도하세요."
            )
        raw, actual_date, fallback_days = await _fetch_fallback(api_key, search_date)
        fallback_used = True

    _store_rates(actual_date, raw)
    if target_currencies:
        wanted = set(target_currencies)
        raw = [r for r in raw if r.get("cur_unit") in wanted]

    rates = [_normalize_rate(r) for r in raw]
    _apply_sanity(rates, _previous_day_rates(actual_date))
    return {
        "search_date": search_date,
        "actual_date": actual_date,
        "rates": [r.model_dump() for r in rates],
        "fallback_used": fallback_used,
        "fallback_days_back": fallback_days,
    }


async def get_exchange_rates(
    search_date: str | None = None,
    target_currencies: list[str] | None = None,
    fallback_to_previous: bool = True,
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> ExchangeRatesResult:
    """Fetch deal-base exchange rates from Korea Eximbank."""
    api_key = config.get("EXCHANGE_RATE_API_KEY")
    if not api_key:
        raise errors.ApiKeyMissing("EXCHANGE_RATE_API_KEY가 .env에 설정되지 않았습니다.")

    today = _today_kst_yyyymmdd()
    if search_date is None:
        search_date = today
    _validate_inputs(search_date, today, target_currencies)

    key = (search_date, tuple(target_currencies) if target_currencies else None)
    cached_payload = _cache_lookup(key)
    cached = cached_payload is not None

    if cached_payload:
        payload = cached_payload
    else:
        payload = await _build_payload(
            api_key, search_date, target_currencies, fallback_to_previous
        )
        _cache_store(key, payload)

    rates_models = [ExchangeRate(**r) for r in payload["rates"]]
    data = ExchangeRatesData(
        search_date=payload["search_date"],
        actual_date=payload["actual_date"],
        rates=rates_models,
    )

    hints = ah.maybe_hints(
        render_format,
        artifact_type="rates_dashboard",
        title=f"{payload['actual_date']} 매매기준율 환율",
        preferred_chart="bar",
        columns_for_chart=["cur_unit", "deal_bas_r"],
        comparison_columns=["ttb", "deal_bas_r", "tts"],
    )

    return ExchangeRatesResult(
        data=data,
        metadata={
            "source": "koreaexim.go.kr",
            "data_type": "AP01",
            "fetched_at": datetime.now(KST).isoformat(),
            "cached": cached,
            "fallback_used": payload.get("fallback_used", False),
            "fallback_days_back": payload.get("fallback_days_back", 0),
        },
        render_format=render_format,
        artifact_hints=hints,
    )
