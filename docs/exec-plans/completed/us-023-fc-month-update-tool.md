# US-023: `update_fc_month_report` — FC 실적 보고서 당월 배부판 자동 생성

> 상태: 구현 완료 (2026-06-26). `src/humax_excel_mcp/core/fc_report_layout.py`,
> `src/humax_excel_mcp/tools/fc_month_update.py`로 포팅 완료, `tests/unit/test_fc_month_update.py`
> 단위 테스트 통과. §2.5/§2.8 오케스트레이션 순서는 구현 시 일부 정리됨(백업 전에 시트 존재/구조
> 검증을 선행해 불필요한 백업 생성을 방지) — 동작/에러코드/필드는 본 문서 스펙과 동일.
> 작성 배경: 2026-06-26 세션에서 "raw data + 전월 양식(배부판)" 2개 파일로 5월 배부판을 생성하는
> 작업을 수행하며 기존 스킬(`build_fc_report.py`)의 누락 로직(`{월}(AC)` 시트 미처리)을 발견·수정·
> 실데이터로 교차검증했다. 이 문서는 그 작업을 **표준 절차**로 일반화하고, humax-excel-mcp의
> 11번째 도구로 포팅하기 위한 실행 스펙이다. `docs/prd/mcp-design-plan.md` §4 형식을 따른다.

## 0. 사용자 시나리오 (트리거)

사용자가 다음 2개 파일을 주면서 "당월 배부판 생성해줘" 라고 요청하는 경우:

1. **raw data**: `26BP+{월} 누계 실적({날짜}) HEV합산ver..xlsx`
2. **전월 양식**: `(보고) Humax FC 실적 ({연도}.{전월})_{날짜}.xlsx` — 1월부터 월별 단독 시트
   (`{월}(AC)`, `{월}(BP)` 등)가 미리 다 만들어져 있는 구조. **대상월의 `{월}(AC)` 시트가 이미
   템플릿 안에 존재해야 한다** (스켈레톤만 있고 비어 있는 상태, hidden).

기대 출력: `(보고) Humax FC 실적 ({연도}.{당월})_{날짜}.xlsx` 한 개 파일, 다음이 모두 완료된 상태:

- `{당월}(AC)` 시트: 예산/실적 채워지고 시트 숨김 해제
- `{당월} 누계(AC)` 시트: 신규 생성, 1월~당월 수식 체인
- `{당월} 누계(상세)` 시트: 신규 생성, 값 + 비고 코멘트
- 전월 누계 시트 2개(`{전월} 누계(AC)`, `{전월} 누계(상세)`) 숨김 처리
- 누계(상세) 총합계와 누계(AC) 마지막 Diff 테이블 총합계 일치 검증

## 1. 표준 워크플로우 (절차 정의)

이전까지 "당월 배부판 생성"은 `{월} 누계(AC)`/`{월} 누계(상세)` 확장만 하면 되는 줄 알았으나,
**`{월}(AC)` 개별월 시트 자체를 채우는 단계가 항상 선행되어야 한다**는 것이 이번 세션에서
확인된 핵심 교정 사항이다. 전체 7단계:

| # | 단계 | 대상 시트 | 방식 |
|---|---|---|---|
| 1 | `{당월}(AC)` 누락 수식 복원 | `{당월}(AC)` | `{전월}(AC)`에서 수식 문자열 복사 + 월 치환 |
| 2 | `{당월}(AC)` 실적 데이터 채우기 | `{당월}(AC)` | raw "실적" 행을 대조직×세그먼트로 집계해 leaf row에 기입 |
| 3 | `{당월}(AC)` 숨김 해제 | `{당월}(AC)` | `sheet_state = "visible"` |
| 4 | `{당월} 누계(AC)` 생성 | 신규 시트 | `{전월} 누계(AC)` 복사 + 수식 체인 1항 확장 |
| 5 | `{당월} 누계(상세)` 생성 | 신규 시트 | `{전월} 누계(상세)` 복사 + raw 1월~당월 집계값/코멘트 기입 |
| 6 | 전월 누계 시트 2개 숨김 | `{전월} 누계(AC/상세)` | `sheet_state = "hidden"` |
| 7 | 교차검증 | - | 누계(상세) 총합계 vs 누계(AC) Diff 총합계 vs raw 직접합 3-way 비교 |

