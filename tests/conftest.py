"""Synthetic 26BP xlsx fixtures generated programmatically."""

from __future__ import annotations

import random
from pathlib import Path

import pandas as pd
import pytest
from openpyxl import Workbook

from humax_excel_mcp.schemas import bp26

COMPANIES = ["HMX", "HUS", "HUK", "HBR", "HSZ"]
DIVISIONS = ["사업부", "대조직", "중조직", "소조직"]
ACCOUNT_GROUPS = [
    ("511000", "급여", "인건비"),
    ("511100", "상여", "인건비"),
    ("521000", "복리후생", "인건비"),
    ("531000", "임차료", "경비"),
    ("541000", "감가상각비", "감가상각비"),
    ("551000", "지급수수료", "경비"),
]
ALLOC_BASES = ["경영지원부문", "공통영업", "기술지원", "전사공통"]


def _full_header_row() -> list[str]:
    headers: list[str] = list(bp26.STRUCTURE_COLUMNS.keys())
    for m in range(1, 13):
        headers.append(f"{m}월 예산")
        headers.append(f"{m}월 실적")
    for m in range(1, 13):
        headers.append(f"{m}월 누계 예산")
        headers.append(f"{m}월 누계 실적")
    headers.extend(["연간 예산", "연간 실적"])
    headers.extend(bp26.TEXT_COLUMNS.keys())
    headers.extend(bp26.ALLOCATION_RATE_COLUMNS.keys())
    return headers


def _allocate_rates() -> list[float]:
    seed = random.choice([
        [25.0, 25.0, 25.0, 25.0],
        [40.0, 10.0, 30.0, 20.0],
        [35.0, 0.0, 30.0, 35.0],
        [50.0, 20.0, 15.0, 15.0],
        [0.0, 100.0, 0.0, 0.0],
    ])
    return list(seed)


def _make_row(
    division: str,
    company: str,
    org_l1: str,
    org_l2: str,
    org_l3: str,
    cc: str,
    gl: tuple[str, str, str],
    rates: list[float],
    alloc_basis: str,
    *,
    rng: random.Random,
) -> list:
    code, name, _group = gl
    monthly: list[float] = []
    for _ in range(12):
        budget = float(rng.randint(50, 500) * 1000)
        actual = budget + float(rng.randint(-50, 50) * 1000)
        monthly.extend([budget, actual])
    cum_b = 0.0
    cum_a = 0.0
    cumulative: list[float] = []
    for i in range(12):
        cum_b += monthly[i * 2]
        cum_a += monthly[i * 2 + 1]
        cumulative.extend([cum_b, cum_a])
    annual = [cum_b, cum_a]
    row = [
        division,
        company,
        org_l1,
        org_l2,
        org_l3,
        cc,
        code,
        name,
        *monthly,
        *cumulative,
        *annual,
        f"{division} {org_l1} {name}",
        "",
        alloc_basis,
        *rates,
    ]
    return row


def _build_workbook(path: Path, *, seed: int = 42, rows_per_org: int = 2) -> Path:
    rng = random.Random(seed)
    wb = Workbook()
    ws = wb.active
    ws.title = "예산+실적"
    headers = _full_header_row()
    ws.append(headers)

    business_units = ["STB", "Mobility", "EVCS국내", "EVCS해외"]
    big_orgs = ["개발", "영업", "경영지원"]
    mid_orgs = ["SW개발", "HW개발", "플랫폼"]
    small_orgs = ["1팀", "2팀"]

    cc_counter = 100000
    detail_rows: list[list] = []
    for bu in business_units:
        for bo in big_orgs:
            for mo in mid_orgs:
                for so in small_orgs:
                    for _ in range(rows_per_org):
                        cc_counter += 1
                        gl = rng.choice(ACCOUNT_GROUPS)
                        rates = _allocate_rates()
                        company = rng.choice(COMPANIES)
                        row = _make_row(
                            "소조직",
                            company,
                            bo,
                            mo,
                            so,
                            str(cc_counter),
                            gl,
                            rates,
                            rng.choice(ALLOC_BASES),
                            rng=rng,
                        )
                        detail_rows.append(row)

    for r in detail_rows:
        ws.append(r)

    numeric_start = len(bp26.STRUCTURE_COLUMNS)
    numeric_end = numeric_start + 24 + 24 + 2

    grand_totals = [0.0] * (numeric_end - numeric_start)
    for r in detail_rows:
        for i in range(numeric_end - numeric_start):
            grand_totals[i] += float(r[numeric_start + i] or 0)

    total_row = [
        "총합계", "", "", "", "", "", "", "총합계",
        *grand_totals,
        "총합계", "", "",
        0.0, 0.0, 0.0, 0.0,
    ]
    ws.append(total_row)

    wb.save(path)
    return path


@pytest.fixture
def sample_26bp_path(tmp_path: Path) -> Path:
    p = tmp_path / "sample_26bp.xlsx"
    return _build_workbook(p, seed=42, rows_per_org=2)


@pytest.fixture
def prev_month_path(tmp_path: Path) -> Path:
    p = tmp_path / "sample_prev_month.xlsx"
    return _build_workbook(p, seed=41, rows_per_org=2)


@pytest.fixture
def curr_month_path(tmp_path: Path) -> Path:
    p = tmp_path / "sample_curr_month.xlsx"
    return _build_workbook(p, seed=42, rows_per_org=2)


@pytest.fixture
def empty_xlsx(tmp_path: Path) -> Path:
    p = tmp_path / "empty.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "예산+실적"
    ws.append(_full_header_row())
    wb.save(p)
    return p


@pytest.fixture
def synthetic_raw_26bp_df() -> pd.DataFrame:
    """Synthetic raw 26BP-shaped DataFrame: 3 months, 2 companies, 3 cost centers,
    2 gl accounts. Returns DataFrame in canonical normalized keys (post raw_bp26.normalize_headers).
    """
    import pandas as pd

    rows = []
    for company in ["HKR", "HMX"]:
        for cc in [101, 102, 103]:
            for gl in [510000, 520000]:
                for month_int, month_str in [(1, "1월"), (2, "2월"), (3, "3월")]:
                    for div in ["예산", "실적"]:
                        rows.append({
                            "division_type": div,
                            "year": "26년",
                            "month": month_str,
                            "company": company,
                            "cost_center": cc,
                            "cost_center_name": f"CC{cc}",
                            "gl_account": gl,
                            "gl_account_name": f"GL{gl}",
                            "org_l1": "사업그룹",
                            "amount_krw": 1000.0 * month_int * (2 if div == "예산" else 1),
                            "rate_stb": 25.0,
                            "rate_mobility": 25.0,
                            "rate_evcs_domestic": 30.0,
                            "rate_evcs_overseas": 20.0,
                        })
    return pd.DataFrame(rows)
