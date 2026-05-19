"""26BP `예산+실적` 시트 63컬럼 매핑 + 스키마 버전."""

from __future__ import annotations

SCHEMA_VERSION = "2026.05"

CHANGELOG: dict[str, str] = {
    "2026.05": "Initial v0.1 — 8 structure + 48 monthly + 2 annual + 3 text + 4 allocation = 65 cols",
}

VALID_COMPANIES: list[str] = ["HMX", "HUS", "HUK", "HBR", "HSZ"]

VALID_DIVISIONS: list[str] = ["총합계", "사업부", "대조직", "중조직", "소조직"]

VALID_ORG_LEVELS: list[str] = ["총합계", "사업부", "대조직", "중조직", "소조직", "본사"]

VALID_ACCOUNT_GROUPS: list[str] = ["인건비", "경비", "감가상각비", "기타"]


def _monthly_columns() -> dict[str, str]:
    cols: dict[str, str] = {}
    for m in range(1, 13):
        cols[f"{m}월 예산"] = f"m{m:02d}_budget"
        cols[f"{m}월 실적"] = f"m{m:02d}_actual"
    for m in range(1, 13):
        cols[f"{m}월 누계 예산"] = f"cum{m:02d}_budget"
        cols[f"{m}월 누계 실적"] = f"cum{m:02d}_actual"
    cols["연간 예산"] = "annual_budget"
    cols["연간 실적"] = "annual_actual"
    return cols


STRUCTURE_COLUMNS: dict[str, str] = {
    "구분": "division",
    "Company": "company",
    "대조직": "org_l1",
    "중조직": "org_l2",
    "소조직": "org_l3",
    "Cost Center": "cost_center",
    "G/L Account": "gl_account",
    "G/L Account Name": "gl_account_name",
}

TEXT_COLUMNS: dict[str, str] = {
    "Text(적요)": "text_summary",
    "비고": "remark",
    "배부기준": "allocation_basis",
}

ALLOCATION_RATE_COLUMNS: dict[str, str] = {
    "STB 배부율": "STB",
    "Mobility 배부율": "Mobility",
    "EVCS국내 배부율": "EVCS_domestic",
    "EVCS해외 배부율": "EVCS_overseas",
}

COLUMN_MAP: dict[str, str] = {
    **STRUCTURE_COLUMNS,
    **_monthly_columns(),
    **TEXT_COLUMNS,
}

ALLOCATION_RATE_KEYS = list(ALLOCATION_RATE_COLUMNS.values())

DEFAULT_COLUMNS: list[str] = [
    "division",
    "company",
    "org_l1",
    "org_l2",
    "org_l3",
    "cost_center",
    "gl_account",
    "gl_account_name",
    "m01_budget", "m01_actual",
    "m02_budget", "m02_actual",
    "m03_budget", "m03_actual",
    "cum03_budget", "cum03_actual",
    "annual_budget", "annual_actual",
    "text_summary",
    "remark",
    "allocation_basis",
]


def validate_headers(actual_headers: list[str]) -> list[str]:
    """Return list of header diffs vs schema. Empty list = match.

    Each diff: 'MISSING:<expected>' or 'UNKNOWN:<actual>'.
    """
    expected = set(COLUMN_MAP.keys()) | set(ALLOCATION_RATE_COLUMNS.keys())
    actual = {h for h in actual_headers if h}
    diffs: list[str] = []
    for h in sorted(expected - actual):
        diffs.append(f"MISSING:{h}")
    for h in sorted(actual - expected):
        diffs.append(f"UNKNOWN:{h}")
    return diffs


def normalize_headers(actual_headers: list[str]) -> list[str]:
    """Map raw header names to canonical keys; unknown headers pass through unchanged."""
    out: list[str] = []
    for h in actual_headers:
        if h in COLUMN_MAP:
            out.append(COLUMN_MAP[h])
        elif h in ALLOCATION_RATE_COLUMNS:
            out.append(ALLOCATION_RATE_COLUMNS[h])
        else:
            out.append(h or "")
    return out