## 2. 신규 도구: `update_fc_month_report`

### 2.1 함수 시그니처

```python
# src/humax_excel_mcp/tools/fc_month_update.py
async def update_fc_month_report(
    raw_path: str,
    template_path: str,
    month: str,                      # 예: "5월"
    *,
    output_path: str | None = None,
    dry_run: bool = False,
    cross_validate_tolerance: float = 10.0,   # KRW. 이 이내 오차는 통과
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> FcMonthUpdateResult:
    ...
```

등록 시 `audited("update_fc_month_report", file_path_arg="template_path")` — 1차 파일 기준은
template_path (수정 대상 보고서), `write_cells`/`apply_golden_template`과 동일한 관례.

### 2.2 입력 파라미터

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `raw_path` | str | `26BP+{월} 누계 실적 HEV합산ver.xlsx` 경로. "예산+실적" 시트 필요 |
| `template_path` | str | 전월 FC 보고서 경로. `{전월}(AC)`, `{당월}(AC)`(스켈레톤), `{전월} 누계(AC)`, `{전월} 누계(상세)` 4개 시트 모두 존재해야 함 |
| `month` | str | `"N월"` 형식, N=2~12 (1월은 누계 체인 시작점이라 본 도구 대상 아님) |
| `output_path` | str\|None | 기본값 `{template_stem}_{month}{suffix}`. template_path와 동일 금지 |
| `dry_run` | bool | True면 파일 저장/백업 없이 집계·검증 결과만 반환 |
| `cross_validate_tolerance` | float | 3-way 교차검증 허용 오차(원). 초과 시 `VerificationFailed` |

### 2.3 사전조건 (검증 후 즉시 raise)

- `raw_path`, `template_path` 둘 다 `.xlsx` 존재 → 아니면 `errors.FileNotFound`
- `month` 정규식 `^\d{1,2}월$` 불일치 또는 N==1 → `errors.InvalidMonth`
- `output_path.resolve() == template_path.resolve()` → `errors.OverwriteOriginalForbidden`
- `out.parent` 미존재 → `errors.WritePermissionDenied`
- `wb`에 `{당월}(AC)` 또는 `{전월}(AC)` 시트 없음 → `errors.SheetNotFound` (메시지에 "대상월 스켈레톤 시트가 템플릿에 미리 존재해야 함" 안내 포함)
- `{당월} 누계(AC)` 또는 `{당월} 누계(상세)`가 **이미** `wb.sheetnames`에 존재 → `errors.StructureMismatch`
  ("이미 생성된 보고서를 입력한 것으로 보입니다")
- raw에서 `구분=="실적" and Month==month` 행이 0건 → `errors.EmptyResult`

### 2.4 핵심 매핑 상수

