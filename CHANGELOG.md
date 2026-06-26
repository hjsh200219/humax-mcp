# Changelog — humax-excel-mcp

`git log` (18 커밋, be1172a → 5db0fce) 및 working tree 분석 기준. 날짜는 커밋 날짜.

## [Unreleased] — 커밋 전 (working tree)

### 추가
- **`update_fc_month_report`** 도구 신규 (11번째 도구) — raw data + 전월 FC 보고서로 당월 배부판
  (`{월}(AC)` 채우기 + `{월} 누계(AC)`/`{월} 누계(상세)` 생성 + 3-way 교차검증) 자동 생성.
  기존 `humax-monthly-report` 스킬의 `build_fc_report.py`가 `{월}(AC)` 개별월 시트를
  채우지 않는 누락을 발견·수정해 포팅 (2026-06-26 5월 실데이터로 검증). 설계 문서:
  `docs/exec-plans/active/us-023-fc-month-update-tool.md`.
  - 신규 `src/humax_excel_mcp/core/fc_report_layout.py`(레이아웃 상수),
    `src/humax_excel_mcp/tools/fc_month_update.py`(오케스트레이션).
  - `schemas/responses.py`에 `FcMonthAcSummary`/`FcMonthCumulativeSummary`/
    `FcMonthVerification`/`FcMonthUpdateResult` 추가.
- **`write_cells`**: `지급수수료` 시트 대상으로 사전 검증 경고 추가. CC(B열)+GL(E열) 값은 있는데 AB열(4월예산 SUMIFS 수식)이 비어 있는 행을 감지해 경고 메시지 반환 (`src/humax_excel_mcp/tools/write.py`).

### 참고 (커밋 시 주의)
- `git status`상 106개 파일이 "modified"로 뜨지만 실질 변경은 **`write.py` 1개뿐**. 나머지는 전부 CRLF↔LF 줄바꿈 차이(diff 13,688 삽입/13,663 삭제 중 거의 전부)다. 저장소에 `.gitattributes`가 없고 `core.autocrlf`도 설정돼 있지 않아 발생.
  - VS Code에서 그대로 커밋하면 의미 없는 105개 파일 변경이 커밋 이력에 끼어든다.
  - 권장: ① `git add src/humax_excel_mcp/tools/write.py`로 실제 변경분만 스테이징해 커밋, 또는 ② 커밋 전 `git config core.autocrlf true`(Windows) + `.gitattributes`(`* text=auto`) 추가 후 한 번 정규화 커밋을 별도로 분리.

---

## v0.1.2 — 2026-05-19 (`b96b5d8`, `3543e9d`)
**실데이터 어댑터 — 26BP 트랜잭션 레벨 xlsx 대응 (234 tests)**

- `core/aggregator.py` 신규: raw 트랜잭션 행을 조직×계정 단위로 집계
- `schemas/raw_bp26.py` 신규: raw 컬럼 스키마 분리 정의
- `core/excel_io.py`, `core/template_bindings.py`, `tools/template_engine.py`, `tools/report.py` 확장 — 집계 스키마와 raw 스키마 분리 반영
- 알려진 패턴(메모리 기록):
  - EVCS는 호출당 한 번만 집계 (aggregator-evcs-per-call-flag)
  - 대용량 원본 파일은 읽기 전용으로 열어야 함 (excel-io-readonly-source-large-file)
  - raw 스키마와 집계 스키마는 분리 유지 (raw-vs-aggregated-schema-separation)

> 주의: `pyproject.toml`은 현재도 `version = "0.1.1"`로 남아 있음 — v0.1.2 작업 시 버전 문자열을 올리지 않은 채 진행된 것으로 보임.

## v0.1.1 — 2026-05-19 (`b972848`, `c70fae4`)
**도구 3종 추가 (7개 → 10개) — 디자인 드리프트 제거**

- `apply_golden_template` 신규: 골든 템플릿 적용으로 셀 서식/구조 드리프트 차단
- `generate_report` 신규
- `restore_backup` 신규
- `core/template_loader.py`, `core/template_bindings.py` 신규 — 템플릿 바인딩 엔진
- `fixtures/templates/*.xlsx` + `.template.json` 3종 추가 (evcs_account, humax_account, humax_allocation)
- `scripts/build_fixture_templates.py` 신규
- 패턴(메모리 기록): 골든 템플릿 엔진 패턴(golden-template-engine-pattern), audited 데코레이터의 `file_path_arg` 확장(audited-file-path-arg-extension)

