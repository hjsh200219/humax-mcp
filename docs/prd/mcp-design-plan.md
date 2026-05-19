# humax-excel-mcp 설계 문서

> **버전:** v0.1-draft (Revision 3) | **작성일:** 2026-05-19  
> **상태:** Revision 3 — `get_exchange_rates` 환율 도구 추가 (7개 도구). Architect/Critic 재검토 대기  
> **관련 문서:** `consulting-plan.md` (Section A-I), `humax-lecture-plan.md` (모듈 7)  
> **Revision 1 변경 요약:** Architect/Critic 합의 9개 must-fix 적용 — P1 위반 해소, Option D 추가, FILE_LOCKED, truncation 정렬, 강사 체크리스트, 스키마 버전 관리, 감사 로그 접근 제어, 배포 전략 현실화, API 신뢰 경계 위험 등록  
> **Revision 2 변경 요약:** (1) 전 도구 `output_format` + `artifact_hints` Live Artifact 출력 옵션 추가, (2) `get_allocation_rates` / `update_allocation_rates` 배부율 도구 2종 신규, (3) Pre-mortem S5-S6 추가 (6 시나리오), (4) 테스트/강의/RALPLAN-DR 정합성 갱신  
> **Revision 3 변경 요약:** (1) `get_exchange_rates` 환율 자동 조회 도구 신규 (한국수출입은행 API), (2) Pre-mortem S7 추가 (7 시나리오), (3) 부록 D 통화 코드 매핑 추가, (4) 도구 수 6→7 전체 정합성 갱신, (5) 강의 모듈 7 환율 실습 +10분

---

## 1. 개요

### 1.1 목적

`humax-excel-mcp`는 Humax 고정비 결산 워크플로우에서 발생하는 **5개 에러를 구조적으로 해결**하기 위한 Python MCP(Model Context Protocol) 서버이다. Claude Desktop(Cowork)에서 자연어로 호출하여, Python 결정론 처리의 정확성과 Cowork의 낮은 학습 곡선을 동시에 달성한다.

### 1.2 핵심 가치

실무자는 CLI를 학습하지 않는다. Python 결정론 로직을 MCP `@mcp.tool()` 데코레이터로 감싸면, Claude Desktop에서 자연어 호출만으로 셀 단위 편집, 합계 검증, 토큰 절약 필터링, Diff 후보 추출이 가능해진다.

### 1.3 5개 에러 해결 매핑

| # | 에러 (file #1 원문) | 근본 원인 | MCP 도구 | 해결 방식 |
|---|---|---|---|---|
| 1 | 업데이트 과정에서 원본파일 훼손, 복구불가 | LLM이 Excel 전체를 재생성 → 메타데이터 유실 | `write_cells`, `update_allocation_rates` | openpyxl 셀 단위 편집 + 자동 백업 + 원본 읽기 전용. 배부율 변경도 동일 백업/output_path 정책 적용 |
| 2 | 지시하지 않은 내용 변경 (디자인 드리프트) | 프롬프트에 제약 미명시 → LLM이 "개선" 시도 | `write_cells` | 코드가 지정 셀만 수정. 서식/수식 변경 불가 구조 |
| 3 | 원하는 디자인/조건 구현 어려움 (10회 이상 재명령) | 출력 스키마 미명시 → 매번 다른 결과 | `extract_filtered` | 스키마가 코드에 고정. 동일 입력 → 동일 출력 보장 |
| 4 | data 용량 커서 사용량 빠르게 소진 | 25시트 × 63열 전체 전송 → 토큰 폭발 | `extract_filtered` | 필요한 시트/월/회사/컬럼만 필터링 → 토큰 70-90% 절감 |
| 5 | 작업 후 숫자 검토작업 필요 | LLM 확률적 생성 → 숫자 오류 가능성 | `verify_sums`, `get_allocation_rates` | Python 결정론 합계 검증. 불일치 시 즉시 리포트. 배부율 조회 시 4개 비율 합계 100% 자동 검증 |
| (3-보조) | Step 3 수기 편집: 환율 update | 매월 환율을 수기 확인/입력 → 오류 가능성 | `get_exchange_rates` | 한국수출입은행 API 자동 조회. 휴일 fallback + JPY 정규화 + 캐시. `verify_sums`와 연계하여 환율 적용 후 검증 권장 |

---

## 2. 기술 스택

| 구성 요소 | 버전/패키지 | 역할 |
|---|---|---|
| **Python** | 3.10+ | 런타임 (match문, union type 활용) |
| **FastMCP** (`mcp` SDK) | `pip install mcp` | MCP 서버 프레임워크. `@mcp.tool()` 데코레이터 기반 도구 노출 |
| **openpyxl** | 3.1+ | Excel(.xlsx) 읽기/쓰기. 셀 단위 결정론 편집, 서식 보존 |
| **pandas** | 2.0+ | 대용량 시트 필터링, 피벗, 집계 연산 |
| **pydantic** | 2.0+ | 입력 파라미터 검증, JSON 스키마 자동 생성 |
| **pytest** | 8.0+ | 단위/통합/E2E 테스트 |
| **python-dotenv** | 1.0+ | 환경 변수 관리 (.env 파일) |

### 2.1 선택 근거

- **FastMCP**: Anthropic 공식 MCP SDK. Claude Desktop과 네이티브 연동. `@mcp.tool()` 한 줄로 도구 노출.
- **openpyxl**: 순수 Python. Windows/Mac/Linux 동작. 셀 병합/조건부 서식 등 알려진 제한은 Phase 2 첫 주 호환성 테스트에서 실측 (서식 보존율 95% 미달 시 xlwings fallback).
- **pandas**: 15,007행 × 63열 규모의 26BP 시트를 메모리 내에서 필터링. 토큰 절약의 핵심.
- **pydantic**: MCP 도구 입력 검증 + Claude Desktop에 자동 JSON 스키마 노출 → 자연어 호출 시 파라미터 추론 정확도 향상.

---

## 3. 디렉터리 구조

```
humax-excel-mcp/
├── pyproject.toml              # 패키지 메타 + 의존성
├── .env.example                # 환경 변수 템플릿
├── README.md                   # 퀵스타트 + Claude Desktop 등록
│
├── src/
│   └── humax_excel_mcp/
│       ├── __init__.py
│       ├── server.py           # FastMCP 앱 진입점 + 7개 도구 등록
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── extract.py      # extract_filtered 구현
│       │   ├── verify.py       # verify_sums 구현
│       │   ├── write.py        # write_cells 구현
│       │   ├── diff.py         # generate_diff_candidates 구현
│       │   ├── allocation_get.py   # get_allocation_rates 구현
│       │   ├── allocation_set.py   # update_allocation_rates 구현
│       │   └── exchange.py        # get_exchange_rates 구현
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── bp26.py         # 26BP 63컬럼 스키마 정의
│       │   ├── requests.py     # 각 도구의 입력 pydantic 모델
│       │   └── responses.py    # 각 도구의 출력 pydantic 모델
│       ├── core/
│       │   ├── __init__.py
│       │   ├── excel_io.py     # openpyxl 래퍼 (읽기/쓰기/백업)
│       │   ├── backup.py       # 자동 백업 로직
│       │   ├── filters.py      # 월/회사/컬럼 필터 로직
│       │   ├── validators.py   # 합계 검증, 이상치 탐지
│       │   └── token_guard.py  # 응답 크기 제한 (토큰 가드)
│       └── config.py           # 설정 관리 (dotenv 로딩)
│
├── tests/
│   ├── conftest.py             # pytest fixtures (샘플 Excel 생성)
│   ├── unit/
│   │   ├── test_extract.py
│   │   ├── test_verify.py
│   │   ├── test_write.py
│   │   └── test_diff.py
│   ├── integration/
│   │   ├── test_mcp_server.py  # MCP 서버 기동 + tool invocation
│   │   └── test_backup.py      # 백업/복구 시나리오
│   └── e2e/
│       └── test_monthly_close.py  # 월 결산 시뮬레이션
│
├── fixtures/
│   ├── sample_26bp.xlsx        # 테스트용 합성 26BP (마스킹)
│   ├── sample_prev_month.xlsx  # 전월 산출물 합성본
│   └── golden/                 # known-good 결과 (E2E 비교용)
│       ├── expected_extract.json
│       ├── expected_verify.json
│       └── expected_diff.json
│
└── docs/
    ├── claude-desktop-setup.md # Claude Desktop 등록 가이드
    └── schema-mapping.md       # 26BP 컬럼 매핑 상세
```

---

## 4. 7개 도구 상세 Spec

### 4.1 `extract_filtered` -- 필터링 추출

26BP 원본에서 필요한 데이터만 추출하여 Claude 컨텍스트에 전달. 토큰 70-90% 절감의 핵심 도구.

#### 함수 시그니처

```python
@mcp.tool()
async def extract_filtered(
    file_path: str,
    sheet_name: str,
    *,
    month: str | None = None,
    company: str | None = None,
    columns: list[str] | None = None,
    org_level: str | None = None,
    account_group: str | None = None,
    max_rows: int = 500,
    sort_by: Literal["row_order", "variance_abs_desc", "amount_desc"] = "variance_abs_desc",
    output_format: Literal["json", "csv", "markdown"] = "json",
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> ExtractResult:
    """26BP Excel에서 조건에 맞는 데이터를 필터링 추출합니다."""
```

#### 입력 파라미터

| 파라미터 | 타입 | 필수 | 검증 룰 | 설명 |
|---|---|---|---|---|
| `file_path` | `str` | Y | 파일 존재 확인, `.xlsx` 확장자 | 대상 Excel 파일 경로 |
| `sheet_name` | `str` | Y | 시트 존재 확인 | 대상 시트명 (예: "예산+실적", "3월", "누계") |
| `month` | `str \| None` | N | `YYYY-MM` 형식 또는 `None` | 월 필터 (예: "2026-03") |
| `company` | `str \| None` | N | 유효 회사 코드 검증 | 회사 필터 (예: "HMX", "HUS", "HUK", "HBR", "HSZ") |
| `columns` | `list[str] \| None` | N | bp26 스키마 키 이름으로 검증 | 추출할 컬럼 목록. `None`이면 기본 25개 컬럼 |
| `org_level` | `str \| None` | N | 유효 조직 레벨 검증 | 조직 계층 필터 (예: "본사", "사업부") |
| `account_group` | `str \| None` | N | 유효 계정 그룹 검증 | 계정 그룹 필터 (예: "인건비", "경비") |
| `max_rows` | `int` | N | `1 <= max_rows <= 2000` | 최대 반환 행 수 (토큰 가드) |
| `sort_by` | `Literal` | N | `"row_order" \| "variance_abs_desc" \| "amount_desc"` | truncation 전 정렬 기준. 기본값 `variance_abs_desc` (재무 데이터는 차이 큰 항목 우선) |
| `output_format` | `Literal` | N | `"json" \| "csv" \| "markdown"` | 출력 형식 |
| `render_format` | `Literal` | N | `"excel" \| "live_artifact" \| "both"` | 출력 대상. `"live_artifact"` 또는 `"both"` 시 `artifact_hints` 포함. 미명시 시 Claude가 자연어로 확인 |

#### 동작 단계

1. **파일 검증**: `file_path` 존재 및 `.xlsx` 확장자 확인
2. **시트 로딩**: openpyxl `load_workbook(data_only=True)` → pandas DataFrame 변환
3. **필터 적용** (순차):
   - `month` 필터: 월 컬럼 기준 행 필터링
   - `company` 필터: 회사 코드 컬럼 기준 행 필터링
   - `org_level` 필터: 대조직/중조직 컬럼 기준 행 필터링
   - `account_group` 필터: 계정 그룹 컬럼 기준 행 필터링
   - `columns` 필터: 지정 컬럼만 선택 (미지정 시 기본 25개)
4. **정렬 + 행 제한**: `sort_by` 기준으로 정렬 후 `max_rows` 초과 시 상위 N행 반환 + `truncated: true` 플래그. 기본값 `variance_abs_desc`는 |예산-실적| 차이가 큰 행을 우선 반환하여 truncation 시 중요 이상치가 누락되지 않도록 보장
5. **토큰 가드**: 직렬화 결과가 100KB 초과 시 자동으로 `max_rows` 축소 후 재시도
6. **직렬화**: `output_format`에 따라 JSON/CSV/Markdown 변환
7. **반환**: `ExtractResult` 객체

#### 반환 데이터 구조

```json
{
  "success": true,
  "data": [
    {
      "row_index": 5,
      "구분": "본사",
      "Company": "HMX",
      "대조직": "경영지원",
      "GL_Account": "511000",
      "GL_Account_Name": "급여",
      "budget_amount": 150000,
      "actual_amount": 145000,
      "variance": -5000,
      "text_summary": "본사 경영지원 급여"
    }
  ],
  "metadata": {
    "total_rows": 15007,
    "filtered_rows": 342,
    "returned_rows": 342,
    "truncated": false,
    "filters_applied": {
      "month": "2026-03",
      "company": "HMX",
      "columns": ["구분", "Company", "대조직", "GL_Account", "budget_amount", "actual_amount"]
    },
    "sort_order": "variance_abs_desc",
    "estimated_tokens": 12500,
    "file_path": "/path/to/26BP.xlsx",
    "sheet_name": "예산+실적"
  },
  "render_format": "live_artifact",
  "artifact_hints": {
    "type": "table_with_chart",
    "title": "26.03 본사 인건비 필터 결과",
    "preferred_chart": "bar",
    "columns_for_chart": ["gl_account_name", "budget_amount", "actual_amount"],
    "highlight_threshold": 10
  }
}
```

#### 에러 케이스

