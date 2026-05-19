"""get_exchange_rates tool — PRD §4.8. Korea Eximbank API."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import httpx

from .. import config
from ..core import artifact_hints as ah
from ..core import errors
from ..schemas.responses import ExchangeRate, ExchangeRatesData, ExchangeRatesResult

API_URL = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"
TIMEOUT_SECONDS = 10.0
CACHE_TTL_SECONDS = 12 * 3600
FALLBACK_MAX_DAYS = 7

KST = timezone(timedelta(hours=9))

UNIT_100_CURRENCIES = {"JPY(100)", "IDR(100)"}

SUPPORTED_CURRENCIES = {
    "USD", "EUR", "JPY(100)", "CNH", "GBP", "HKD", "CHF", "CAD", "AUD", "SGD",
    "THB", "SEK", "NZD", "BRL", "IDR(100)",
}

_cache: dict[tuple[str, tuple[str, ...] | None], tuple[float, dict]] = {}
_prev_day_cache: dict[str, dict[str, float]] = {}


def _today_kst_yyyymmdd() -> str:
    return datetime.now(KST).strftime("%Y%m%d")


def _parse_numeric(value: Any) -> float:
    if value is None:
        raise ValueError("None")
    if isinstance(value, (int, float)):
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


def _fetch(api_key: str, date: str) -> list[dict]:
    params = {"authkey": api_key, "searchdate": date, "data": "AP01"}
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            resp = client.get(API_URL, params=params)
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


def _apply_sanity(rates: list[ExchangeRate], date: str) -> bool:
    prev = _prev_day_cache.get(date)
    if not prev:
        for r in rates:
            _prev_day_cache.setdefault(date, {})[r.cur_unit] = r.deal_bas_r
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


def _clear_state_for_tests() -> None:
    _cache.clear()
    _prev_day_cache.clear()


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

    key = (search_date, tuple(target_currencies) if target_currencies else None)
    cached_payload = _cache_lookup(key)
    cached = cached_payload is not None

    if cached_payload:
        payload = cached_payload
    else:
        raw = _fetch(api_key, search_date)
        actual_date = search_date
        fallback_used = False
        fallback_days = 0
        if not raw:
            if not fallback_to_previous:
                raise errors.NoDataForDate(
                    "해당 날짜의 환율 데이터가 없습니다 (휴일/주말). fallback_to_previous=True로 재시도하세요."
                )
            d = datetime.strptime(search_date, "%Y%m%d")
            for back in range(1, FALLBACK_MAX_DAYS + 1):
                d_try = d - timedelta(days=back)
                raw_try = _fetch(api_key, d_try.strftime("%Y%m%d"))
                if raw_try:
                    raw = raw_try
                    actual_date = d_try.strftime("%Y%m%d")
                    fallback_used = True
                    fallback_days = back
                    break
            if not raw:
                raise errors.FallbackExhausted(
                    f"7일 이내 영업일 환율 데이터를 찾을 수 없습니다. 시작일: {search_date}"
                )

        if target_currencies:
            wanted = set(target_currencies)
            raw = [r for r in raw if r.get("cur_unit") in wanted]

        rates = [_normalize_rate(r) for r in raw]
        _apply_sanity(rates, actual_date)
        payload = {
            "search_date": search_date,
            "actual_date": actual_date,
            "rates": [r.model_dump() for r in rates],
            "fallback_used": fallback_used,
            "fallback_days_back": fallback_days,
        }
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