## v0.1.0 — 2026-05-19 (`b194dc6`, `97517d8`, `9a0bc8d`)
**최초 구현 — TDD로 7개 MCP 도구 (130 tests)**

- 최초 도구 7개: `extract_filtered`, `verify_sums`, `write_cells`, `generate_diff_candidates`, `get_allocation_rates`, `update_allocation_rates`, `get_exchange_rates`
- `schemas/bp26.py`(Pydantic v2), `core/excel_io.py`, `core/backup.py`(sha256 백업 검증), `core/token_guard.py`(50KB/100KB 토큰 가드 + PII 정규식), `core/audit.py`(JSONL 감사 로그), `server.py`(FastMCP 서버)
- `tests/{unit,integration,e2e}` 130개 테스트 전체 통과
- 패턴(메모리 기록): pytest-httpx 0.36 API 차이(`url=re.compile(...)`), 스키마 검증을 빈 df 체크보다 먼저(validation-order-schema-first), diff는 회사+CC+GL 복합키 필요(pandas-multi-key-diff-pattern), write 출력 경로 안전성(write-tool-output-path-safety)

## 초기 scaffolding — 2026-05-19 (`be1172a`)
- 저장소 최초 생성: PRD(`docs/prd/mcp-design-plan.md`), 강의 계획서(`docs/prd/humax-lecture-plan.md`), `.gitignore`, `LICENSE`, 최초 `README.md`

---

## 인프라 / 하니스

### 2026-05-19 (`c18e05a`)
- Agent harness + GC 인프라 구축 (L4 Optimized): `AGENTS.md`, `ARCHITECTURE.md`, `docs/harness/*`, `docs/design-docs/*`, `scripts/gc.sh`, `scripts/verify_docs.py`, `.pre-commit-config.yaml`, `.claudeignore`
### 2026-05-19 (`7a1616d`)
- L3 → L4 하니스 전환 핸드오프. 패턴: ruff format은 advisory(차단 아님), vulture가 Pydantic v2 필드를 false positive로 잡는 이슈 기록

---

## 문서 / 강의 자료 (MCP 코드 변경 없음)

| 날짜 | 커밋 | 내용 |
|---|---|---|
| 2026-05-26 | `c73ceab` | 4회차 강의 계획 v2 (Desktop→Code→API→Web) 추가 |
| 2026-05-26 | `d3c8d58` | 강의 계획 v2 핸드오프 (DRI 모델 페다고지 메모리) |
| 2026-05-26 | `7d4c291` | `docs/prd/data-flow.md` 추가 (비개발자용 Excel 데이터 흐름 설명) |
| 2026-06-04 | `75dd3ac` | 강의 계획 v2에 2회차 실행 로그 추가 |
| 2026-06-04 | `2641b1b` | 핸드오프 (3회차 git 기초 예정) |
| 2026-06-18 | `9de29fb` | README를 현재 코드/구조에 맞게 업데이트 |
| 2026-06-18 | `4e5e6ee` | 강의 계획 4→5회차 재편 + 인터랙티브 강의 튜너(`lecture-plan-playground.html`) 신설 |
| 2026-06-18 | `5db0fce` | 5회차 재편 + 강의 튜너 신설 핸드오프 (최신 HEAD) |

---

## 현재 버전 스냅샷 (HEAD `5db0fce` 기준)

- MCP 도구 10개 (`src/humax_excel_mcp/tools/__init__.py`의 `TOOL_NAMES` 참조): `extract_filtered`, `verify_sums`, `write_cells`, `generate_diff_candidates`, `get_allocation_rates`, `update_allocation_rates`, `get_exchange_rates`, `apply_golden_template`, `generate_report`, `restore_backup`
- 안전 정책 P1–P5: 원본 보존(read-only 기본) / 결정론 Python 위임 / 토큰 효율 / 백업+dry-run+감사로그+sha256 / 자연어 호출
- `pyproject.toml` 버전 문자열: `0.1.1` (위 "참고" 항목 — 실제 기능은 v0.1.2 수준)