| 에러 | 코드 | 메시지 |
|---|---|---|
| 파일 미존재 | `FILE_NOT_FOUND` | `"파일을 찾을 수 없습니다: {file_path}"` |
| 시트 미존재 | `SHEET_NOT_FOUND` | `"시트를 찾을 수 없습니다: {sheet_name}. 사용 가능: {available_sheets}"` |
| 잘못된 컬럼명 | `INVALID_COLUMN` | `"잘못된 컬럼명: {col}. 사용 가능: {valid_columns}"` |
| 잘못된 회사 코드 | `INVALID_COMPANY` | `"잘못된 회사 코드: {company}. 사용 가능: HMX, HUS, HUK, HBR, HSZ"` |
| 토큰 초과 | `TOKEN_LIMIT_EXCEEDED` | `"응답 크기 초과. max_rows를 {suggested}로 줄여주세요."` |
| 빈 결과 | `EMPTY_RESULT` | `"필터 조건에 맞는 데이터가 없습니다."` |
| 파일 잠금 | `FILE_LOCKED` | `"파일이 다른 프로그램에서 열려 있습니다. Excel을 닫고 다시 시도하세요."` |
| 스키마 불일치 | `SCHEMA_MISMATCH` | `"파일 헤더가 스키마 v{version}과 일치하지 않습니다. 변경된 컬럼: {diff}. schemas/bp26.py를 업데이트하세요."` |

#### 토큰/응답 크기 제약

- **하드 리밋**: 직렬화 결과 100KB (약 25,000-35,000 토큰)
- **소프트 리밋**: 50KB 초과 시 경고 + `max_rows` 축소 권장
- **기본 max_rows**: 500행 (26BP 월별 본사 데이터 기준 안전 범위)
- **토큰 추정**: JSON 1행 평균 약 30-50 토큰 기준

---

### 4.2 `verify_sums` -- 합계 검증

조직 5계층 합산 일치 여부를 결정론적으로 검증. 에러 #5(숫자 검토 부담) 해결의 핵심.

#### 함수 시그니처

```python
@mcp.tool()
async def verify_sums(
    file_path: str,
    sheet_name: str,
    *,
    levels: list[str] | None = None,
    tolerance: float = 0.01,
    check_formulas: bool = True,
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> VerifyResult:
    """Excel 시트의 조직 계층별 합계 일치를 검증합니다."""
```

#### 입력 파라미터

| 파라미터 | 타입 | 필수 | 검증 룰 | 설명 |
|---|---|---|---|---|
| `file_path` | `str` | Y | 파일 존재 + `.xlsx` | 대상 Excel 파일 |
| `sheet_name` | `str` | Y | 시트 존재 확인 | 대상 시트명 |
| `levels` | `list[str] \| None` | N | 유효 조직 레벨 목록 | 검증할 조직 레벨 (기본: 전체 5계층) |
| `tolerance` | `float` | N | `0 <= tolerance <= 1.0` | 허용 오차 (백만원 단위, 기본 0.01 = 1만원) |
| `check_formulas` | `bool` | N | - | 수식 셀 존재 여부 검사 포함 |
| `render_format` | `Literal` | N | `"excel" \| "live_artifact" \| "both"` | 출력 대상. `"live_artifact"` 시 검증 결과 Pass/Fail 카드 + 5계층 트리 artifact_hints 포함 |

#### 동작 단계

1. **파일/시트 로딩**: openpyxl로 값 모드(`data_only=True`) + 수식 모드(별도) 이중 로딩
2. **조직 계층 식별**: 행 구조 파싱 → 총합계/사업부/대조직/중조직/소조직 5계층 트리 구성
3. **합계 검증** (계층별 bottom-up):
   - 소조직 합계 = 해당 소조직 내 상세 행의 합
   - 중조직 합계 = 해당 중조직 하위 소조직 합계의 합
   - 대조직 합계 = 해당 대조직 하위 중조직 합계의 합
   - 사업부 합계 = 해당 사업부 하위 대조직 합계의 합
   - 총합계 = 모든 사업부 합계의 합
4. **이상치 탐지**: |예산 - 실적| >= 10백만원인 항목 자동 추출
5. **수식 검증** (`check_formulas=True` 시): 수식 셀이 값으로 덮어쓰여진 경우 경고
6. **결과 집계**: 계층별 pass/fail 리스트, 이상치 리스트, 수식 경고 리스트

#### 반환 데이터 구조

```json
{
  "success": true,
  "summary": {
    "total_checks": 47,
    "passed": 45,
    "failed": 2,
    "warnings": 1
  },
  "level_results": [
    {
      "level": "총합계",
      "expected": 1250000,
      "actual": 1250000,
      "difference": 0,
      "status": "PASS"
    },
    {
      "level": "사업부-STB",
      "expected": 450000,
      "actual": 449985,
      "difference": -15,
      "status": "FAIL",
      "detail": "대조직 '개발' 합계 불일치: expected 120000, actual 119985"
    }
  ],
  "anomalies": [
    {
      "row_index": 23,
      "org": "본사-경영지원",
      "account": "급여",
      "budget": 150000,
      "actual": 65000,
      "variance": -85000,
      "flag": "LARGE_VARIANCE",
      "suggested_comment": "11 급여 -85백만"
    }
  ],
  "formula_warnings": [
    {
      "cell": "F15",
      "expected_formula": "=SUM(F16:F25)",
      "current_state": "hard_coded_value",
      "warning": "수식이 값으로 덮어쓰여져 있습니다."
    }
  ],
  "metadata": {
    "file_path": "/path/to/file.xlsx",
    "sheet_name": "3월",
    "levels_checked": ["총합계", "사업부", "대조직", "중조직", "소조직"],
    "tolerance": 0.01,
    "anomaly_threshold_million": 10
  }
}
```

#### 에러 케이스

| 에러 | 코드 | 메시지 |
|---|---|---|
| 파일 미존재 | `FILE_NOT_FOUND` | `"파일을 찾을 수 없습니다: {file_path}"` |
| 시트 미존재 | `SHEET_NOT_FOUND` | `"시트를 찾을 수 없습니다: {sheet_name}"` |
| 조직 구조 파싱 실패 | `PARSE_ERROR` | `"조직 계층 구조를 인식할 수 없습니다. 시트 형식을 확인하세요."` |
| 합계 행 미발견 | `SUBTOTAL_NOT_FOUND` | `"합계 행을 찾을 수 없습니다. 레벨: {level}"` |
| 파일 잠금 | `FILE_LOCKED` | `"파일이 다른 프로그램에서 열려 있습니다. Excel을 닫고 다시 시도하세요."` |
| 스키마 불일치 | `SCHEMA_MISMATCH` | `"파일 헤더가 스키마 v{version}과 일치하지 않습니다. 변경된 컬럼: {diff}. schemas/bp26.py를 업데이트하세요."` |

#### 토큰/응답 크기 제약

- 검증 결과는 구조화된 요약이므로 일반적으로 5-15KB (2,000-5,000 토큰)
- 이상치 항목이 50개 초과 시 상위 50개만 반환 + 잔여 수 표시

---

### 4.3 `write_cells` -- 결정론적 셀 편집

지정된 셀만 정확히 수정. 에러 #1(원본 훼손), #2(디자인 드리프트) 해결의 핵심.

#### 함수 시그니처

```python
@mcp.tool()
async def write_cells(
    file_path: str,
    sheet_name: str,
    updates: list[CellUpdate],
    *,
    output_path: str | None = None,
    dry_run: bool = False,
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> WriteResult:
    """Excel 파일의 지정된 셀만 결정론적으로 편집합니다. 서식/수식은 보존됩니다.
    백업은 항상 자동 생성됩니다 (비활성화 불가). output_path는 file_path와 달라야 합니다."""
```

#### 입력 파라미터

| 파라미터 | 타입 | 필수 | 검증 룰 | 설명 |
|---|---|---|---|---|
| `file_path` | `str` | Y | 파일 존재 + `.xlsx` | 대상 Excel 파일 |
| `sheet_name` | `str` | Y | 시트 존재 확인 | 대상 시트명 |
| `updates` | `list[CellUpdate]` | Y | 1 <= len <= 5000, 셀 주소 유효성 | 편집할 셀 목록 |
| `output_path` | `str \| None` | N | 디렉터리 존재 확인 + **`output_path != file_path` 서버 측 검증** | 출력 파일 경로. `None`이면 원본 옆에 `_edited` 접미사. **원본 직접 덮어쓰기 불가** |
| `dry_run` | `bool` | N | - | `True`면 실제 쓰기 없이 검증만 수행 |

#### CellUpdate 구조

```python
class CellUpdate(BaseModel):
    cell: str                    # 셀 주소 (예: "D5", "F23")
    value: int | float | str     # 새 값
    skip_if_formula: bool = True # True면 수식 셀은 건너뜀 (기본 True)
```

#### 동작 단계

1. **입력 검증**: `file_path`, `sheet_name`, 각 `CellUpdate`의 셀 주소 유효성. `output_path == file_path` 시 `OVERWRITE_ORIGINAL_FORBIDDEN` 에러 즉시 반환
2. **백업 생성** (항상 실행, 비활성화 불가):
   - 백업 경로: `{원본_디렉터리}/.backup/{원본명}_{YYYYMMDD_HHMMSS}.xlsx`
   - 백업 성공 확인 후에만 편집 진행
3. **워크북 로딩**: openpyxl `load_workbook()` (수식 모드, 서식 보존)
4. **수식 셀 보호**: 각 `CellUpdate`에 대해 해당 셀이 수식 셀인지 확인
   - `skip_if_formula=True`이고 수식 셀이면: 건너뜀 + 경고 기록
   - `skip_if_formula=False`이고 수식 셀이면: 값 덮어쓰기 + 경고 기록
5. **셀 편집**: 값만 교체. 서식(폰트, 배경색, 테두리, 열 너비, 행 높이) 변경 없음
6. **Dry-run** (`dry_run=True` 시): 검증 결과만 반환, 파일 쓰기 없음
7. **저장**: `output_path` 또는 기본 경로에 저장
8. **사후 검증**: 저장된 파일을 다시 읽어 편집된 셀 값 확인 (write-read-verify)

#### 반환 데이터 구조

```json
{
  "success": true,
  "dry_run": false,
  "summary": {
    "total_updates": 150,
    "applied": 145,
    "skipped_formula": 3,
    "skipped_invalid": 2,
    "warnings": 3
  },
  "output_path": "/path/to/file_edited.xlsx",
  "backup_path": "/path/to/.backup/file_20260319_143022.xlsx",
  "applied": [
    {"cell": "D5", "old_value": 120000, "new_value": 125000}
  ],
  "skipped": [
    {"cell": "F15", "reason": "formula_cell", "formula": "=SUM(F16:F25)"}
  ],
  "warnings": [
    {"cell": "G8", "message": "병합 셀 범위 내 편집 — 마스터 셀만 수정됨"}
  ],
  "verification": {
    "verified": true,
    "mismatches": []
  }
}
```

#### 에러 케이스

| 에러 | 코드 | 메시지 |
|---|---|---|
| 파일 미존재 | `FILE_NOT_FOUND` | `"파일을 찾을 수 없습니다: {file_path}"` |
| 시트 미존재 | `SHEET_NOT_FOUND` | `"시트를 찾을 수 없습니다: {sheet_name}"` |
| 백업 실패 | `BACKUP_FAILED` | `"백업 생성 실패: {reason}. 편집을 중단합니다."` |
| 셀 주소 무효 | `INVALID_CELL` | `"잘못된 셀 주소: {cell}"` |
| 출력 경로 쓰기 불가 | `WRITE_PERMISSION_DENIED` | `"출력 경로에 쓸 수 없습니다: {output_path}"` |
| 사후 검증 실패 | `VERIFICATION_FAILED` | `"쓰기 후 검증 실패: {mismatches}. 백업에서 복구하세요."` |
| 업데이트 수 초과 | `TOO_MANY_UPDATES` | `"최대 5000개 셀까지 편집 가능합니다. 요청: {count}"` |
| 원본 덮어쓰기 시도 | `OVERWRITE_ORIGINAL_FORBIDDEN` | `"output_path가 원본 file_path와 동일합니다. 원본 직접 덮어쓰기는 허용되지 않습니다."` |
| 파일 잠금 | `FILE_LOCKED` | `"파일이 다른 프로그램에서 열려 있습니다. Excel을 닫고 다시 시도하세요."` |
| 스키마 불일치 | `SCHEMA_MISMATCH` | `"파일 헤더가 스키마 v{version}과 일치하지 않습니다. 변경된 컬럼: {diff}. schemas/bp26.py를 업데이트하세요."` |

#### 토큰/응답 크기 제약

- 결과는 편집 요약이므로 일반적으로 5-20KB
- `applied` 배열이 1000개 초과 시 처음/마지막 50개만 + 중간 생략

---

### 4.4 `generate_diff_candidates` -- Diff 후보 추출

전월 대비 |10백만원| 이상 변동 항목을 추출하여 코멘트 초안 재료 제공.

#### 함수 시그니처

```python
@mcp.tool()
async def generate_diff_candidates(
    prev_file: str,
    curr_file: str,
    *,
    prev_sheet: str = "누계",
    curr_sheet: str = "누계",
    threshold_million: float = 10.0,
    include_comment_draft: bool = True,
    max_candidates: int = 100,
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> DiffResult:
    """전월 대비 변동이 큰 항목을 추출하고 코멘트 초안을 생성합니다."""
```

#### 입력 파라미터

| 파라미터 | 타입 | 필수 | 검증 룰 | 설명 |
|---|---|---|---|---|
| `prev_file` | `str` | Y | 파일 존재 + `.xlsx` | 전월 파일 경로 |
| `curr_file` | `str` | Y | 파일 존재 + `.xlsx` | 당월 파일 경로 |
| `prev_sheet` | `str` | N | 시트 존재 확인 | 전월 시트명 (기본 "누계") |
| `curr_sheet` | `str` | N | 시트 존재 확인 | 당월 시트명 (기본 "누계") |
| `threshold_million` | `float` | N | `threshold >= 0` | 변동 임계값 (백만원, 기본 10.0) |
| `include_comment_draft` | `bool` | N | - | 코멘트 초안 생성 여부 |
| `max_candidates` | `int` | N | `1 <= max_candidates <= 500` | 최대 후보 수 |