신규 모듈 `src/humax_excel_mcp/core/fc_report_layout.py`에 모아서 단일 소스로 관리 (TD-005와
동일한 취지 — 향후 #9/#10 고정비 도구에서도 일부 재사용 가능):

```python
"""FC 실적 보고서 ({월}(AC), {월} 누계(상세)) 시트의 고정 레이아웃 상수.
실데이터 기준 검증일: 2026-06-26 (4월->5월 업데이트). 원본 양식이 바뀌면 이 파일만 갱신."""

# ---- "{월}(AC)" 시트: BP(2-29)/실적(32-59)/Diff(62-89) 3블록, 블록 간 +30 오프셋 ----
# 대조직(raw col10, '대조직') -> 실적 블록 leaf row 번호
ALIAS_TO_ROW = {
    '사업 그룹': 37, '개발 그룹': 38, 'SCM실': 39, 'Media그룹': 40,
    'CEO': 42, 'Staff(CEO)': 43, '경영지원실': 44, 'HR실': 45,
    'HUS': 47, 'HMX': 48, 'HUK': 49, 'HDG': 50, 'HUG': 51, 'HTR': 52,
    'HBR': 53, 'HJP': 54, 'HTH': 55, 'HAU': 56, 'HID': 57, 'HSZ': 58,
}
LEAF_ROWS = list(ALIAS_TO_ROW.values())

# AC 시트 세그먼트 열 -> raw "예산+실적" 시트 0-based 컬럼 인덱스
SEG_RAW_IDX = {
    'J': 45, 'K': 46, 'L': 47, 'M': 48, 'N': 49, 'O': 50,
    'Q': 51, 'R': 52, 'S': 53, 'T': 54, 'U': 55, 'V': 56, 'W': 57,
}
# 주의: P열은 항상 '=SUM(Q:W)' 기존 수식이라 직접 쓰지 않음. F/G/H/I는 합계행 수식 영역.

RAW_COL_GUBUN = 0          # '예산'/'실적'
RAW_COL_MONTH = 2          # '1월'~'12월'
RAW_COL_HQCORP = 4         # 본사/법인 (라벨 중복 이슈 있어 누계(상세) 집계는 COL_COMPANY 사용)
RAW_COL_COMPANY = 5        # 본사/법인 판정용 신뢰 컬럼 (HKR=본사, 그 외=법인)
RAW_COL_ORG = 10           # '대조직' — ALIAS_TO_ROW 키
RAW_COL_DAEGYEJEONG_RE = 17
RAW_COL_AMOUNT_KRW = 23    # 권위있는 금액 필드 (col21 Amount(Doc)는 사용하지 않음)

# ---- "{월} 누계(상세)" 시트: 대계정 카테고리 x 본사/법인 x 사업부 ----
CAT_MAP = {
    '11 급여': '인건비', '53 4대보험료': '인건비', '13 퇴직급여': '인건비',
    '16 여비교통비': '여비교통비',
    '29 지급수수료': '지급수수료', '40 외주개발용역비': '지급수수료',
    '41 인증대행료': '지급수수료', '42 특허처리비': '지급수수료',
    '23 감가상각비': '감가상각비',
    '47 광고선전비': '광고선전비',
}  # 매핑 없는 대계정(re)는 전부 '기타'. 14 복리후생비/15 교육훈련비는 기타 (인건비 아님 — 검증 시 발견된 실수 주의)
CATS = ['인건비', '여비교통비', '감가상각비', '지급수수료', '광고선전비', '기타']
ROWS_HQ = {c: 5 + i for i, c in enumerate(CATS)}     # 본사: 행 5~10
ROWS_CORP = {c: 12 + i for i, c in enumerate(CATS)}  # 법인: 행 12~17
SEG_BLOCK_COLS = {       # 사업부 -> (예산열, 실적열, 비고열)
    '총합계': ('C', 'D', 'G'), 'STB': ('H', 'I', 'L'), 'Mobility': ('M', 'N', 'Q'),
    'EVCS': ('R', 'S', 'V'), '공통': ('W', 'X', 'AA'), '건물': ('AB', 'AC', 'AF'),
    'Shared': ('AG', 'AH', 'AK'),
}
SEG_COLS_RAW = {  # 누계(상세) 집계용 — AC 시트와 다른 축(사업부 단위가 더 굵음)
    'STB': 45, 'Mobility': 46, 'EVCS_in': 47, 'EVCS_out': 48, '공통': 49, '건물': 50, 'Shared': 61,
}
COMMENT_THRESHOLD = 9_000_000   # 이 금액(원) 이상 차이 블록만 코멘트
COMMENT_ITEM_MIN = 5_000_000
COMMENT_TOPN = 3
```

### 2.5 동작 단계 (구현 순서)

1. 입력 검증 (§2.3)
2. `excel_io.assert_xlsx_path` ×2, `out` 경로 확정
3. raw 집계 — 대조직×세그먼트 (`_aggregate_org_actuals`, §3.1) → `sums`, `total_check`, `unmatched`
   - `unmatched`(DUMMY 제외하고 금액 != 0인 항목)이 있으면 결과의 `warnings`에 포함 (하드 실패 아님 — 신규 조직코드 대응)
4. `dry_run`이 아니면 `backup_mod.create_backup(Path(template_path))`
5. `excel_io.load_workbook_safe(template_path, data_only=False)`로 로드
6. `{당월}(AC)`/`{전월}(AC)` 시트 획득 (`excel_io.get_sheet`, 없으면 `SheetNotFound`)
7. `_restore_ac_formulas(ws_cur, ws_ref, month, prev_month)` (§3.1) → `restored` 개수
8. `_fill_ac_actuals(ws_cur, sums)` (§3.1) → `written` 개수 (항상 `len(LEAF_ROWS) * 13 = 260`)
9. `ws_cur.sheet_state = "visible"`
10. raw 1월~당월 전체를 pandas로 로드 (`_load_raw_df`, §3.2) → `totals`, `diffs` (대계정×본사법인 축)
11. `_build_cumulative_ac_sheet(wb, prev_month, month)` (§3.2, `build_ac_sheet` 그대로 포팅) — 신규 시트명 중복 시 사전에 §2.3에서 이미 막힘
12. `_build_cumulative_detail_sheet(wb, prev_month, month, totals, diffs)` (§3.2, `build_detail_sheet` 포팅)
13. `_reposition(wb, prev_month, month, "누계(AC)")`, 동일하게 `"누계(상세)"` — 전월 시트 바로 뒤로 이동 + 전월 시트는 두 함수 내부에서 이미 `hidden` 처리됨
14. `_cross_validate(wb, sums, month)` (§2.8) → `(raw_total, derived_cumulative_total, detail_grand_total, diff)`
    - `abs(diff) > cross_validate_tolerance` → `errors.VerificationFailed` (저장 전에 발생시켜 잘못된 파일이 나가지 않게 함)
15. `dry_run`이 아니면 `wb.save(out)`
16. 저장 후 재로드 검증: `{당월}(AC).sheet_state == "visible"`, leaf 셀 샘플 일치, 신규 누계 시트 존재, 전월 누계 시트 `hidden` — 불일치 시 `errors.VerificationFailed`
17. `FcMonthUpdateResult` 빌드 + `artifact_hints.maybe_hints(render_format, artifact_type="verification_result", title=f"{month} 배부판 생성 결과")`

### 2.6 반환 데이터 구조 (Pydantic — `schemas/responses.py`에 추가)

```python
class FcMonthAcSummary(BaseModel):
    model_config = ConfigDict(extra="allow")
    sheet: str                       # "{월}(AC)"
    formulas_restored: int
    cells_written: int
    unmatched_orgs: dict[str, float] # 보통 {} (DUMMY는 항상 0이라 사전 제외)
    raw_actual_total: float          # 해당월 raw "실적" Amount(KRW) 총합

class FcMonthCumulativeSummary(BaseModel):
    model_config = ConfigDict(extra="allow")
    ac_sheet_created: str            # "{월} 누계(AC)"
    detail_sheet_created: str        # "{월} 누계(상세)"
    prev_sheets_hidden: list[str]    # ["{전월} 누계(AC)", "{전월} 누계(상세)"]
    formula_chain_extended: int      # build_ac_sheet에서 확장된 수식 셀 수

class FcMonthVerification(BaseModel):
    model_config = ConfigDict(extra="allow")
    verified: bool
    raw_direct_total: float
    derived_cumulative_total: float
    detail_grand_total: float
    diff: float
    tolerance: float

class FcMonthUpdateResult(BaseResult):
    dry_run: bool
    month: str
    prev_month: str
    output_path: str | None
    backup_path: str | None
    ac_summary: FcMonthAcSummary
    cumulative_summary: FcMonthCumulativeSummary
    verification: FcMonthVerification
    warnings: list[str] = Field(default_factory=list)
```

### 2.7 에러 케이스

| 조건 | 에러 |
|---|---|
| raw/template 파일 없음 또는 xlsx 아님 | `FileNotFound` |
| month 형식/범위 오류 | `InvalidMonth` |
| output_path == template_path | `OverwriteOriginalForbidden` |
| output 디렉터리 없음 | `WritePermissionDenied` |
| `{당월}(AC)`/`{전월}(AC)` 시트 없음 | `SheetNotFound` |
| 누계 시트가 이미 존재 (재실행 의심) | `StructureMismatch` |
| raw에 대상월 실적 행 0건 | `EmptyResult` |
| 백업 실패 | `BackupFailed` (`create_backup` 내부에서 발생) |
| 3-way 교차검증 오차 > tolerance | `VerificationFailed` |
| 저장 후 재검증 불일치 | `VerificationFailed` |

### 2.8 교차검증 로직 (3-way)

이번 세션에서 실데이터로 확인한 방식 — 같은 raw 금액을 서로 다른 두 축(조직×세그먼트 vs
대계정×본사법인)으로 분해한 값이므로 거의 정확히 일치해야 함 (검증 시 1-2원 이내):

```python
def _cross_validate(wb, sums_target, month, months_all):
    """1월~당월 실적 누계를 AC 시트 leaf-row 직접합으로 재계산 → 누계(상세) 총합계와 비교."""
    total = 0.0
    for m in months_all[:-1]:  # 1월~전월: 이미 리터럴 값으로 채워져 있음 (각 월이 "당월"이었을 때 본 도구로 채워짐)
        ws = wb[f"{m}(AC)"]
        for r in LEAF_ROWS:
            for col in SEG_RAW_IDX:
                total += float(ws.cell(r, column_index_from_string(col)).value or 0)
    for r in LEAF_ROWS:               # 당월: 방금 집계한 sums 사용 (시트엔 썼지만 재로드 안 해도 됨)
        for col in SEG_RAW_IDX:
            total += sums_target.get(r, {}).get(col, 0.0)

    detail_ws = wb[f"{month} 누계(상세)"]
    grand_total_actual = sum(
        detail_ws[f"D{r}"].value or 0
        for r in (list(ROWS_HQ.values()) + list(ROWS_CORP.values()))
    )  # D열 = 실적(총합계 블록)
    return total, grand_total_actual, total - grand_total_actual
```

## 3. 참고 구현 (이번 세션에 실데이터로 검증된 코드)

### 3.1 `{월}(AC)` 시트 채우기 — `/tmp/fix_ac_sheet.py` (그대로 포팅 대상)

> 4월→5월 실데이터 검증 결과: raw 실적 총합 2,621,136,854원, 미매칭 조직 DUMMY(항상 0원)만 존재,
> 수식 285개 복원, 셀 260개 기입. 이 로직을 `tools/fc_month_update.py`의 `_restore_ac_formulas` /
> `_aggregate_org_actuals` / `_fill_ac_actuals`로 그대로 옮기면 됨 (함수 시그니처 동일, import만
> `core.fc_report_layout`의 상수로 교체).

```python
from collections import defaultdict
from openpyxl.utils import column_index_from_string
from ..core.fc_report_layout import ALIAS_TO_ROW, SEG_RAW_IDX, LEAF_ROWS


def _aggregate_org_actuals(raw_path: str, month: str):
    """raw '예산+실적' 시트에서 month의 '실적' 행만 대조직x세그먼트로 집계."""
    from openpyxl import load_workbook
    wb = load_workbook(raw_path, data_only=True, read_only=True)
    ws = wb['예산+실적']
    sums: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    total_check = 0.0
    unmatched: dict[str, float] = defaultdict(float)
    for row in ws.iter_rows(min_row=4, values_only=True):
        if row[0] != '실적':
            continue
        if str(row[2]).strip() != month:
            continue
        org = str(row[10]).strip()
        amt = float(row[23] or 0)
        total_check += amt
        if org not in ALIAS_TO_ROW:
            unmatched[org] += amt
            continue
        r = ALIAS_TO_ROW[org]
        for col, idx in SEG_RAW_IDX.items():
            sums[r][col] += float(row[idx] or 0)
    wb.close()
    return sums, total_check, dict(unmatched)


def _restore_ac_formulas(ws_cur, ws_ref, month: str, prev_month: str) -> int:
    """{전월}(AC) 시트의 수식 문자열을 {당월}(AC)의 빈 셀에 복사 (월 문자열만 치환).
    템플릿이 매월 일관되게 누락시키는 BP블록 leaf row 수식 + 집계행 SUM 수식을 복원."""
    needle = "'%s(BP)'" % prev_month
    repl = "'%s(BP)'" % month
    restored = 0
    for r in range(1, 91):       # 3블록(BP/실적/Diff) 전체 = 행 1~90
        for c in range(1, 26):   # A~Y열
            rv = ws_ref.cell(r, c).value
            cv = ws_cur.cell(r, c).value
            if isinstance(rv, str) and rv.startswith('=') and cv is None:
                ws_cur.cell(r, c).value = rv.replace(needle, repl)
                restored += 1
    return restored


def _fill_ac_actuals(ws, sums: dict[int, dict[str, float]]) -> int:
    """실적 블록 leaf row(20개) x 세그먼트열(13개) = 260셀 기입."""
    written = 0
    for r in LEAF_ROWS:
        for col in SEG_RAW_IDX:
            v = sums.get(r, {}).get(col, 0.0)
            ws.cell(r, column_index_from_string(col)).value = round(v, 2)
            written += 1
    return written
```

### 3.2 누계(AC)/누계(상세) 생성 — `build_fc_report.py` 핵심 함수 (기존 검증됨, 변경 불필요)

> 원본: `humax-monthly-report` 스킬의 `scripts/build_fc_report.py`. 이미 4월 업데이트 작업에서
> 기존 보고서 수치와 24/24 정확히 일치하도록 검증됨 (스크립트 내 주석 참고). 로직 변경 없이
> `tools/fc_month_update.py`로 그대로 옮기고, 상단 상수(`CAT_MAP`/`CATS`/`SEG_COLS_RAW`/
> `ROWS_HQ`/`ROWS_CORP`/`SEG_BLOCK_COLS`/`COMMENT_*`)는 `core/fc_report_layout.py`에서 import.

```python
import pandas as pd
from ..core.fc_report_layout import (
    CAT_MAP, CATS, ROWS_HQ, ROWS_CORP, SEG_BLOCK_COLS, SEG_COLS_RAW,
    COMMENT_THRESHOLD, COMMENT_ITEM_MIN, COMMENT_TOPN,
    RAW_COL_GUBUN, RAW_COL_MONTH, RAW_COL_COMPANY, RAW_COL_DAEGYEJEONG_RE,
)

SEGS = ['STB', 'Mobility', 'EVCS', '공통', '건물', 'Shared']


def _month_range(month: str) -> list[str]:
    n = int(month.replace("월", ""))
    return [f"{i}월" for i in range(1, n + 1)]


def _load_raw_df(raw_path: str, months: list[str]) -> pd.DataFrame:
    import openpyxl
    wb = openpyxl.load_workbook(raw_path, data_only=True, read_only=True)
    ws = wb["예산+실적"]
    records = []
    for row in ws.iter_rows(min_row=4, values_only=True):
        if row[RAW_COL_GUBUN] not in ('예산', '실적'):
            continue
        if str(row[RAW_COL_MONTH]).strip() not in months:
            continue
        rec = {
            'gubun': row[RAW_COL_GUBUN], 'month': row[RAW_COL_MONTH],
            'company': row[RAW_COL_COMPANY],
            'daegyejeong_re': str(row[RAW_COL_DAEGYEJEONG_RE]).strip() if row[RAW_COL_DAEGYEJEONG_RE] else None,
        }
        for name, idx in SEG_COLS_RAW.items():
            rec[name] = row[idx] or 0
        records.append(rec)
    wb.close()
    df = pd.DataFrame(records)
    df['EVCS'] = df['EVCS_in'] + df['EVCS_out']
    df['hb2'] = df['company'].apply(lambda c: '본사' if c == 'HKR' else '법인')
    df['category'] = df['daegyejeong_re'].map(CAT_MAP).fillna('기타')
    return df


def _compute_totals(df: pd.DataFrame) -> dict:
    results = {}
    for hb in ['본사', '법인']:
        for gubun in ['예산', '실적']:
            for cat in CATS:
                sub = df[(df.hb2 == hb) & (df.gubun == gubun) & (df.category == cat)]
                s = sub[SEGS].sum()
                results[(cat, hb, gubun)] = {'총합계': float(s.sum()), **{k: float(s[k]) for k in SEGS}}
    return results


def _compute_account_diffs(df: pd.DataFrame) -> dict:
    # (build_fc_report.py의 compute_account_diffs와 동일 — 코멘트 작성용 대계정별 차이)
    ...  # 전체 코드는 build_fc_report.py 참고, 변경 없이 포팅


def _format_comment(diff_series, force_top1: bool = False) -> str:
    ...  # build_fc_report.py의 format_comment 그대로


def _build_cumulative_ac_sheet(wb, prev_month: str, month: str):
    src = wb[f"{prev_month} 누계(AC)"]
    new = wb.copy_worksheet(src)
    new.title = f"{month} 누계(AC)"
    new.sheet_state = "visible"
    needle = f"'{prev_month}(AC)'!"
    n_modified = 0
    for row in new.iter_rows():
        for cell in row:
            v = cell.value
            if not (isinstance(v, str) and v.startswith('=') and needle in v):
                continue
            tail = f"{needle}{cell.coordinate}"
            if not v.endswith(tail):
                continue  # 예상 패턴과 다른 셀은 건드리지 않음 (안전장치)
            cell.value = v + f"+'{month}(AC)'!{cell.coordinate}"
            n_modified += 1
    for row in new.iter_rows():
        for cell in row:
            v = cell.value
            if isinstance(v, str) and not v.startswith('=') and prev_month in v:
                cell.value = v.replace(prev_month, month)
    src.sheet_state = "hidden"
    return new, n_modified


def _build_cumulative_detail_sheet(wb, prev_month: str, month: str, totals: dict, diffs: dict):
    src = wb[f"{prev_month} 누계(상세)"]
    new = wb.copy_worksheet(src)
    new.title = f"{month} 누계(상세)"
    new.sheet_state = "visible"
    a1 = new['A1'].value
    if isinstance(a1, str) and prev_month in a1:
        new['A1'] = a1.replace(prev_month, month)
    for hb, rowmap in [('본사', ROWS_HQ), ('법인', ROWS_CORP)]:
        for cat, r in rowmap.items():
            budget = totals[(cat, hb, '예산')]
            actual = totals[(cat, hb, '실적')]
            seg_diffs = diffs[(cat, hb)]
            for seg, (bcol, acol, ccol) in SEG_BLOCK_COLS.items():
                new[f"{bcol}{r}"] = round(budget[seg], 0)
                new[f"{acol}{r}"] = round(actual[seg], 0)
                total_diff = actual[seg] - budget[seg]
                if seg == '총합계' or abs(total_diff) >= COMMENT_THRESHOLD:
                    text = _format_comment(seg_diffs[seg], force_top1=(seg == '총합계'))
                    new[f"{ccol}{r}"] = text if text else None
                else:
                    new[f"{ccol}{r}"] = None
    src.sheet_state = "hidden"
    return new


def _reposition(wb, prev_month: str, month: str, suffix: str) -> None:
    name_new = f"{month} {suffix}"
    name_prev = f"{prev_month} {suffix}"
    idx_prev = wb.sheetnames.index(name_prev)
    idx_new = wb.sheetnames.index(name_new)
    wb.move_sheet(name_new, offset=(idx_prev + 1) - idx_new)
```

> 비고 코멘트 한계 (알려진 제한, 자동화 안 함): `_format_comment`는 "11 급여 +77백만 /
> 53 4대보험료 △35백만" 형태의 1줄 기계적 코멘트만 생성. 특정 거래처/이벤트를 짚는 2번째 줄
> (예: "iWedia 외주개발 용역비 집행 지연 지속")은 raw data의 거래처명/Text 컬럼을 사람이 판단해야
> 하는 부분이라 도구가 채우지 않음 — 응답의 `warnings`에 "차이 9백만원 이상 블록 N개, 2번째 줄
> 수동 보강 권장" 형태로 안내만 추가.

## 4. 신규 파일 / 등록 체크리스트

### 4.1 신규 파일

- `src/humax_excel_mcp/core/fc_report_layout.py` — §2.4 상수 전체
- `src/humax_excel_mcp/tools/fc_month_update.py` — §2.5 오케스트레이션 + §3.1/§3.2 함수
- `schemas/responses.py`에 §2.6 모델 4개 추가 (`FcMonthAcSummary`, `FcMonthCumulativeSummary`, `FcMonthVerification`, `FcMonthUpdateResult`)
- (선택) `tests/test_fc_month_update.py` — §6 참고

### 4.2 `tools/__init__.py` 수정 (diff)

```diff
 from .extract import extract_filtered as _extract_filtered
+from .fc_month_update import update_fc_month_report as _update_fc_month_report
 from .report import generate_report as _generate_report

 TOOL_NAMES = [
     "extract_filtered", "verify_sums", "write_cells", "generate_diff_candidates",
     "get_allocation_rates", "update_allocation_rates", "get_exchange_rates",
     "apply_golden_template", "generate_report", "restore_backup",
+    "update_fc_month_report",
 ]

 def register_all(mcp) -> None:
-    """Register all 10 tools on the FastMCP instance."""
+    """Register all 11 tools on the FastMCP instance."""
     ...
     mcp.tool()(audited("restore_backup", file_path_arg="backup_path")(_restore_backup))
+    mcp.tool()(audited("update_fc_month_report", file_path_arg="template_path")(_update_fc_month_report))
```

### 4.3 `server.py` 주석 갱신

`build_server()`의 docstring `"""Build FastMCP server with all 10 tools registered (v0.1.1)."""`
→ `"""Build FastMCP server with all 11 tools registered (v0.2.0)."""` (버전 bump은 SemVer 정책에 맞게 조정)

### 4.4 `CHANGELOG.md` 추가 항목 (초안)

```markdown
## [Unreleased]
### Added
- `update_fc_month_report` 도구 신규 — raw data + 전월 FC 보고서로 당월 배부판
  (`{월}(AC)` 채우기 + `{월} 누계(AC)`/`{월} 누계(상세)` 생성 + 3-way 교차검증) 자동 생성.
  기존 `humax-monthly-report` 스킬의 `build_fc_report.py`가 `{월}(AC)` 개별월 시트를
  채우지 않는 누락을 발견·수정해 포팅 (2026-06-26 5월 실데이터로 검증).
```

## 5. 알려진 제한사항 / 유지보수 포인트

- `ALIAS_TO_ROW`(대조직→row), `CAT_MAP`(대계정→카테고리)는 raw data의 라벨 문자열에 의존.
  raw data 스키마/조직명이 바뀌면 `core/fc_report_layout.py`만 갱신하면 되도록 분리해 둠.
- 1월은 누계 체인의 시작점이라 본 도구로 처리하지 않음 (사전조건에서 `InvalidMonth`로 막음).
  1월 최초 세팅은 별도 수동 절차.
- 비고란 2번째 줄(거래처/이벤트 서술)은 자동화하지 않음 — §3.2 하단 참고.
- `_restore_ac_formulas`는 "현재 셀이 None일 때만" 복원하므로, 템플릿이 이미 부분적으로
  틀린 값을 갖고 있는 경우는 감지하지 못함 — 운영 중 이상 발견 시 별도 점검 필요.

## 6. 테스트 제안

- `fixtures/templates/`에 데이터 클리어드 골든 템플릿이 있는 관례를 따라, 실제 5월 raw data의
  일부(조직 2~3개 × 1개월)만 추출한 미니 fixture로 `_aggregate_org_actuals`/`_fill_ac_actuals`
  단위 테스트.
  
- `_cross_validate`는 이번 세션에서 실제로 1-2원 이내로 일치함을 확인했으므로, 회귀 테스트에서
  `cross_validate_tolerance` 기본값(10원)을 넘기면 바로 실패하도록 assert.
  
- `dry_run=True`일 때 원본 파일이 전혀 수정되지 않는지 (mtime/hash 불변) 확인하는 테스트.

## 7. 범위 외 (Out of scope)

- 고정비 계정별 실적(`build_gyejungbyul.py`), EVCS 고정비 실적(`build_evcs.py`) 포팅 — 별도
  태스크(#9, #10). 본 문서는 "FC 실적 누계/배부판" 파일 1종만 다룬다.
