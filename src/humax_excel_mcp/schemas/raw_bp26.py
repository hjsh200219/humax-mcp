"""26BP Raw Transaction Sheet schema — US-022.

Maps row-3 header strings from the 26BP raw transaction sheet to canonical
English keys. Position-aware for duplicate '구분' headers.
"""

from __future__ import annotations

SCHEMA_VERSION = "2026.05-raw"
HEADER_ROW = 3  # 1-indexed; data starts at row 4

# Structure columns (mapping Korean header -> English key)
# NOTE: first '구분' occurrence (col 1) maps to 'division_type'.
#       Second occurrence at col 19 maps to 'expense_type' via position-aware logic.
STRUCTURE_COLUMNS: dict[str, str] = {
    "구분": "division_type",
    "Year": "year",
    "Month": "month",
    "Company\nCode": "company_code",
    "본사/법인": "head_or_corp",
    "Company": "company",
    "Posting Date": "posting_date",
    "Doc no.": "doc_no",  # PII — dropped before aggregation; included for schema completeness
    "Cost Center": "cost_center",
    "Cost Ctr Name": "cost_center_name",
    "대조직": "org_l1",
    "배부조직": "allocation_org",
    "보고용": "report_use",
    "보고용(re)": "report_use_re",
    "G/L Account": "gl_account",
    "소계정": "gl_account_name",
    "대계정": "gl_account_major",
    "대계정(re)": "gl_account_major_re",
    # NOTE: second "구분" -> "expense_type" via position-aware logic in normalize_headers
    "분류": "category",
}

VALUE_COLUMNS: dict[str, str] = {
    "통화\n(Doc)": "currency_doc",
    "Amount\n(Doc)": "amount_doc",
    "통화\n(KRW)": "currency_krw",
    "Amount\n(KRW)": "amount_krw",
}

TEXT_COLUMNS: dict[str, str] = {
    "Reversed\nwith": "reversed_with",  # audit trail, retained (NOT PII)
    "비고": "remark",
    "배부기준": "allocation_basis",
}

ALLOCATION_RATE_COLUMNS: dict[str, str] = {
    "STB\n(배부율)": "rate_stb",
    "Mobility\n(배부율)": "rate_mobility",
    "EVCS(국내)\n(배부율)": "rate_evcs_domestic",
    "EVCS(해외)\n(배부율)": "rate_evcs_overseas",
    "공통\n(배부율)": "rate_common",
    "건물\n(배부율)": "rate_building",
    "H.Mobility\n(배부율)": "rate_h_mobility",
    "H.EV\n(배부율)": "rate_h_ev",
    "하이파킹\n(배부율)": "rate_hiparking",
    "피플카\n(배부율)": "rate_peoplecar",
    "위너콤\n(배부율)": "rate_winnercom",
    "홀딩스\n(배부율)": "rate_holdings",
    "H.Networks\n(배부율)": "rate_h_networks",
    "TOTAL\n(배부율)": "rate_total",
}

# Intentionally NOT included in COLUMN_MAP (see rationale below).
# These exist at cols 46-59, 61-62 as bare-name strings ("STB", "Mobility", etc.).
# They are pre-computed allocation amounts that the aggregator does NOT consume.
# Excluding them from COLUMN_MAP avoids bare-name collision with rate columns.
ALLOCATION_AMOUNT_COLUMNS: dict[str, str] = {
    # Documented for reference only; not part of canonical mapping.
    # Keys here would collide with rate cols on bare-name normalization.
}

# COLUMN_MAP scope contract:
# Includes only columns the aggregator reads:
#   - structure (identity + grouping)
#   - value (amounts to sum)
#   - text (allocation_basis for filtering)
#   - allocation_rates (used for EVCS virtual row computation in US-024a)
# Excludes:
#   - ALLOCATION_AMOUNT_COLUMNS (aggregator recomputes via amount x rate / 100; no need to read them)
#   - PII columns (Text, Vendor Name, URL, Doc no. — dropped before COLUMN_MAP application)
#   - Marker cols ('▶'), col 63 (None)
COLUMN_MAP: dict[str, str] = {
    **STRUCTURE_COLUMNS,
    **VALUE_COLUMNS,
    **TEXT_COLUMNS,
    **ALLOCATION_RATE_COLUMNS,
}

# PII columns dropped before aggregation. `reversed_with` is retained for audit.
PII_COLUMNS: list[str] = ["Text", "Vendor\nName", "URL", "Doc no."]

REQUIRED_COLUMNS: list[str] = [
    "Year",
    "Month",
    "Company",
    "Cost Center",
    "G/L Account",
    "Amount\n(KRW)",
    "구분",  # division_type (예산/실적)
]

MONTH_MAP: dict[str, int] = {f"{m}월": m for m in range(1, 13)}

VALID_HUMAX_COMPANIES: list[str] = ["HKR", "HMX", "HUS", "HUK", "HBR", "HSZ"]


def normalize_headers(raw_headers: list[str]) -> list[str]:
    """Map raw row-3 header strings to canonical English keys.

    Position-aware: the duplicate '구분' at col 1 maps to 'division_type';
    the second occurrence at col 19 maps to 'expense_type'.
    Unknown headers pass through unchanged.
    """
    result: list[str] = []
    seen_gubun = 0
    for h in raw_headers:
        s = str(h) if h is not None else ""
        if s == "구분":
            seen_gubun += 1
            if seen_gubun == 1:
                result.append("division_type")
            else:
                result.append("expense_type")
        elif s in COLUMN_MAP:
            result.append(COLUMN_MAP[s])
        else:
            result.append(s)
    return result


def validate_headers(actual_headers: list[str]) -> list[str]:
    """Return diff list: 'MISSING:<key>' for required cols absent from canonical mapping.

    Only required (REQUIRED_COLUMNS) absence raises a diff. Extra columns are tolerated.
    """
    normalized = set(normalize_headers(actual_headers))
    expected_canonical_required = {COLUMN_MAP.get(req, req) for req in REQUIRED_COLUMNS}
    # '구분' is required; division_type covers it
    expected_canonical_required.discard("구분")
    expected_canonical_required.add("division_type")
    missing = expected_canonical_required - normalized
    return [f"MISSING:{m}" for m in sorted(missing)]