#### 동작 단계

1. **양 파일 로딩**: 전월/당월 각각 openpyxl → pandas DataFrame
2. **구조 대조**: 두 시트의 행/열 구조 일치 여부 확인. 불일치 시 경고 + 공통 부분만 비교
3. **셀 단위 차이 계산**: `당월값 - 전월값` 산출
4. **임계값 필터링**: `|차이| >= threshold_million` (백만원 단위) 항목만 추출
5. **코멘트 초안 생성** (`include_comment_draft=True` 시):
   - 패턴: `[코드] [계정명] [+/-금액]백만` (예: "11 급여 -85백만")
   - 변동률 50% 이상 시 "대폭 증가/감소" 태그 추가
6. **정렬**: |차이| 내림차순
7. **후보 수 제한**: `max_candidates` 초과 시 잔여 수 표시

#### 반환 데이터 구조

```json
{
  "success": true,
  "summary": {
    "total_cells_compared": 4725,
    "candidates_found": 23,
    "candidates_returned": 23,
    "truncated": false,
    "largest_variance_million": 85.0,
    "net_variance_million": -120.5
  },
  "candidates": [
    {
      "row_index": 23,
      "org": "본사",
      "sub_org": "경영지원",
      "account_code": "511000",
      "account_name": "급여",
      "prev_value": 150000,
      "curr_value": 65000,
      "diff": -85000,
      "diff_million": -85.0,
      "diff_pct": -56.7,
      "comment_draft": "11 급여 -85백만 (대폭 감소, -56.7%)",
      "severity": "HIGH"
    }
  ],
  "structure_warnings": [],
  "metadata": {
    "prev_file": "/path/to/prev.xlsx",
    "curr_file": "/path/to/curr.xlsx",
    "prev_sheet": "누계",
    "curr_sheet": "누계",
    "threshold_million": 10.0
  }
}
```

#### 에러 케이스

| 에러 | 코드 | 메시지 |
|---|---|---|
| 전월 파일 미존재 | `FILE_NOT_FOUND` | `"전월 파일을 찾을 수 없습니다: {prev_file}"` |
| 당월 파일 미존재 | `FILE_NOT_FOUND` | `"당월 파일을 찾을 수 없습니다: {curr_file}"` |
| 시트 구조 불일치 | `STRUCTURE_MISMATCH` | `"시트 구조가 다릅니다: 전월 {prev_cols}열, 당월 {curr_cols}열. 공통 부분만 비교합니다."` (경고, 계속 진행) |
| 숫자 아닌 셀 | `NON_NUMERIC` | (내부 건너뜀, 에러 아닌 경고로 처리) |
| 파일 잠금 | `FILE_LOCKED` | `"파일이 다른 프로그램에서 열려 있습니다. Excel을 닫고 다시 시도하세요."` |
| 스키마 불일치 | `SCHEMA_MISMATCH` | `"파일 헤더가 스키마 v{version}과 일치하지 않습니다. 변경된 컬럼: {diff}. schemas/bp26.py를 업데이트하세요."` |

#### 토큰/응답 크기 제약

- 후보 100개 기준 약 15-30KB
- `max_candidates=500` 최대 시 약 75KB (하드 리밋 100KB 이내)

---

### 4.5 Live Artifact 자동 생성

모든 7개 도구에 `render_format: Literal["excel", "live_artifact", "both"] = "excel"` 파라미터를 추가하여, Claude Desktop(Cowork)의 Live Artifact 기능과 연동한다.

#### 작동 메커니즘

1. **사용자 호출**: 자연어로 도구 호출 시 `render_format` 명시 또는 미명시
2. **미명시 시 확인**: Claude가 `"결과를 Excel로 저장할까요, 아니면 화면에 바로 보여드릴까요?"` 자연어 확인
3. **MCP 도구 응답**: 데이터(`data`) + 메타데이터(`metadata`) + **`artifact_hints`** 필드 반환
4. **Claude Desktop 측**: `artifact_hints`를 참조하여 Live Artifact 자동 생성 (표, 차트, 카드 등)
5. **MCP는 hints만 제공**: 실제 렌더링은 Claude Desktop이 수행. MCP 서버는 데이터와 힌트만 반환

#### artifact_hints 스키마

```python
class ArtifactHints(BaseModel):
    type: Literal[
        "table", "chart", "dashboard", "diff_cards",
        "verification_result", "table_with_chart", "before_after_bar"
    ]
    title: str                                          # Artifact 제목
    preferred_chart: Literal[
        "bar", "line", "pie", "tree", "stacked_bar", "before_after_bar"
    ] | None = None
    columns_for_chart: list[str] | None = None          # 차트에 사용할 컬럼
    comparison_columns: list[str] | None = None         # 비교 대상 컬럼
    highlight_threshold: int | None = None              # 강조 임계값
    pii_redacted: bool = False                          # PII 마스킹 적용 여부
```

#### 응답 스키마 확장 (공통)

모든 도구의 반환 JSON에 아래 필드가 추가된다 (`render_format`이 `"live_artifact"` 또는 `"both"` 일 때):

```python
{
  "status": "ok",
  "data": [...],
  "metadata": {...},
  "render_format": "live_artifact",
  "artifact_hints": {
    "type": "dashboard" | "table" | "chart" | "diff_cards" | ...,
    "title": str,
    "preferred_chart": "bar" | "line" | "pie" | "tree" | ...,
    "columns_for_chart": list[str],
    "comparison_columns": list[str],
    "highlight_threshold": int | None,
    "pii_redacted": bool
  }
}
```

#### 도구별 권장 artifact 유형

| 도구 | artifact 유형 | 상세 |
|---|---|---|
| `extract_filtered` | 필터된 표 + 막대 차트 + 합계 카드 | `type: "table_with_chart"`, `preferred_chart: "bar"` |
| `verify_sums` | 검증 결과 Pass/Fail 카드 + 5계층 트리 | `type: "verification_result"`, `preferred_chart: "tree"` |
| `write_cells` | dry-run 미리보기 + 변경 셀 diff 카드 | `type: "diff_cards"` |
| `generate_diff_candidates` | Diff 카드 리스트 + 트렌드 차트 | `type: "diff_cards"`, `preferred_chart: "bar"` |
| `get_allocation_rates` | 배부율 테이블 + 사업부별 비율 차트 | `type: "table_with_chart"`, `preferred_chart: "stacked_bar"` |
| `update_allocation_rates` | dry-run 미리보기 + 변경 전후 비교 | `type: "diff_cards"`, `preferred_chart: "before_after_bar"` |
| `get_exchange_rates` | 환율 대시보드 + 통화별 막대 차트 | `type: "rates_dashboard"`, `preferred_chart: "bar"` |

#### 자연어 확인 흐름

```
사용자: "3월 본사 인건비 추출해줘"

Claude (render_format 미명시 감지):
  "결과를 Excel 파일로 저장할까요, 아니면 화면에 바로 시각화해서 보여드릴까요?
   1) Excel 파일 저장
   2) 화면에 바로 보기 (Live Artifact)
   3) 둘 다"

사용자: "화면에 보여줘"

Claude → extract_filtered(render_format="live_artifact") 호출
  → artifact_hints 포함 응답 수신
  → Live Artifact로 필터된 표 + 막대 차트 자동 렌더링
```

#### 보안 정책

- **PII 마스킹**: `artifact_hints.pii_redacted` 플래그로 PII 마스킹 적용 여부 표시. PII 처리는 Section 6.4 거버넌스 정책을 따름
- **Anthropic API 경유**: Artifact 데이터도 Claude Desktop → Anthropic API 경로를 경유하므로, Section 6.4의 데이터 분류/PII 필터 정책이 동일하게 적용됨
- **외부 공유 금지**: Live Artifact 스크린샷/캡처를 통한 PII 유출 방지를 위해, PII 포함 데이터의 artifact에는 `"pii_redacted": true` 플래그 + `"이 데이터는 사내 전용입니다. 외부 공유를 금지합니다."` 워터마크 안내 첨부

---

### 4.6 `get_allocation_rates` -- 배부율 조회

26BP raw `예산+실적` 시트에서 현재 적용 중인 배부율을 조회한다. file #1 Step 3 (수기 편집)의 "환율/배부율 update" 작업 중 배부율 부분을 자동화하기 위한 조회 도구.

#### 데이터 출처

- **시트**: `예산+실적`
- **컬럼**: C30 배부기준 / C31 STB 배부율(%) / C32 Mobility 배부율(%) / C33 EVCS국내 배부율(%) / C34 EVCS해외 배부율(%)

#### 함수 시그니처

```python
@mcp.tool()
async def get_allocation_rates(
    file_path: str,
    month: int,
    *,
    company: str | None = None,
    cost_center: str | None = None,
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> AllocationRatesResult:
    """26BP raw에서 적용 중인 배부율 조회.

    데이터 출처: raw 예산+실적 시트 C30 배부기준 / C31-34 STB/Mobility/EVCS(국내)/EVCS(해외) 배부율 (%)
    """
```

#### 입력 파라미터

| 파라미터 | 타입 | 필수 | 검증 룰 | 설명 |
|---|---|---|---|---|
| `file_path` | `str` | Y | 파일 존재 + `.xlsx` | 26BP raw 파일 경로 |
| `month` | `int` | Y | `1 <= month <= 12` | 대상 월 |
| `company` | `str \| None` | N | 유효 회사 코드 검증 | 특정 회사 필터 |
| `cost_center` | `str \| None` | N | CC 코드 형식 검증 | 특정 Cost Center 필터 |
| `render_format` | `Literal` | N | `"excel" \| "live_artifact" \| "both"` | 출력 대상 |

#### 동작 단계

1. **파일 존재 / 잠금 확인**: 미존재 시 `FILE_NOT_FOUND`, 잠금 시 `FILE_LOCKED`
2. **시트 헤더 검증**: `예산+실적` 시트의 C30-C34 컬럼 존재 확인 (SCHEMA_MISMATCH)
3. **시트 로딩**: openpyxl `load_workbook(data_only=True)` (read-only)
4. **행 필터링**: `month` + `company` + `cost_center` 조건으로 대상 행 필터
5. **배부율 추출**: C30(배부기준), C31(STB%), C32(Mobility%), C33(EVCS국내%), C34(EVCS해외%) 추출
6. **그룹화**: 동일 (배부기준, 4개 비율) 조합별 그룹화 → 적용 단위 식별
7. **합계 검증**: 각 행의 4개 비율 합 = 100% 검증. 위반 시 `rate_sum_violations` 카운트 + 경고
8. **artifact_hints 생성**: 배부율 테이블 + 사업부별 비율 stacked bar 차트

#### 반환 데이터 구조

```json
{
  "status": "ok",
  "data": [
    {
      "cost_center": "102401",
      "cost_center_name": "Staff(CEO)",
      "allocation_basis": "경영지원부문",
      "rates": {
        "STB": 35.0,
        "Mobility": 0.0,
        "EVCS_domestic": 30.0,
        "EVCS_overseas": 35.0
      },
      "rate_sum": 100.0,
      "rate_sum_ok": true,
      "row_count": 12
    }
  ],
  "metadata": {
    "month": 3,
    "filter_company": null,
    "filter_cc": null,
    "rate_sum_violations": 0,
    "unique_rates_count": 47,
    "schema_version": "2026.05"
  },
  "render_format": "live_artifact",
  "artifact_hints": {
    "type": "table_with_chart",
    "title": "26.03 배부율 조회",
    "preferred_chart": "stacked_bar",
    "columns_for_chart": ["cost_center_name", "STB", "Mobility", "EVCS_domestic", "EVCS_overseas"],
    "pii_redacted": false
  }
}
```

#### 에러 케이스

| 에러 | 코드 | 메시지 |
|---|---|---|
| 파일 미존재 | `FILE_NOT_FOUND` | `"파일을 찾을 수 없습니다: {file_path}"` |
| 파일 잠금 | `FILE_LOCKED` | `"파일이 다른 프로그램에서 열려 있습니다. Excel을 닫고 다시 시도하세요."` |
| 시트 미존재 | `SHEET_NOT_FOUND` | `"예산+실적 시트를 찾을 수 없습니다."` |
| 스키마 불일치 | `SCHEMA_MISMATCH` | `"C30-C34 배부율 컬럼이 누락되었습니다. 스키마 v{version} 확인 필요."` |
| 잘못된 월 | `INVALID_MONTH` | `"month는 1-12 범위여야 합니다. 입력: {month}"` |
| 비율 합 위반 | `RATE_SUM_VIOLATION` | `"배부율 합계 100% 위반 행 {count}건 발견. (경고, 결과는 반환)"` |

#### 토큰/응답 크기 제약

- 배부율 조회 결과는 일반적으로 3-10KB (unique_rates_count 50개 기준)
- 100KB 하드 리밋 이내

---

### 4.7 `update_allocation_rates` -- 배부율 변경

26BP raw의 배부율을 변경한다. `write_cells`와 동일한 안전 정책 (원본 보존, 자동 백업, dry-run, output_path 검증)을 적용한다.

#### 함수 시그니처

```python
@mcp.tool()
async def update_allocation_rates(
    file_path: str,
    month: int,
    updates: list[AllocationUpdate],
    output_path: str,
    *,
    dry_run: bool = False,
    rate_tolerance: float = 0.01,
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> AllocationUpdateResult:
    """26BP raw의 배부율 변경. 원본 보존 + 자동 백업 + dry-run 지원.

    write_cells와 동일한 안전 정책 적용:
    - 원본 자동 백업 (create_backup 비노출, 항상 True)
    - output_path != file_path 검증 (OVERWRITE_ORIGINAL_FORBIDDEN)
    - dry_run으로 변경 미리보기
    - rate_tolerance: 4개 비율 합 == 100 검증 시 허용 오차 (IEEE 754 drift 대응,
      `verify_sums.tolerance` 일관 패턴). 기본 0.01% 이내 허용
    """
```

