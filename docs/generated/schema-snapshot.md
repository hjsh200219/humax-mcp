# schema-snapshot.md (auto-generated context)

> bp26 / raw_bp26 스키마 스냅샷. 코드 변경 시 `python scripts/verify_docs.py`로 동기화 검증.

## bp26 (aggregated `예산+실적` 시트)

- `SCHEMA_VERSION = "2026.05"`
- 63컬럼 (8 structure + 48 monthly + 2 annual + 3 text + 4 allocation) = 65
- 헤더 row 1

### STRUCTURE_COLUMNS (8)

| Korean | English key |
|---|---|
| 구분 | division |
| Company | company |
| 대조직 | org_l1 |
| 중조직 | org_l2 |
| 소조직 | org_l3 |
| Cost Center | cost_center |
| G/L Account | gl_account |
| G/L Account Name | gl_account_name |

### Monthly (월 1-12)

- `{m}월 예산` → `m{m:02d}_budget` (12)
- `{m}월 실적` → `m{m:02d}_actual` (12)
- `{m}월 누계 예산` → `cum{m:02d}_budget` (12)
- `{m}월 누계 실적` → `cum{m:02d}_actual` (12)
- `연간 예산` → `annual_budget`
- `연간 실적` → `annual_actual`

### TEXT_COLUMNS (3)

| Korean | English key |
|---|---|
| Text(적요) | text_summary |
| 비고 | remark |
| 배부기준 | allocation_basis |

### ALLOCATION_RATE_COLUMNS (4)

| Korean | English key |
|---|---|
| STB 배부율 | STB |
| Mobility 배부율 | Mobility |
| EVCS국내 배부율 | EVCS_domestic |
| EVCS해외 배부율 | EVCS_overseas |

### Valid Values

- `VALID_COMPANIES = ["HMX", "HUS", "HUK", "HBR", "HSZ"]`
- `VALID_DIVISIONS = ["총합계", "사업부", "대조직", "중조직", "소조직"]`
- `VALID_ORG_LEVELS = ["총합계", "사업부", "대조직", "중조직", "소조직", "본사"]`
- `VALID_ACCOUNT_GROUPS = ["인건비", "경비", "감가상각비", "기타"]`

## raw_bp26 (raw transaction 시트)

- `SCHEMA_VERSION = "2026.05-raw"`
- 헤더 row 3 (1-indexed, 데이터 row 4부터)

### STRUCTURE_COLUMNS (19)

division_type, year, month, company_code, head_or_corp, company, posting_date, doc_no, cost_center, cost_center_name, org_l1, allocation_org, report_use, report_use_re, gl_account, gl_account_name, gl_account_major, gl_account_major_re, category

(position-aware: 첫 `구분` → `division_type`, 두 번째 `구분` → `expense_type`)

### VALUE_COLUMNS (4)

currency_doc, amount_doc, currency_krw, amount_krw

### TEXT_COLUMNS (3)

reversed_with, remark, allocation_basis

### ALLOCATION_RATE_COLUMNS (14)

rate_stb, rate_mobility, rate_evcs_domestic, rate_evcs_overseas, rate_common, rate_building, rate_h_mobility, rate_h_ev, rate_hiparking, rate_peoplecar, rate_winnercom, rate_holdings, rate_h_networks, rate_total

### PII_COLUMNS (제거 대상)

`["Text", "Vendor\nName", "URL", "Doc no."]` — aggregator 진입 전 drop

### REQUIRED_COLUMNS

Year, Month, Company, Cost Center, G/L Account, Amount(KRW), 구분

### VALID_HUMAX_COMPANIES

`["HKR", "HMX", "HUS", "HUK", "HBR", "HSZ"]`

## 검증 명령

```bash
python -c "from humax_excel_mcp.schemas import bp26, raw_bp26; print(bp26.SCHEMA_VERSION, raw_bp26.SCHEMA_VERSION)"
# → 2026.05 2026.05-raw

python scripts/verify_docs.py
# → schema version 일치 + 도구 수 일치 검증
```
