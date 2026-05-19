# ARCHITECTURE.md

> humax-excel-mcp 레이어 구조 + 의존 방향 + 교차 관심사. AGENTS.md의 상세 참조.

## 도메인 개요

stdio MCP 서버. Claude Desktop이 `humax-excel-mcp` 바이너리를 spawn하고 JSON-RPC 호출. 입출력은 결정론 Python으로 처리하고 LLM 산술을 배제한다.

### 데이터 흐름

```
Claude Desktop ──stdio──> server.py (FastMCP)
                                │
                                ▼
                          tools/* (10 도구, @audited 데코레이터)
                                │
                                ▼
                      core/* (excel_io, backup, audit, ...)
                                │
                                ▼
              schemas/* (bp26, raw_bp26, requests, responses)
                                │
                                ▼
                       openpyxl / pandas / httpx
```

## 레이어 정의 (L1 ← L5)

| Layer | Dir / File | 책임 | 의존 허용 |
|---|---|---|---|
| **L1 Server** | `src/humax_excel_mcp/server.py` | FastMCP 인스턴스 생성, tool 등록 진입점 | L2 |
| **L2 Tools** | `src/humax_excel_mcp/tools/` | 10 MCP 도구. 비즈니스 워크플로 조합 | L3, L4, L5 (서로 X) |
| **L3 Core** | `src/humax_excel_mcp/core/` | excel_io, backup, audit, errors, token_guard, artifact_hints, aggregator, template_loader, template_bindings | L4, L5 |
| **L4 Config** | `src/humax_excel_mcp/config.py` | dotenv 로딩, env helpers | L5 |
| **L5 Schemas** | `src/humax_excel_mcp/schemas/` | bp26, raw_bp26, requests, responses (pydantic v2) | (없음) |

### 의존 규칙

- 위 → 아래 단방향만. 역방향 import 금지.
- 같은 레이어 내부 import는 허용 (예: `core/excel_io` → `core/errors`).
- L2 도구끼리 직접 import 금지. 공통 로직은 L3로 추출.
- L5 schemas는 라이브러리(pydantic, pandas) 외 어떤 프로젝트 모듈도 import하지 않는다.

### 위반 시 조치

`docs/design-docs/layer-rules.md` 참조. ruff `I` (isort) + 수동 그렙 (`grep -r "from ..tools" src/humax_excel_mcp/core/`)으로 점검.

## 교차 관심사

| 관심사 | 구현 위치 | 적용 방식 |
|---|---|---|
| **백업** | `core/backup.py` (`create_backup`) | sha256 검증. `tools/write`, `tools/allocation_set`, `tools/template_engine`, `tools/restore`에서 호출 |
| **감사 로그** | `core/audit.py` (`@audited` 데코레이터) | 모든 도구 등록 시점 (`tools/__init__.py`)에 적용. JSONL 일일 로그, 0o700/0o600 권한 |
| **에러 코드** | `core/errors.py` (40+ 코드) | `HumaxMCPError` 계층. PRD §4 매핑. `to_dict()` → MCP 에러 응답 |
| **토큰 가드** | `core/token_guard.py` | SOFT 50KB / HARD 100KB. PII 정규식 (RRN, KR phone, 사번) |
| **PII 차단** | `schemas/raw_bp26.PII_COLUMNS` + `core/token_guard` regex | `core/aggregator.py` 진입 전 컬럼 제거 |
| **스키마 검증** | `core/excel_io.validate_schema`, `detect_source_format` | aggregated (bp26) / raw (raw_bp26) auto-detect |
| **Live Artifact** | `core/artifact_hints.py` | `render_format` ∈ {`excel`, `live_artifact`, `both`}. `maybe_hints()` returns None for excel-only |
| **환율 캐시** | `tools/exchange.py` 내부 | 12h in-process cache. 7-day fallback chain |

## 외부 의존

| 외부 | 사용 위치 | 신뢰 경계 |
|---|---|---|
| 한국수출입은행 API (`oapi.koreaexim.go.kr`) | `tools/exchange.py` | 공공 데이터, PII 무관. 사내 방화벽 허용 필요 |
| `.env` (`EXCHANGE_RATE_API_KEY`) | `config.py` | 절대 커밋 금지 |
| Excel xlsx (사내 raw) | `core/excel_io` | gitignored. 백업/restore만 git history와 분리 |

## 파일 수 (2026-05-19 기준)

- src/humax_excel_mcp/: 3,601 lines (Python only)
- tests/: 234 tests collected (unit + integration + e2e)
- docs/prd/: SSOT 설계 문서 2 (mcp-design-plan, humax-lecture-plan)
- fixtures/templates/: 골든 템플릿 xlsx (데이터 클리어드, 구조만)

## 확장 포인트 (v0.2+)

| 영역 | 위치 | v0.2 변경 예정 |
|---|---|---|
| HTTP/SSE 전송 | `server.py` | 현재 stdio. v0.2에서 사내 PC 1대 서버화 |
| 적요 활용 | `tools/extract.py` + `schemas/bp26.TEXT_COLUMNS` | LLM 분류 도구 추가 |
| 고급 배부 | `tools/allocation_*.py` + `core/aggregator.py` | EVCS 가상 행 외 추가 시나리오 |
| SAP 연동 | 신규 `tools/sap/` | OData / RFC 직접 |

## 회의적 검증 (Skeptical Verification)

자체 평가 편향 차단을 위해 verifier는 "증명될 때까지 미흡" 관점으로 채점. setup-reviewer / health 게이트는 다음을 의심한다:

- 문서가 "존재한다"는 사실 ≠ 코드와 일치한다
- 테스트가 "통과한다"는 사실 ≠ 실제 회귀를 잡는다 (커버리지 게이트 필요)
- 백업이 "생성됐다"는 사실 ≠ 복구 가능하다 (`restore_backup` E2E 필요)