#### AllocationUpdate 구조

```python
class AllocationUpdate(BaseModel):
    cost_center: str                    # Cost Center 코드 (식별자)
    allocation_basis: str               # 배부기준 (식별자)
    new_rates: dict[str, float]         # {"STB": 40.0, "Mobility": 0.0, "EVCS_domestic": 30.0, "EVCS_overseas": 30.0}
```

#### 입력 파라미터

| 파라미터 | 타입 | 필수 | 검증 룰 | 설명 |
|---|---|---|---|---|
| `file_path` | `str` | Y | 파일 존재 + `.xlsx` | 26BP raw 파일 경로 |
| `month` | `int` | Y | `1 <= month <= 12` | 대상 월 |
| `updates` | `list[AllocationUpdate]` | Y | 각 항목 검증 (합계 100%, 범위 0-100) | 변경 항목 리스트 |
| `output_path` | `str` | Y | `output_path != file_path` 서버 측 검증 | 변경 결과 저장 경로 |
| `dry_run` | `bool` | N | - | `True`면 변경 미리보기만 반환, 파일 미작성 |
| `render_format` | `Literal` | N | `"excel" \| "live_artifact" \| "both"` | 출력 대상 |

#### 동작 단계

1. **파일 존재 / 잠금 / 헤더 검증**: FILE_NOT_FOUND, FILE_LOCKED, SCHEMA_MISMATCH
2. **output_path != file_path 검증**: 동일 시 `OVERWRITE_ORIGINAL_FORBIDDEN` 즉시 반환
3. **자동 백업 생성**: `.backup/{원본명}_{YYYYMMDD_HHMMSS}.xlsx` (항상 실행, 비활성화 불가)
4. **updates 각 항목 검증**:
   - 4개 비율 합 = 100 검증 with `rate_tolerance` (`abs(sum - 100.0) <= rate_tolerance`). 위반 시 `RATE_SUM_NOT_100`. IEEE 754 drift 회피 (예: 33.33+33.33+33.34=99.999999998은 tolerance 0.01 이내 허용)
   - 각 비율 범위 0-100 검증 (`INVALID_RATE`)
   - `cost_center` + `allocation_basis` 일치 행 존재 확인 (`CC_BASIS_NOT_FOUND`)
5. **dry_run=True**: 변경 사항 미리보기만 반환 (파일 미작성)
6. **dry_run=False**: openpyxl 셀 단위 편집 (C31-C34 컬럼만), 다른 셀 보존
7. **변경 전후 diff 생성**: 각 변경 항목의 before/after 비율 기록
8. **artifact_hints 생성**: 변경 전후 비교 카드

#### 반환 데이터 구조

```json
{
  "status": "ok",
  "dry_run": false,
  "data": {
    "output_path": "26BP_edited.xlsx",
    "backup_path": ".backup/26BP_20260518_153012.xlsx",
    "updates_applied": 47,
    "changes": [
      {
        "cost_center": "102401",
        "before": {"STB": 35.0, "Mobility": 0.0, "EVCS_domestic": 30.0, "EVCS_overseas": 35.0},
        "after": {"STB": 40.0, "Mobility": 0.0, "EVCS_domestic": 30.0, "EVCS_overseas": 30.0},
        "rows_affected": 12
      }
    ]
  },
  "metadata": {
    "month": 3,
    "validation_violations": 0,
    "schema_version": "2026.05"
  },
  "render_format": "live_artifact",
  "artifact_hints": {
    "type": "diff_cards",
    "title": "26.03 배부율 변경 적용 결과",
    "preferred_chart": "before_after_bar",
    "columns_for_chart": ["cost_center", "STB", "Mobility", "EVCS_domestic", "EVCS_overseas"],
    "comparison_columns": ["before", "after"],
    "pii_redacted": false
  }
}
```

#### 에러 케이스

| 에러 | 코드 | 메시지 |
|---|---|---|
| 파일 미존재 | `FILE_NOT_FOUND` | `"파일을 찾을 수 없습니다: {file_path}"` |
| 파일 잠금 | `FILE_LOCKED` | `"파일이 다른 프로그램에서 열려 있습니다. Excel을 닫고 다시 시도하세요."` |
| 스키마 불일치 | `SCHEMA_MISMATCH` | `"C30-C34 배부율 컬럼이 누락되었습니다. 스키마 v{version} 확인 필요."` |
| 원본 덮어쓰기 시도 | `OVERWRITE_ORIGINAL_FORBIDDEN` | `"output_path가 원본 file_path와 동일합니다. 원본 직접 덮어쓰기는 허용되지 않습니다."` |
| 비율 합 != 100 | `RATE_SUM_NOT_100` | `"배부율 합계가 100%가 아닙니다. cost_center={cc}, 합계={sum}%"` |
| 비율 범위 초과 | `INVALID_RATE` | `"배부율은 0-100 범위여야 합니다. {key}={value}"` |
| CC/배부기준 불일치 | `CC_BASIS_NOT_FOUND` | `"cost_center={cc}, allocation_basis={basis} 일치 행을 찾을 수 없습니다."` |
| 백업 실패 | `BACKUP_FAILED` | `"백업 생성 실패: {reason}. 편집을 중단합니다."` |
| 잘못된 월 | `INVALID_MONTH` | `"month는 1-12 범위여야 합니다. 입력: {month}"` |

#### 토큰/응답 크기 제약

- 변경 결과는 일반적으로 5-15KB
- dry_run 미리보기도 동일 범위

---

### 4.8 `get_exchange_rates` -- 환율 자동 조회

한국수출입은행 환율 API를 자동 조회하여 매매기준율 환율을 반환한다. file #1 Step 3 (수기 편집)의 "환율 update" 작업을 자동화하기 위한 도구.

#### 데이터 출처

- **API**: `https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON`
- **인증**: `.env`의 `EXCHANGE_RATE_API_KEY` (한국수출입은행 Open API 인증키)
- **데이터 유형**: `data=AP01` (매매기준율)
- **응답 형식**: JSON 배열, 통화별 객체

#### 함수 시그니처

```python
@mcp.tool()
async def get_exchange_rates(
    search_date: str | None = None,  # YYYYMMDD, None = 오늘 (KST)
    target_currencies: list[str] | None = None,  # None = 전체
    fallback_to_previous: bool = True,  # 휴일/주말 시 직전 영업일
    render_format: Literal["excel", "live_artifact", "both"] = "excel",
) -> ExchangeRatesResult:
    """한국수출입은행 환율 API 조회.
    Source: https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON
    .env의 EXCHANGE_RATE_API_KEY 사용.
    """
```

#### 입력 파라미터

| 파라미터 | 타입 | 필수 | 검증 룰 | 설명 |
|---|---|---|---|---|
| `search_date` | `str \| None` | N | `YYYYMMDD` 8자리, 미래 날짜 불가, `None` = 오늘 (KST) | 조회 기준일 |
| `target_currencies` | `list[str] \| None` | N | 부록 D 통화 코드 검증 | 조회 대상 통화 (예: `["USD", "EUR", "JPY(100)"]`). `None` = 전체 |
| `fallback_to_previous` | `bool` | N | - | 휴일/주말 빈 응답 시 직전 영업일 자동 재시도 (최대 7일) |
| `render_format` | `Literal` | N | `"excel" \| "live_artifact" \| "both"` | 출력 대상 |

#### 동작 단계

1. **API 키 로드**: `python-dotenv`로 `.env`에서 `EXCHANGE_RATE_API_KEY` 로드
2. **키 검증**: 키 없으면 `API_KEY_MISSING` 에러 즉시 반환
3. **날짜 검증**: `search_date` YYYYMMDD 8자리 형식 확인. `None`이면 오늘 날짜(KST). 미래 날짜 시 `FUTURE_DATE` 에러
4. **API 호출**: `httpx`로 URL 호출 (timeout=10s). `authkey={KEY}&searchdate={date}&data=AP01`
5. **빈 응답 처리** (휴일/주말):
   - `fallback_to_previous=True`: 1일 전 재시도, 최대 7일 반복. 7일 초과 시 `FALLBACK_EXHAUSTED`
   - `fallback_to_previous=False`: `NO_DATA_FOR_DATE` 에러 반환
6. **응답 필터**: `result != 1` 객체 제외 (API 에러 코드)
6.5. **숫자 필드 파싱**: 한국수출입은행 API는 환율 값을 콤마 포함 문자열로 반환 (`"1,393.00"`, `"899.45"`). `deal_bas_r`, `ttb`, `tts`, `bkpr`, `kftc_bkpr`, `kftc_deal_bas_r` 필드를 `str.replace(",", "")` 후 `float()` 변환. 변환 실패 시 `PARSE_ERROR` 에러 (응답 일부 손상)
7. **통화 필터**: `target_currencies` 지정 시 해당 통화만 추출. 미지원 코드 시 `INVALID_CURRENCY`
8. **단위 통화 정규화**: `cur_unit`이 `JPY(100)` 또는 `IDR(100)` 등 100단위 통화인 경우 `unit_multiplier=100` 설정 + `deal_bas_r_per_unit` (1단위당 환율) 추가 필드 생성. 부록 D 참조
9. **캐시**: `{date}_{currencies}` 키로 TTL 12시간 인메모리 캐시. 캐시 히트 시 API 미호출
10. **artifact_hints 생성**: 환율 대시보드 + 통화별 막대 차트
11. **권장 후속 워크플로우**: 환율 적용 시 `write_cells`로 26BP raw `환율` 시트에 셀 단위 적용 후 `verify_sums`로 외화 환산 합계 검증 권장. chained 호출 예시는 Section 11.3 라이브 데모 시나리오 참조

#### 반환 데이터 구조

```json
{
  "status": "ok",
  "data": {
    "search_date": "20260519",
    "actual_date": "20260519",
    "rates": [
      {
        "cur_unit": "USD",
        "cur_nm": "미국 달러",
        "deal_bas_r": 1393.00,
        "ttb": 1378.50,
        "tts": 1407.50,
        "kftc_deal_bas_r": 1393.00
      },
      {
        "cur_unit": "JPY(100)",
        "cur_unit_normalized": "JPY",
        "unit_multiplier": 100,
        "cur_nm": "일본 옌",
        "deal_bas_r": 899.45,
        "deal_bas_r_per_unit": 8.9945,
        "ttb": 890.54,
        "tts": 908.36,
        "kftc_deal_bas_r": 899.45
      }
    ]
  },
  "metadata": {
    "source": "koreaexim.go.kr",
    "data_type": "AP01",
    "fetched_at": "2026-05-19T15:30:00+09:00",
    "cached": false,
    "fallback_used": false,
    "fallback_days_back": 0
  },
  "render_format": "excel",
  "artifact_hints": {
    "type": "rates_dashboard",
    "title": "2026-05-19 매매기준율 환율",
    "preferred_chart": "bar",
    "columns_for_chart": ["cur_unit", "deal_bas_r"],
    "comparison_columns": ["ttb", "deal_bas_r", "tts"]
  }
}
```

#### 에러 케이스

| 에러 | 코드 | 메시지 |
|---|---|---|
| API 키 누락 | `API_KEY_MISSING` | `"EXCHANGE_RATE_API_KEY가 .env에 설정되지 않았습니다."` |
| API 요청 실패 | `API_REQUEST_FAILED` | `"한국수출입은행 API 요청 실패: {status_code} {reason}. timeout={timeout}s"` |
| 잘못된 날짜 형식 | `INVALID_DATE_FORMAT` | `"search_date는 YYYYMMDD 8자리여야 합니다. 입력: {search_date}"` |
| 미래 날짜 | `FUTURE_DATE` | `"미래 날짜는 조회할 수 없습니다. 입력: {search_date}, 오늘: {today}"` |
| 데이터 없음 (fallback 비활성) | `NO_DATA_FOR_DATE` | `"해당 날짜의 환율 데이터가 없습니다 (휴일/주말). fallback_to_previous=True로 재시도하세요."` |
| Fallback 소진 | `FALLBACK_EXHAUSTED` | `"7일 이내 영업일 환율 데이터를 찾을 수 없습니다. 시작일: {search_date}"` |
| API 호출 한도 초과 | `API_RATE_LIMIT` | `"한국수출입은행 API 일일 호출 한도(1,000건)를 초과했습니다."` |
| 미지원 통화 코드 | `INVALID_CURRENCY` | `"지원하지 않는 통화 코드: {code}. 부록 D 통화 코드 목록을 확인하세요."` |

#### Sanity Check (이상치 탐지)

- **전일 대비 ±20% 이내 검증**: 캐시에 전일 데이터가 있으면 각 통화의 `deal_bas_r`가 전일 대비 ±20% 이내인지 확인. 위반 시 `"sanity_warning": true` + 경고 메시지 첨부 (에러는 아님, 데이터는 반환)
- **목적**: API 장애 또는 잘못된 환율 적용 방지 (Pre-mortem S7 연동)

#### 토큰/응답 크기 제약

- 환율 조회 결과는 일반적으로 3-8KB (주요 통화 20-30개 기준)
- 100KB 하드 리밋 이내

---

## 5. 26BP 스키마 매핑

26BP `예산+실적` 시트의 63컬럼을 MCP 도구에서 사용하는 정규화된 키 이름으로 매핑한다.

### 5.1 구조 컬럼 (A-H, 8개)

| 원본 열 | 원본 컬럼명 | 키 이름 | 타입 | 설명 |
|---|---|---|---|---|
| A | 구분 | `division` | `str` | 총합계/사업부/대조직/중조직/소조직 |
| B | Company | `company` | `str` | 회사 코드 (HMX, HUS, HUK, HBR, HSZ) |
| C | 대조직 | `org_l1` | `str` | 대조직명 |
| D | 중조직 | `org_l2` | `str` | 중조직명 |
| E | 소조직 | `org_l3` | `str` | 소조직명 |
| F | Cost Center | `cost_center` | `str` | SAP Cost Center 코드 |
| G | G/L Account | `gl_account` | `str` | SAP G/L 계정 코드 |
| H | G/L Account Name | `gl_account_name` | `str` | 계정 한국어명 |

### 5.2 금액 컬럼 (I-BH, 26개 x 2 = 52개)

26개 기간(1월~12월 당월 + 1월~12월 누계 + 예산 2개)에 대해 각각 예산/실적 쌍.

| 원본 열 범위 | 패턴 | 키 이름 패턴 | 타입 | 설명 |
|---|---|---|---|---|
| I-J | 1월 예산/실적 | `m01_budget` / `m01_actual` | `float` | 1월 당월 예산/실적 |
| K-L | 2월 예산/실적 | `m02_budget` / `m02_actual` | `float` | 2월 당월 예산/실적 |
| ... | ... | ... | ... | ... |
| AG-AH | 12월 예산/실적 | `m12_budget` / `m12_actual` | `float` | 12월 당월 예산/실적 |
| AI-AJ | 1월 누계 예산/실적 | `cum01_budget` / `cum01_actual` | `float` | 1월 누계 |
| ... | ... | ... | ... | ... |
| BG-BH | 연간 예산/실적 | `annual_budget` / `annual_actual` | `float` | 연간 합계 |

### 5.3 텍스트/참조 컬럼 (BI-BK, 3개)

| 원본 열 | 원본 컬럼명 | 키 이름 | 타입 | 설명 |
|---|---|---|---|---|
| BI (C25) | Text(적요) | `text_summary` | `str` | 적요 텍스트 (60% 채움) |
| BJ (C29) | 비고 | `remark` | `str` | 실무자 코멘트 (4% 채움) |
| BK (C30) | 배부기준 | `allocation_basis` | `str` | 배부 기준 |

> **참고**: C31~C34 (배부율 4개: STB/Mobility/EVCS국내/해외)는 v0.1에서 `get_allocation_rates` (Section 4.6) 및 `update_allocation_rates` (Section 4.7) 도구로 조회/변경을 지원한다.

### 5.4 기본 25컬럼 (extract_filtered 기본값)

`columns` 파라미터 미지정 시 반환되는 기본 컬럼:

```python
DEFAULT_COLUMNS = [
    "division", "company", "org_l1", "org_l2", "org_l3",
    "cost_center", "gl_account", "gl_account_name",
    # 당월 (최근 3개월만)
    "m01_budget", "m01_actual",  # 동적으로 최근 3개월로 변경
    "m02_budget", "m02_actual",
    "m03_budget", "m03_actual",
    # 누계
    "cum_budget", "cum_actual",
    # 연간
    "annual_budget", "annual_actual",
    # 텍스트
    "text_summary", "remark", "allocation_basis",
]
```

### 5.5 스키마 유지보수 및 버전 관리

| 항목 | 정책 |
|---|---|
| **스키마 버전** | `schemas/bp26.py` 상단에 `SCHEMA_VERSION = "2026.05"` 명시. 컬럼 변경 시 버전 갱신 |
| **유지보수 책임** | 26BP 컬럼 구조 변경 시 `bp26.py` 갱신 책임: 실무 담당자 (Humax 측) + 컨설턴트 hypercare 기간 1-3개월 |
| **헤더 검증** | 파일 로딩 시 실 파일 헤더 vs `bp26.py` 스키마 비교. 불일치 시 `SCHEMA_MISMATCH` 에러: `"파일 헤더가 스키마 v{version}과 일치하지 않습니다. 변경된 컬럼: {diff}. schemas/bp26.py를 업데이트하세요."` |
| **검증 주기** | 매월 결산 첫 작업으로 schema verify 권장 (새 26BP 파일 수령 시) |
| **변경 이력** | `bp26.py` 내 `CHANGELOG` 딕셔너리에 버전별 변경 사항 기록 |

> **주의**: 26BP 컬럼 구조는 SAP/재무기획 부서의 결정에 따라 변경될 수 있다. 스키마 불일치가 발생하면 MCP 도구가 잘못된 컬럼을 참조하여 조용히 오답을 반환할 수 있으므로, 헤더 검증은 모든 도구의 파일 로딩 첫 단계에서 수행한다.

---

## 6. 안전 및 거버넌스

### 6.1 백업 정책

| 항목 | 정책 |
|---|---|
| **자동 백업** | `write_cells` 및 `update_allocation_rates` 실행 전 `.backup/` 디렉터리에 타임스탬프 파일 자동 생성. **항상 활성화 (비활성화 불가, API에 노출하지 않음)** |
| **백업 실패 시** | 편집 중단. `BACKUP_FAILED` 에러 반환. 원본 무수정 보장 |
| **백업 보관** | 최근 10회분 보관. 초과 시 가장 오래된 백업 삭제 (설정 가능) |
| **백업 경로** | `{원본_디렉터리}/.backup/{원본명}_{YYYYMMDD_HHMMSS}.xlsx` |
| **복구** | 수동 복구 (백업 파일을 원본 위치로 복사). v0.2에서 `restore` 도구 추가 예정 |

### 6.2 Dry-run 모드

`write_cells`의 `dry_run=True` 파라미터로 실제 파일 수정 없이 편집 결과를 미리 확인:

- 수식 셀 보호 경고 확인
- 편집 대상 셀의 이전/이후 값 미리보기
- 병합 셀 경고 확인
- 총 편집 수 확인

**권장 운영 패턴**: 항상 `dry_run=True`로 먼저 실행 → 결과 확인 → `dry_run=False`로 실행

### 6.3 감사 로그

모든 도구 호출은 구조화된 JSON 로그로 기록:

```python
# 로그 구조
{
    "timestamp": "2026-03-19T14:30:22+09:00",
    "tool": "write_cells",
    "user": "system",           # MCP 서버 레벨 (Claude Desktop 사용자 식별은 v0.3)
    "file_path": "/path/to/file.xlsx",
    "sheet_name": "3월",
    "action_summary": {
        "total_updates": 150,
        "applied": 145,
        "skipped": 5
    },
    "backup_path": "/path/to/.backup/file_20260319_143022.xlsx",
    "dry_run": false,
    "duration_ms": 2340,
    "success": true,
    "error": null
}
```

**로그 경로**: `.humax-mcp/audit/audit_{YYYYMMDD}.jsonl` (일별 로테이션)

#### 감사 로그 접근 제어 및 보관 정책

| 항목 | 정책 |
|---|---|
| **저장 경로** | `.humax-mcp/audit/audit_{YYYYMMDD}.jsonl` (프로젝트 루트 하위) |
| **접근 권한** | 파일 시스템 권한 기반. 실무자 본인만 read/write (`chmod 600`) |
| **보관 기간** | 12개월. 이후 자동 삭제 또는 사내 정보보호 정책에 따라 보관 연장/이관 |
| **PII 포함 가능성** | 로그에 파일 경로(인명 포함 가능), 액션 요약(사업부명/계정명 등) 포함 가능. PII가 포함된 로그로 취급 |
| **외부 공유 금지** | 감사 로그를 Slack, 이메일, 클라우드 드라이브에 첨부하여 공유하지 않음 |
| **사고 시 분석** | 데이터 손상/오류 발생 시 로그 분석 권한자: 정보보호팀 또는 해당 부서장 위임자 |
| **자동 정리** | 12개월 경과 로그는 서버 시작 시 자동 삭제 (설정 가능: `AUDIT_RETENTION_MONTHS=12`) |

### 6.4 외부 전송 거버넌스 Hook

MCP 도구는 로컬에서 실행되므로 SAP 데이터가 외부 API로 전송되지 않는다. 단, `extract_filtered`의 반환 데이터는 Claude Desktop 컨텍스트에 포함되어 Anthropic API로 전송될 수 있다.

**거버넌스 체크포인트:**

| 체크 | 설명 | 구현 |
|---|---|---|
| **PII 필터** | 적요(text_summary) 내 인명/사번 패턴 탐지 시 경고 | `token_guard.py`에서 정규식 검사 |
| **금액 마스킹 옵션** | `extract_filtered`에 `mask_amounts=True` 옵션 (v0.2) | 금액을 상대값(예산 대비 %)으로 변환 |
| **데이터 분류 표시** | 반환 JSON에 `data_classification: "INTERNAL"` 필드 포함 | 모든 응답에 자동 첨부 |
| **전송 경고** | 적요 컬럼 포함 시 `"warning": "적요 데이터가 포함되어 있습니다. 사내 전송 정책을 확인하세요."` | `extract_filtered` 반환 시 자동 |
| **외부 API 호출** | `get_exchange_rates`는 한국수출입은행 공공 데이터 API 호출 (SAP 데이터 미전송). PII 무관, 거버넌스 부담 0 | `oapi.koreaexim.go.kr` 사내 방화벽 허용 필요 (IT 사전 확인). API 키만 전송, 사내 데이터 미포함 |

**Phase 0 거버넌스 게이트와 연동:**

- 정보보호팀 승인 전: 합성/마스킹 데이터만 사용
- 마스킹 필수 결정 시: `extract_filtered`에 마스킹 옵션 자동 활성화
- 외부 전송 전면 금지 시: MCP 도구 반환 데이터를 로컬 파일로만 출력 (Claude 컨텍스트 미포함 모드)

---

## 7. 테스트 Plan

### 7.1 Unit 테스트

| 대상 | 파일 | 테스트 케이스 | 통과 기준 |
|---|---|---|---|
| extract: 필터 조합 | `test_extract.py` | 월 필터, 회사 필터, 컬럼 필터, 복합 필터, 빈 결과 | 각 필터 조건에 맞는 행/열만 반환 |
| extract: 토큰 가드 | `test_extract.py` | max_rows 초과, 100KB 초과 자동 축소 | 하드 리밋 이내로 잘림 + truncated 플래그 |
| extract: 출력 형식 | `test_extract.py` | JSON, CSV, Markdown 각각 | 파싱 가능한 유효 형식 |
| verify: 합계 검증 | `test_verify.py` | 정상 합계, 불일치 합계, 허용 오차 경계 | PASS/FAIL 정확 판정 |
| verify: 이상치 탐지 | `test_verify.py` | |10백만| 이상/미만 경계 케이스 | 임계값 기준 정확 필터링 |
| verify: 수식 검증 | `test_verify.py` | 수식 셀 정상, 수식 → 값 덮어쓰기 감지 | 경고 정확 발생 |
| write: 셀 편집 | `test_write.py` | 숫자/문자열/날짜 편집, 빈 셀 채우기 | 편집 값 정확 + 서식 보존 |
| write: 수식 보호 | `test_write.py` | skip_if_formula=True/False | 수식 셀 건너뜀/덮어쓰기 + 경고 |
| write: 백업 | `test_write.py` | 백업 생성, 백업 실패 시 중단 | 백업 파일 존재 + 편집 중단 |
| write: dry-run | `test_write.py` | dry_run=True 시 파일 무변경 | 원본 해시 동일 |
| write: 원본 덮어쓰기 차단 | `test_write.py` | output_path == file_path | `OVERWRITE_ORIGINAL_FORBIDDEN` 에러 |
| write: 파일 잠금 | `test_write.py` | xlsx가 Excel에서 열려있음 (Windows lock) | `FILE_LOCKED` 에러 |
| write: 스키마 불일치 | `test_write.py` | 시트 헤더 schema_version 다름 | `SCHEMA_MISMATCH` 에러 |
| diff: 변동 추출 | `test_diff.py` | 정상 변동, 임계값 경계, 빈 데이터 | 임계값 기준 정확 필터링 |
| diff: 코멘트 초안 | `test_diff.py` | 코멘트 패턴 정합성 | `[코드] [계정명] [+/-금액]` 형식 |
| alloc_get: 필터 조합 | `test_allocation_get.py` | 월 필터, 회사 필터, CC 필터, 복합 필터, 빈 결과 | 각 필터 조건에 맞는 배부율 행만 반환 |
| alloc_get: 합계 검증 | `test_allocation_get.py` | 4개 비율 합 = 100%, 위반 행 탐지, 경계 케이스 | `rate_sum_ok` 플래그 정확 + `rate_sum_violations` 카운트 |
| alloc_get: 그룹화 | `test_allocation_get.py` | 동일 비율 조합 그룹화, unique_rates_count | 그룹 수 정확 + row_count 합계 = 전체 행 |
| alloc_set: dry-run | `test_allocation_set.py` | dry_run=True 시 파일 무변경 | 원본 해시 동일 + 변경 미리보기 정확 |
| alloc_set: RATE_SUM 검증 | `test_allocation_set.py` | 합계 99%, 101%, 100% 경계 | 합계 != 100 시 `RATE_SUM_NOT_100` 에러 |
| alloc_set: output_path 검증 | `test_allocation_set.py` | output_path == file_path | `OVERWRITE_ORIGINAL_FORBIDDEN` 에러 |
| alloc_set: 셀 편집 | `test_allocation_set.py` | C31-C34만 편집, 다른 셀 보존 | 편집 값 정확 + 비대상 셀 무변경 |
| alloc_set: 백업 | `test_allocation_set.py` | 백업 생성, 백업 실패 시 중단 | 백업 파일 존재 + 편집 중단 |
| alloc_set: CC_BASIS 불일치 | `test_allocation_set.py` | 존재하지 않는 CC/배부기준 조합 | `CC_BASIS_NOT_FOUND` 에러 |
| exchange: API 성공 | `test_exchange.py` | 정상 날짜 + 전체 통화 조회 | 응답 `status: "ok"` + rates 배열 비어있지 않음 |
| exchange: 휴일 fallback | `test_exchange.py` | 주말/휴일 날짜 + `fallback_to_previous=True` | `actual_date`가 `search_date`보다 이전 + `fallback_used: true` |
| exchange: 타임아웃 | `test_exchange.py` | API 타임아웃 mock | `API_REQUEST_FAILED` 에러 |
| exchange: 키 누락 | `test_exchange.py` | `EXCHANGE_RATE_API_KEY` 미설정 | `API_KEY_MISSING` 에러 |
| exchange: JPY 정규화 | `test_exchange.py` | JPY(100) 포함 응답 | `deal_bas_r_per_unit` = `deal_bas_r / 100` + `unit_multiplier: 100` |
| exchange: 통화 필터 | `test_exchange.py` | `target_currencies=["USD", "EUR"]` | 2개 통화만 반환 |
| exchange: 미래 날짜 | `test_exchange.py` | 내일 날짜 | `FUTURE_DATE` 에러 |
| exchange: 캐시 히트 | `test_exchange.py` | 동일 날짜+통화 2회 연속 호출 | 2회차 `cached: true` + API 미호출 |
| exchange: sanity check | `test_exchange.py` | 전일 대비 ±20% 초과 mock | `sanity_warning: true` + 경고 메시지 |

### 7.2 Integration 테스트

| 대상 | 파일 | 테스트 케이스 | 통과 기준 |
|---|---|---|---|
| MCP 서버 기동 | `test_mcp_server.py` | FastMCP 앱 시작 → 7개 도구 노출 확인 | `mcp.list_tools()` 에 7개 도구 포함 |
| Tool invocation | `test_mcp_server.py` | MCP 프로토콜로 각 도구 호출 | 정상 응답 반환 |
| 백업 + 편집 + 검증 체인 | `test_backup.py` | write_cells → verify_sums 순차 호출 | 편집 후 검증 통과 |
| 동시 접근 | `test_mcp_server.py` | 같은 파일에 대해 2개 도구 동시 호출 | 파일 잠금 또는 순차 처리로 충돌 방지 |
| 배부율 조회→변경 체인 | `test_allocation_chain.py` | get_allocation_rates → update_allocation_rates 순차 호출 | 조회 결과 기반 변경 + 변경 후 재조회 일치 |
| 배부율 변경→검증 체인 | `test_allocation_chain.py` | update_allocation_rates → verify_sums 순차 호출 | 배부율 변경 후 합계 검증 통과 |
| 환율 API mock | `test_exchange_integration.py` | httpx mock으로 API 성공/실패/빈 응답 시뮬레이션 | 정상 응답 파싱 + 에러 핸들링 정확 |
| 환율 캐시 동작 | `test_exchange_integration.py` | 동일 키 2회 호출 → 캐시 히트 확인. TTL 만료 후 재호출 | `cached: true/false` 정확 + API 호출 횟수 검증 |

### 7.3 E2E 테스트

| 대상 | 파일 | 테스트 케이스 | 통과 기준 |
|---|---|---|---|
| 월 결산 시뮬레이션 | `test_monthly_close.py` | 합성 26BP → extract → verify → write → diff 4단계 체인 | known-good fixture와 셀 단위 비교, 불일치 0건 |
| 대용량 데이터 | `test_monthly_close.py` | 15,007행 × 63열 합성 데이터로 전체 파이프라인 | 5분 이내 완료 + 정확 결과 |
| 배부율 조회/변경 시나리오 | `test_monthly_close.py` | 합성 26BP → get_allocation_rates → update_allocation_rates(dry_run) → update_allocation_rates → get_allocation_rates(변경 확인) → verify_sums | 변경 전후 비율 정확 + 합계 100% + 결산 합계 일치 |

### 7.4 Observability

| 항목 | 구현 | 확인 방법 |
|---|---|---|
| 감사 로그 | 모든 도구 호출 시 JSONL 로그 기록 | 로그 파일 존재 + 파싱 가능 |
| 에러 로그 | 예외 발생 시 스택 트레이스 포함 | 에러 재현 → 로그에서 원인 추적 가능 |
| 성능 메트릭 | 각 도구 실행 시간 기록 | 로그의 `duration_ms` 필드 |
| 토큰 사용량 | `extract_filtered` 반환 시 `estimated_tokens` 포함 | 메타데이터 필드 확인 |

---

## 8. Pre-mortem (7 시나리오)

### S1: write_cells가 원본 파일 깨짐 (백업 실패)

| 항목 | 내용 |
|---|---|
| **시나리오** | write_cells 실행 중 디스크 공간 부족 또는 파일 시스템 오류로 백업 생성 실패. 그럼에도 편집이 진행되어 원본 파일이 손상됨 |
| **확률** | 낮음 (아래 3중 안전장치로 확률 대폭 감소) |
| **영향** | 에러 #1(원본 훼손)을 해결하려다 오히려 악화. 실무자 신뢰 붕괴 |
| **예방** | (1) **백업은 항상 실행 (API에 비활성화 파라미터 없음)** — `create_backup` 파라미터를 public API에서 제거하여 자연어로도 우회 불가. (2) 백업 성공 확인 = 파일 존재 + 크기 > 0 + 해시 비교. 실패 시 편집 절대 불가 (코드 레벨 보장). (3) **`output_path != file_path` 서버 측 검증** — 원본과 동일 경로 지정 시 `OVERWRITE_ORIGINAL_FORBIDDEN` 에러 즉시 반환. `output_path=None`이면 자동으로 `_edited` 접미사 경로 사용. 원본 직접 덮어쓰기는 구조적으로 불가능 |
| **탐지** | 백업 실패 시 `BACKUP_FAILED` 에러 즉시 반환 + 감사 로그 기록. 원본 덮어쓰기 시도 시 `OVERWRITE_ORIGINAL_FORBIDDEN` 에러 |
| **복구** | `.backup/` 디렉터리의 최신 백업에서 복구. v0.2에서 `restore` 도구 추가 |

### S2: 토큰 응답 200K 초과 (필터 부적절)

| 항목 | 내용 |
|---|---|
| **시나리오** | extract_filtered에서 필터 조건 없이 전체 시트 추출 요청. 15,007행 × 63열 = 약 3-5M 토큰 분량이 Claude 컨텍스트로 전달되어 컨텍스트 초과 또는 요금 폭발 |
| **확률** | 높음 (실무자가 자연어로 "전체 데이터 보여줘"라고 요청 가능) |
| **영향** | Claude Desktop 세션 중단. 사용량 빠르게 소진 (에러 #4 재현) |
| **예방** | (1) `max_rows` 기본값 500행 강제. (2) 직렬화 결과 100KB 하드 리밋 — 초과 시 자동 축소 후 재직렬화. (3) `estimated_tokens` 메타데이터로 사전 경고. (4) 필터 0개 + max_rows > 1000 조합 시 확인 프롬프트 강제 |
| **탐지** | `token_guard.py`에서 직렬화 크기 실시간 측정 → 소프트 리밋(50KB) 경고, 하드 리밋(100KB) 차단 |
| **복구** | 자동 축소 후 재시도. 사용자에게 필터 조건 추가 권장 메시지 |

### S3: 적요/PII 외부 전송 거버넌스 위반

| 항목 | 내용 |
|---|---|
| **시나리오** | extract_filtered 결과에 적요(text_summary) 컬럼이 포함되고, 해당 적요에 거래처 담당자 성명, 사번 등 PII가 포함된 채로 Claude Desktop → Anthropic API로 전송됨. 사내 정보보호 정책 위반 |
| **확률** | 높음 (적요 60% 채움. PII 포함 여부 미확인 상태) |
| **영향** | 정보보호팀 감사 적발 시 MCP 서버 사용 중단 명령. Phase 2 전체 지연 |
| **예방** | (1) 적요 컬럼 포함 시 자동 경고 메시지 첨부. (2) PII 패턴(인명, 사번, 전화번호) 정규식 탐지 → 해당 행 마스킹 또는 제외. (3) Phase 0 거버넌스 게이트 통과 전까지 적요 컬럼 기본 제외 설정. (4) `data_classification` 필드를 모든 응답에 자동 첨부하여 감사 추적 가능 |
| **탐지** | `token_guard.py`의 PII 정규식 스캔 → 탐지 시 `"pii_detected": true` 플래그 + 경고 |
| **복구** | PII 탐지된 응답은 Claude 컨텍스트에서 자동 제거 불가 (이미 전송됨). Anthropic Zero Data Retention 옵션 확인 필요. 사후 대응으로 감사 로그 제출 |

### S4: Anthropic API 신뢰 경계 — 입력 데이터 외부 경유

| 항목 | 내용 |
|---|---|
| **시나리오** | 실무자 자연어 호출 → Claude Desktop → Anthropic API → 응답 경로에서, MCP 도구 인자(파일 경로, 필터 조건)와 `extract_filtered` 반환 데이터가 Anthropic 서버를 경유함. DPA(Data Processing Agreement) / ZDR(Zero Data Retention) 상태에 따라 데이터가 학습/저장될 가능성 |
| **확률** | 확정 (아키텍처 상 반드시 발생. 위험 수준은 DPA/ZDR 계약 상태에 의존) |
| **영향** | SAP 재무 데이터가 외부 서버에 전송/저장됨. 사내 정보보호 정책 위반 가능. 정보보호팀 감사 시 MCP 사용 중단 명령 |
| **예방** | (1) `open-questions.md`의 DPA/ZDR 확인을 **Phase 0 거버넌스 게이트 필수 항목**으로 명시 — DPA/ZDR 미확인 시 합성 데이터만 사용. (2) PII regex 필터를 도구 호출 반환 전에 사전 적용 (`token_guard.py`). (3) 사내 정보보호 정책에 따라 적요/인명/사번 마스킹 또는 익명화. (4) `data_classification: "INTERNAL"` 필드를 모든 응답에 자동 첨부 |
| **탐지** | 감사 로그에 모든 도구 호출 + 반환 데이터 크기 기록. PII 탐지 시 `pii_detected: true` 플래그 |
| **복구** | 이미 전송된 데이터는 Anthropic 측 ZDR 정책에 의존. 사후 대응: 감사 로그 제출 + Anthropic에 데이터 삭제 요청 (ZDR 적용 시 자동 삭제) |

### S5: Live Artifact 캡처/공유로 PII 유출

| 항목 | 내용 |
|---|---|
| **시나리오** | 실무자가 Live Artifact로 렌더링된 배부율/인건비 데이터를 스크린샷 캡처하여 Slack/이메일로 외부 공유. 적요에 포함된 인명/사번 등 PII가 유출됨 |
| **확률** | 중간 (Live Artifact의 시각적 편의성이 공유 욕구를 높임) |
| **영향** | 사내 정보보호 정책 위반. 정보보호팀 감사 시 Live Artifact 기능 사용 중단 명령 가능 |
| **예방** | (1) `artifact_hints.pii_redacted: bool` 플래그로 PII 마스킹 적용 여부 명시. (2) PII 포함 artifact에 `"이 데이터는 사내 전용입니다. 외부 공유를 금지합니다."` 워터마크 안내 자동 첨부. (3) `token_guard.py` PII regex 스캔을 artifact 데이터에도 동일 적용. (4) Section 6.4 거버넌스 정책과 연동 |
| **탐지** | 감사 로그에 `render_format` 및 `pii_redacted` 필드 기록. PII 탐지 시 `pii_detected: true` 플래그 |
| **복구** | 이미 캡처/공유된 스크린샷은 회수 불가. 사후 대응으로 외부 공유 금지 교육 + 감사 로그 기반 사용 이력 제출 |

### S6: 배부율 변경 시 합계 100% 위반으로 결산 결과 오류

| 항목 | 내용 |
|---|---|
| **시나리오** | `update_allocation_rates`로 배부율 변경 시 4개 사업부 비율 합이 100%가 아닌 채로 적용됨. 해당 월 결산에서 배부 금액이 맞지 않아 전체 결산 결과 오류 발생 |
| **확률** | 낮음 (아래 3중 안전장치로 확률 대폭 감소) |
| **영향** | 결산 마감 지연. 배부 오류 원인 추적에 1-2일 소요. 실무자 신뢰 붕괴 |
| **예방** | (1) `RATE_SUM_NOT_100` 사전 차단 — updates 각 항목의 4개 비율 합 != 100 시 즉시 에러 반환, 편집 불가. (2) `dry_run=True` 권장 운영 패턴 — 변경 전 미리보기로 비율 합 확인. (3) 변경 후 `verify_sums` 호출 권장 — 배부율 변경이 합계에 미치는 영향 검증. (4) `get_allocation_rates`의 `rate_sum_violations` 메타데이터로 기존 위반 사전 탐지 |
| **탐지** | `update_allocation_rates` 입력 검증 단계에서 즉시 차단. 감사 로그에 검증 결과 기록 |
| **복구** | dry_run으로 사전 차단이 기본. 적용 후 발견 시 `.backup/` 최신 백업에서 복구 |

### S7: 환율 API 장애 또는 잘못된 환율 적용

| 항목 | 내용 |
|---|---|
| **시나리오** | `get_exchange_rates` 조회 시 한국수출입은행 API 장애, 잘못된 환율 반환, 또는 휴일 fallback으로 오래된 환율이 적용됨. 외화 환산 금액이 틀어져 결산 결과 오류 발생 |
| **확률** | 낮음 (API 안정성 높으나, 연휴/시스템 점검 시 일시 장애 가능) |
| **영향** | 외화 환산 오류 → 해외 법인(HUS, HUK, HBR, HSZ) 결산 금액 불일치. 원인 추적에 반나절 소요 |
| **예방** | (1) **Sanity check**: 전일 대비 ±20% 이내 검증. 위반 시 `sanity_warning: true` 경고 (데이터는 반환하되 주의 환기). (2) **Fallback 캐시**: TTL 12시간 인메모리 캐시로 API 장애 시 최근 캐시 데이터 반환. (3) **휴일 처리**: `fallback_to_previous=True` 기본값으로 최대 7일 전 영업일 데이터 자동 조회. (4) **감사 로그**: 조회 날짜 + 통화 + 환율값 + source(API/캐시) 기록 → 적용 후 `verify_sums` 권장 |
| **탐지** | 감사 로그에 `actual_date`, `cached`, `fallback_used`, `sanity_warning` 필드 기록. sanity check 위반 시 경고 메시지 |
| **복구** | 자동 백업에서 롤백 + 올바른 환율로 재적용. 수기 환율 입력 fallback (기존 워크플로우로 복귀 가능) |

---

## 9. Claude Desktop 등록 가이드

### 9.1 사전 준비

```bash
# Python 3.10+ 확인
python3 --version

# 프로젝트 클론 또는 다운로드
cd ~/humax-excel-mcp

# 의존성 설치
pip install -e .
# 또는
pip install mcp openpyxl pandas pydantic python-dotenv
```

### 9.2 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 편집
# HUMAX_DATA_DIR=/path/to/26bp/files    # 26BP 파일이 있는 디렉터리
# BACKUP_RETENTION=10                     # 백업 보관 수
# LOG_DIR=./logs                          # 감사 로그 디렉터리
# TOKEN_HARD_LIMIT_KB=100                 # 토큰 하드 리밋 (KB)
# EXCHANGE_RATE_API_KEY=                  # 한국수출입은행 Open API 인증키 (https://www.koreaexim.go.kr/ir/HPHKIR020M01?apino=2)
```

### 9.3 Claude Desktop 설정

Claude Desktop의 `claude_desktop_config.json` (Settings > Developer > Edit Config)에 아래 추가:

```json
{
  "mcpServers": {
    "humax-excel-mcp": {
      "command": "python3",
      "args": ["-m", "humax_excel_mcp.server"],
      "cwd": "/Users/{username}/humax-excel-mcp",
      "env": {
        "HUMAX_DATA_DIR": "/path/to/26bp/files"
      }
    }
  }
}
```

> **Windows 경로 주의**: Windows에서는 `"command": "python"`, 경로 구분자 `\\` 사용.

### 9.4 동작 확인

Claude Desktop 재시작 후, 대화창에서:

```
"26BP 3월 raw에서 본사 인건비만 추출해줘"
```

Claude가 `extract_filtered` 도구를 자동 호출하여 결과를 반환하면 정상.

### 9.5 사내 배포 전략 — GitHub Private Repo 기반

**확정 사항**: 사내 IT가 GitHub 허용. **Private repo** 사용. 모든 배포/업데이트는 `git pull` 기반.

#### 9.5.1 저장소 구조

| 항목 | 설명 |
|---|---|
| 호스팅 | GitHub Private Repo (사내 Org 또는 강사 개인 계정 + Humax 멤버 read/write) |
| Repo 명 | `humax-excel-mcp` (또는 사내 명명 규칙 적용) |
| 접근 권한 | 강사: admin / 실무자: write (PR 머지 권한은 강사) / 부서 전파 시 read-only 추가 |
| 브랜치 전략 | `main` (안정) / `dev` (통합) / `feature/*` (작업 단위) |
| 태그 | `v0.1.0`, `v0.2.0` 등 SemVer 적용 |

#### 9.5.2 보안 정책 (.gitignore 강제)

GitHub Private이라도 **사내 데이터/PII는 절대 push 금지**.

```gitignore
# Humax raw 데이터 (절대 금지)
*.xlsx
*.csv
*.jsonl
docs/rfp/

# 환경 변수 (API 키, 사내 정보)
# EXCHANGE_RATE_API_KEY 포함 — 절대 push 금지
.env
.env.local

# 백업/감사 로그 (PII 가능성)
.backup/
audit/
.humax-mcp/

# 사내 사전 (배부율, CC 마스터)
humax_config/allocation/*.json
humax_config/cc_master.json

# Python
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/

# IDE
.vscode/
.idea/
```

**push 전 사전 점검**: `git status` + `git diff --cached` 필수 확인. CI에서 PII 정규식 스캔 (선택).

#### 9.5.3 Humax-Specific 자산 분리

| 자산 | 위치 |
|---|---|
| 일반 MCP 코드 (도구 7종, 서버, 테스트) | 메인 repo (push OK) |
| 26BP 스키마 (`bp26.py`) | 메인 repo (컬럼 구조는 공개 가능 수준) |
| 배부율 마스터 (월별) | `.env` 또는 별도 Private subrepo (Git submodule) |
| CC 마스터 (한국어 부서명) | `.gitignore` 제외 / `humax_config/.local` 디렉터리 |
| 실 Excel raw 파일 | **절대 push 금지** |

#### 9.5.4 초기 설치 (`scripts/install.ps1` Windows)

```powershell
# scripts/install.ps1
# 사전: Git for Windows, Python 3.10+ 설치 완료

# 1. Repo clone
git clone https://github.com/<humax-org>/humax-excel-mcp.git
cd humax-excel-mcp

# 2. 가상환경
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. 의존성
pip install -e .

# 4. .env 생성 (사내 정보 입력)
Copy-Item .env.example .env
Write-Host "==> .env 파일을 편집하여 배부율/CC 마스터 경로 및 EXCHANGE_RATE_API_KEY를 입력하세요"

# 5. Claude Desktop config 자동 등록
$configPath = "$env:APPDATA\Claude\claude_desktop_config.json"
$repoPath = (Get-Location).Path
# JSON 파싱 + humax-excel-mcp MCP 서버 항목 추가 (mcpServers.humax-excel)
# (실제 구현은 jq 또는 PowerShell ConvertFrom-Json/ConvertTo-Json)

Write-Host "==> 설치 완료. Claude Desktop을 재시작하세요"
```

리눅스/macOS는 `scripts/install.sh` 동등 스크립트 제공.

#### 9.5.5 업데이트 (`scripts/update.ps1`)

```powershell
# scripts/update.ps1
Set-Location $PSScriptRoot\..

# 1. 로컬 변경사항 stash (실무자 임시 변경 보존)
git stash --include-untracked

# 2. 최신 가져오기
git fetch origin
git pull origin main

# 3. 의존성 업데이트
.venv\Scripts\Activate.ps1
pip install -e . --upgrade

# 4. 마이그레이션 스크립트 (필요 시)
if (Test-Path "scripts\migrate.ps1") {
    & scripts\migrate.ps1
}

# 5. 변경 사항 안내
Write-Host "==> 업데이트 완료. Claude Desktop을 재시작하세요"
git log --oneline -5
```

실무자: PowerShell 1줄 (`.\scripts\update.ps1`).

#### 9.5.6 개발자 워크플로우 (강사 또는 실무 개발자)

```bash
# 1. feature 브랜치
git checkout -b feature/sap-export-improve

# 2. 코드 수정 + 테스트
pytest tests/

# 3. 커밋 + push
git add src/
git commit -m "feat: improve sap export performance"
git push origin feature/sap-export-improve

# 4. GitHub Web UI에서 PR 생성 → 리뷰 → main 머지

# 5. 태그 (안정 릴리스 시)
git checkout main
git pull
git tag v0.2.0
git push --tags
```

#### 9.5.7 GitHub Actions CI (`.github/workflows/test.yml`)

```yaml
name: tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.10' }
      - run: pip install -e ".[test]"
      - run: pytest tests/ --cov=src
      - run: |
          # PII 정규식 스캔 (선택)
          ! grep -rE '(주민등록번호|RRN|\\d{6}-\\d{7})' src/ tests/ docs/
```

머지 전 자동 검증. CI 실패 시 머지 차단.

#### 9.5.8 운영 모델 (단계별)

| 단계 | 배포 모델 | 관리 |
|---|---|---|
| **Phase 1 (강의 + 컨설팅)** | stdio 로컬 / 각 PC `git clone` + `install.ps1` | 강사가 push, 실무자가 pull |
| **Phase 2 (실무자 자력 운영)** | 동일 / 실무자도 GitHub write 권한 | 실무자 PR 강사 리뷰 (hypercare 1-3개월) |
| **Phase 3 (부서 확대)** | 옵션 분기 (아래 참조) | 부서장 또는 사내 IT 일부 위임 |

#### 9.5.9 Phase 3 배포 옵션 (부서 확대 시)

기본 권장은 **stdio + git pull 유지**. 부서 규모에 따라 선택:

| 옵션 | 적합 규모 | 인프라 |
|---|---|---|
| **stdio + git pull** (권장 1순위) | 1-15명 | 각 PC clone, 코드 변경 시 `update.ps1` |
| **실무자 PC 1대 서버화 (HTTP/SSE)** | 5-15명 | 1대만 포트 열기, 나머지 PC는 `config.json`만 |
| **사내 서버 1대 (HTTP/SSE)** | 15명+ | 사내 Linux/Windows 서버, IT팀 운영 |

> **stdio → HTTP/SSE 전환 비용**: 서버 코드 `mcp.run()` → `mcp.run_sse(...)` 1줄. 도구 코드는 변경 없음. 인프라 결정만 필요.

#### 9.5.10 사전 점검 (배포 전 IT 협의)

| 항목 | 확인 |
|---|---|
| 사내 GitHub 접근 허용 (외부 또는 사내 Org) | ✅ 확정 |
| Private repo 정책 (사내 Org 권장) | 사내 IT 결정 |
| Python 3.10+ 실행 권한 | 표준 이미지 포함 또는 개별 설치 승인 |
| Claude Desktop `config.json` 편집 권한 | `%APPDATA%\Claude\` 쓰기 권한 |
| Anthropic API 외부 호출 정책 (Claude Desktop 내장) | DPA/ZDR 확인 (open-questions 참조) |
| 외부 API 방화벽 허용 (`oapi.koreaexim.go.kr`) | `get_exchange_rates` 호출 위해 IT 사전 확인 (공공 데이터, PII 무관) |
| 사내 데이터 git push 금지 | `.gitignore` + CI 정규식 스캔 |
| 사고 발생 시 책임 소재 | SOW에 명시 (강사 hypercare vs 실무자 자력) |

---

## 10. 확장 로드맵

### v0.1 (MVP, 현재 설계)

- 7개 핵심 도구: `extract_filtered`, `verify_sums`, `write_cells`, `generate_diff_candidates`, `get_allocation_rates`, `update_allocation_rates`, `get_exchange_rates`
- 26BP `예산+실적` 시트 대상
- 로컬 실행 (Claude Desktop stdio 연결)
- 자동 백업 + dry-run + 감사 로그
- 합성 데이터 기반 테스트
- Live Artifact 출력 옵션 (`render_format` + `artifact_hints`) 전 도구 지원

### v0.2 (적요 활용 + 고급 배부)

- `classify_by_text`: 적요 기반 계정 자동 분류 (적요 PoC H1/H2/H3 통과 시)
- `allocate_costs`: 배부율 마스터 기반 건별 배부 자동화 (v0.1의 배부율 조회/변경 기반 확장)
- `restore_backup`: 백업에서 원본 복구 도구
- PII 마스킹 옵션 (`mask_pii=True`) 내장
- 금액 마스킹 옵션 (`mask_amounts=True`)
- CC 마스터 시트 연동 (Description 77% 활용)

### v0.3 (SAP 연동)

- SAP GUI Scripting 래퍼: FBL3N 자동 추출 → MCP 도구로 노출
- SAP OData/RFC 연동 (SAP Basis 권한 확보 시)
- 사용자 식별 (Claude Desktop 사용자 → 감사 로그 연동)
- 멀티 워크북 지원 (Humax/EVCS/HUS/HUK/HBR/HSZ 동시 처리)

### v0.4 (전사 확대 + 자동화)

- cron 기반 무인 실행 파이프라인 (SAP → 추출 → 편집 → 검증 → 알림)
- Slack/이메일 알림 통합
- 사내 MCP 마켓플레이스 등록 (다른 부서 도구와 함께)
- SAP BTP/Joule 연동 평가 (Phase 3)
- 웹 대시보드 (검증 결과/이상치 시각화)

---

## 11. 강의 모듈 7 매핑

### 11.1 강의 목표와 MCP 도구 매핑

모듈 7 (Python MCP 제작 입문, 2시간 25분)은 본 설계 문서의 v0.1 범위를 실습 기반으로 전달한다. Revision 2에서 배부율 조회 실습(Live Artifact 출력) 추가로 +15분. Revision 3에서 환율 API 조회 실습 추가로 +10분.

| 강의 시간 | 내용 | 본 문서 참조 | 강사 제공 | 실무자 작성 |
|---|---|---|---|---|
| 0:00-0:20 | MCP 개념 재정리 (1차 복습) | 1. 개요 | 슬라이드 + K-Data MCP 시연 | - |
| 0:20-0:40 | FastMCP SDK 기본 (`@mcp.tool()`) | 2. 기술 스택 | 코드 예시 + 라이브 코딩 | - |
| 0:40-1:10 | humax-excel-mcp 설계 해설 (7개 도구) | 4. 도구 상세 Spec | 아키텍처 다이어그램 + 함수 시그니처 | 시그니처 읽기 + 질의 |
| 1:10-1:45 | **실습: extract_filtered 작성** | 4.1 + 5. 스키마 매핑 | 템플릿 코드 (빈칸 채우기 형태) | 필터 로직 + 파라미터 검증 작성 |
| 1:45-1:50 | **시연: verify_sums** (강사 라이브 코딩) | 4.2 | 완성 코드 시연 + 구조 설명 | 관찰 + 질의 |
| 1:50-2:05 | **실습: get_allocation_rates 조회** (Live Artifact 출력) | 4.6 + 4.5 | 배부율 조회 템플릿 + Live Artifact 결과 시연 | 배부율 조회 호출 + artifact 확인 |
| 2:05-2:15 | **실습: get_exchange_rates 환율 조회** (외부 API 연동) | 4.8 + 부록 D | 환율 API 호출 시연 + JPY 정규화 설명 + 캐시/fallback 동작 확인 | API 키 설정 + 환율 조회 호출 + artifact 확인 |
| 2:15-2:25 | Claude Desktop 등록 + 자연어 호출 시연 | 9. 등록 가이드 | 등록 가이드 문서 + 라이브 데모 | config.json 편집 + 호출 테스트 (사전 설치 완료 전제) |

### 11.2 강사 템플릿 vs 실무자 작성 영역

#### 강사 제공 (사전 작성)

- `server.py`: FastMCP 앱 진입점 (완성)
- `schemas/bp26.py`: 26BP 스키마 정의 (완성)
- `schemas/requests.py`, `schemas/responses.py`: pydantic 모델 (완성)
- `core/excel_io.py`: openpyxl 래퍼 (완성)
- `core/backup.py`: 백업 로직 (완성)
- `core/token_guard.py`: 토큰 가드 (완성)
- `tests/conftest.py`: 테스트 fixture (완성)
- `fixtures/`: 합성 Excel 파일 (완성)

#### 실무자 작성 (강의 실습)

- `tools/extract.py`: 필터 로직 핵심부 (빈칸 채우기)
  ```python
  # 강사 템플릿 (빈칸 = 실무자 작성)
  async def extract_filtered(...) -> ExtractResult:
      wb = load_workbook(file_path, data_only=True)
      ws = wb[sheet_name]
      df = worksheet_to_dataframe(ws)

      # === 실무자 작성 시작 ===
      if month:
          df = ____  # month 필터 적용
      if company:
          df = ____  # company 필터 적용
      if columns:
          df = ____  # 컬럼 선택
      # === 실무자 작성 끝 ===

      return build_extract_result(df, max_rows, output_format)
  ```

- `tools/verify.py`: 합계 검증 로직 (참고용 시연 코드, 실습 대상 아님)
  ```python
  # 강사 시연용 완성 코드 (실무자는 관찰 + 구조 이해)
  async def verify_sums(...) -> VerifyResult:
      df = load_sheet_as_dataframe(file_path, sheet_name)
      tree = build_org_tree(df)

      results = []
      for level in tree.levels:
          expected = sum_children(tree, level)  # 하위 레벨 합계 계산
          actual = get_subtotal_row(df, level)   # 해당 레벨의 합계 행 값
          status = "PASS" if abs(expected - actual) <= tolerance else "FAIL"
          results.append(LevelResult(level=level, expected=expected, actual=actual, status=status))

      return build_verify_result(results, tolerance)
  ```

### 11.3 라이브 데모 시나리오

```
실무자: "26BP 3월 raw에서 본사 인건비만 추출해서 합계 검증해줘"

Claude Desktop:
1. [extract_filtered 호출]
   → file: "26BP+3월 누계 실적.xlsx", sheet: "예산+실적",
     month: "2026-03", company: "HMX", account_group: "인건비"
   → 결과: 본사 인건비 42행 추출, estimated_tokens: 1,800

2. [verify_sums 호출]
   → file: "26BP+3월 누계 실적.xlsx", sheet: "예산+실적",
     levels: ["총합계", "사업부", "대조직"]
   → 결과: "본사 인건비 3월 합계 X백만원, 조직 3계층 합산 일치 확인. 이상치 2건 탐지."

3. Claude 종합 응답:
   "본사 인건비 3월 데이터를 추출했습니다 (42건, 토큰 약 1,800개 사용).
    합계 검증 결과 3계층 모두 일치합니다.
    이상치 2건:
    - 11 급여 -85백만 (대폭 감소, -56.7%)
    - 22 복리후생 +15백만 (+12.3%)"
```

### 11.4 강사 사전 점검 체크리스트

강의 **D-1** (전일)까지 아래 항목을 모든 실습 노트북에서 확인한다.

| # | 점검 항목 | 확인 방법 | 실패 시 대응 |
|---|---|---|---|
| 1 | Python 3.10+ 설치 | `python3 --version` (3.10 이상) | IT팀에 사전 설치 요청 |
| 2 | pip 의존성 설치 성공 | `pip install mcp openpyxl pandas pydantic python-dotenv` 에러 없음 | 오프라인 환경 시 wheels 사전 다운로드 |
| 3 | Claude Desktop 최신 버전 (MCP 지원) | Claude Desktop 설정 > Developer 메뉴 존재 확인 | 최신 버전 다운로드 + 설치 |
| 4 | 합성 fixture 파일 무결성 | `sample_26bp.xlsx` 열기 + `golden/*.json` 파싱 확인 | fixture 재생성 (`pytest --fixtures`) |
| 5 | Claude Desktop MCP 등록 테스트 | 강사 노트북에서 `config.json` 등록 후 자연어 호출 1회 성공 | config.json 경로/Python 경로 확인 |
| 6 | 강의실 네트워크 (pip 접근) | `pip install --dry-run mcp` 성공 | 오프라인 패키지 번들 준비 |
| 7 | config.json 사전 배포 | 5-10대 노트북에 `claude_desktop_config.json` MCP 등록 완료 | USB/공유 드라이브로 일괄 배포 |

> **핵심**: Claude Desktop 재시작 후 MCP 도구가 노출되기까지 10-30초 소요. 강의 시간 내 이 과정을 하면 시간 부족. 반드시 사전 배포.

---

## 12. RALPLAN-DR 요약

### 12.1 Principles (5개)

| # | 원칙 | 설명 |
|---|---|---|
| P1 | **원본 보존 우선** | 입력 파일은 읽기 전용. 모든 편집은 백업 후 새 파일에 출력 |
| P2 | **결정론적 처리** | 숫자 연산, 셀 편집은 Python 코드 실행. LLM의 확률적 생성에 의존하지 않음 |
| P3 | **토큰 효율** | 필요한 데이터만 추출. 처리/검증 분리. 100KB 하드 리밋 |
| P4 | **SAP 데이터 거버넌스** | PII 탐지, 데이터 분류 표시, 마스킹 옵션. Phase 0 게이트 전 실데이터 전송 금지 |
| P5 | **Cowork 친화** | 실무자는 CLI 학습 불필요. 자연어 호출만으로 모든 도구 사용 가능 |

### 12.2 Decision Drivers (3개)

| # | 동인 | 가중치 | 설명 |
|---|---|---|---|
| D1 | **실무자 학습 곡선 최소화** | 최상 | CLI/Python 학습 없이 Claude Desktop 자연어로 호출 |
| D2 | **에러 5개 구조적 해결** | 최상 | 프롬프트 개선만으로는 #1(원본 훼손), #5(숫자 검토) 근본 해결 불가 |
| D3 | **사내 배포 용이성** | 상 | MCP 서버 1회 작성 → v0.1 stdio: 각 PC에 Python+deps 필요. v0.2+ HTTP/SSE: 서버 1대만, 사용자는 config.json만 |

### 12.3 Options 비교

#### Option A: Cowork 스킬만 (MCP 없음)

| Pros | Cons |
|---|---|
| 즉시 적용 (추가 설치 없음) | #1 원본 훼손, #5 숫자 검토 근본 해결 불가 |
| 학습 곡선 제로 | 토큰 절약 한계 (전체 파일 전송 구조 유지) |
| | 대용량 데이터 처리 불가 |

#### Option B: Claude Code (CLI) 직접 사용

| Pros | Cons |
|---|---|
| Python 결정론 완전 활용 | 실무자 CLI 학습 부담 (D1 위반) |
| 자기 수정 + cron 무인 | 각 PC에 개별 설치 필요 (D3 위반) |
| Git 통합 | 강의 2시간 내 습득 어려움 |

#### Option C: MCP 서버 (하이브리드) -- 권장

| Pros | Cons |
|---|---|
| Python 결정론 + Cowork 자연어 (D1+D2 충족) | 초기 MCP 서버 개발 비용 (강사가 흡수, 7개 도구) |
| 1회 제작 → 전사 배포 (D3 충족) | openpyxl 서식 보존 한계 (실측 필요) |
| 토큰 70-90% 절감 (필터링) | Phase 0 거버넌스 게이트 의존 |
| 백업/검증/감사 로그 내장 | 실무자 호출만 (cron 무인은 v0.4) |
| 배부율 조회/변경 자동화 (수기 편집 Step 3 배부율 해소) | |
| 환율 자동 조회 (한국수출입은행 API, 수기 편집 Step 3 환율 해소) | |
| Live Artifact 출력으로 즉시 시각화 (Claude Desktop 연동) | |

#### Option D: Cowork + Computer Use (MCP 없이 Python 직접 실행)

| Pros | Cons |
|---|---|
| MCP 서버 개발 없이 즉시 사용 가능 | 비결정론적 (화면 좌표 기반 조작 → 해상도/언어 설정에 따라 실패) |
| 추가 코드 0줄 (Claude가 Python REPL 직접 실행) | 감사 로그 없음 (도구 호출 기록 구조 부재) |
| openpyxl 코드를 직접 작성/실행 | 배치 처리 비효율 (매 호출마다 화면 캡처 + 해석 루프) |
| | 실행 속도 느림 (스크린샷 → 좌표 계산 → 클릭 반복) |
| | 반복 사용 시 일관성 보장 불가 |

> **기각 사유**: D1(학습 곡선)은 충족하나, D2(구조적 해결)의 핵심인 **결정론적 처리**, **감사 로그**, **배치 처리 효율**에서 MCP(Option C)가 근본적으로 우위. Computer Use는 GUI 자동화에 적합하지, 구조화된 데이터 파이프라인에는 부적합.

### 12.4 권장 사유

**Option C (MCP 하이브리드)를 권장한다.**

1. **D1 충족**: 실무자는 Claude Desktop에서 자연어로 호출. CLI/Python 학습 불필요. K-Data MCP, 사주 MCP 등 1차 강의에서 이미 체험한 패턴과 동일.
2. **D2 충족**: Python 결정론으로 에러 #1(원본 훼손)과 #5(숫자 검토)를 구조적으로 해결. openpyxl 셀 단위 편집 + 자동 백업 + verify_sums 결정론 검증. 배부율 도구(`get_allocation_rates`, `update_allocation_rates`)로 수기 편집 Step 3의 배부율 작업도 자동화.
3. **D3 충족**: MCP 서버 1회 작성 → `claude_desktop_config.json`에 경로 추가만으로 전사 배포. 사내 서버 호스팅 시 유지보수도 1인.
4. **Option A 대비**: 에러 #1, #5 근본 해결 + 토큰 절감이 Option A에서 불가능한 구조적 한계. Live Artifact 시각화도 MCP 도구의 `artifact_hints`로만 가능.
5. **Option B 대비**: 동일한 Python 결정론을 CLI 학습 없이 달성. 강의 2시간 25분 내 실습 가능. 사내 배포가 개별 설치 대비 압도적으로 용이.
6. **리스크 관리**: Phase 0 거버넌스 게이트 + dry-run + 자동 백업 + PII 탐지 + Live Artifact PII 워터마크 + 환율 sanity check로 안전장치 다층 확보. Pre-mortem 7 시나리오 (S1-S7) 커버.
7. **Option D 대비**: Computer Use는 MCP 없이 즉시 사용 가능하나, 화면 좌표 기반 비결정론, 감사 로그 부재, 배치 비효율로 결산 워크플로우의 반복적/대량 데이터 처리에 부적합. MCP는 동일한 openpyxl 로직을 결정론적 API로 감싸 일관성과 추적성을 보장.

---

## 부록 A: 유효 회사 코드

| 코드 | 회사명 |
|---|---|
| HMX | Humax (본사) |
| HUS | Humax USA |
| HUK | Humax UK |
| HBR | Humax Brazil |
| HSZ | Humax Shenzhen |

## 부록 B: 조직 5계층 구조

```
총합계
├── STB (사업부)
│   ├── 개발 (대조직)
│   │   ├── SW개발 (중조직)
│   │   │   └── 플랫폼팀 (소조직)
│   │   └── HW개발 (중조직)
│   └── 영업 (대조직)
├── Mobility (사업부)
├── EVCS국내 (사업부)
└── EVCS해외 (사업부)
```

## 부록 C: CellUpdate 검증 규칙

| 검증 | 조건 | 에러 |
|---|---|---|
| 셀 주소 형식 | `^[A-Z]{1,3}[1-9][0-9]*$` 정규식 | `INVALID_CELL` |
| 값 타입 | `int \| float \| str` | `INVALID_VALUE_TYPE` |
| 업데이트 수 | `1 <= len(updates) <= 5000` | `TOO_MANY_UPDATES` / `EMPTY_UPDATES` |
| 중복 셀 | 동일 셀 주소 중복 시 마지막 값 적용 + 경고 | 경고만 (에러 아님) |

## 부록 D: 한국수출입은행 API 통화 코드 매핑

`get_exchange_rates`에서 사용하는 통화 코드 목록. 한국수출입은행 매매기준율(AP01) 기준.

| 통화 코드 | 통화명 | 단위 | 비고 |
|---|---|---|---|
| USD | 미국 달러 | 1 | 기준 통화 |
| EUR | 유로 | 1 | |
| JPY(100) | 일본 옌 | 100 | **100엔 단위 표시**. `deal_bas_r_per_unit`으로 1엔당 환율 제공 |
| CNH | 위안화 | 1 | 역외 위안 |
| GBP | 영국 파운드 | 1 | |
| HKD | 홍콩 달러 | 1 | |
| CHF | 스위스 프랑 | 1 | |
| CAD | 캐나다 달러 | 1 | |
| AUD | 호주 달러 | 1 | |
| SGD | 싱가포르 달러 | 1 | |
| THB | 태국 바트 | 1 | |
| SEK | 스웨덴 크로나 | 1 | |
| NZD | 뉴질랜드 달러 | 1 | |
| BRL | 브라질 헤알 | 1 | Humax Brazil (HBR) 관련 |
| IDR(100) | 인도네시아 루피아 | 100 | 100루피아 단위. JPY와 동일 정규화 적용 |

> **참고**: 한국수출입은행 API는 약 25-30개 통화를 제공하며, 위 목록은 Humax 결산에서 주로 사용되는 통화를 발췌한 것이다. `target_currencies=None` (전체) 조회 시 API가 반환하는 모든 통화가 포함된다. 단위가 1이 아닌 통화(JPY(100), IDR(100) 등)는 `unit_multiplier` 필드와 `deal_bas_r_per_unit` 필드가 자동 추가된다.
