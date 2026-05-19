# harness-setup.md

> Pre-Implementation Checklist 상세 SSOT. AGENTS.md에서 링크.

## 구조 / 공통화

- [ ] **TDD 우선** — `tests/unit/test_<module>.py`에 실패 테스트 작성 → 통과 → Refactor
- [ ] **함수 50줄 이내**, 매개변수 4개 이하, 중첩 3단계 이내
- [ ] **early return** 우선, 깊은 nested if 금지
- [ ] **try-except 에러 삼키지 않기** — 로깅 또는 `HumaxMCPError` 재raise
- [ ] **import 방향** — L5 → L4 → L3 → L2 → L1 단방향. `grep -rE "from \.\.tools" src/humax_excel_mcp/core/`로 위반 점검
- [ ] **매직 넘버 금지** — 모듈 상단 상수로 추출 (예: `_AUTO_DETECT_MIN_MATCHES = 5`)
- [ ] **Search Before Building** — 신규 helper 작성 전 `grep -r "<keyword>" src/humax_excel_mcp/core/ src/humax_excel_mcp/schemas/`

## 공유 모듈 레지스트리

신규 작성 전 다음 모듈에 동일/유사 기능 있는지 확인:

| 카테고리 | 모듈 | 함수 |
|---|---|---|
| 백업 | `core/backup.py` | `create_backup`, `prune_backups` |
| 감사 | `core/audit.py` | `audited` decorator, `audit_dir` |
| 에러 | `core/errors.py` | `HumaxMCPError`, `_make(CODE)` |
| Excel I/O | `core/excel_io.py` | `assert_xlsx_path`, `load_workbook_safe`, `get_sheet`, `worksheet_to_dataframe`, `validate_schema`, `detect_source_format` |
| 토큰 가드 | `core/token_guard.py` | `estimate_size_kb`, `auto_truncate` |
| Artifact hints | `core/artifact_hints.py` | `build_hints`, `maybe_hints` |
| 스키마 | `schemas/bp26.py`, `schemas/raw_bp26.py` | `validate_headers`, `normalize_headers`, `detect_source_format` |
| Pydantic 요청/응답 | `schemas/requests.py`, `schemas/responses.py` | 모든 도구 입출력 |

## 데이터 / 성능

- [ ] 루프 내부 DB/API/openpyxl 호출 점검 (N+1 차단)
- [ ] 독립 await 병렬화 (`asyncio.gather`) 검토 — 환율 N개 통화 동시 조회 등
- [ ] 메모리 집계보다 pandas groupby/agg 우선
- [ ] 캐시 가능 데이터는 TTL 명시 (예: 환율 12h)
- [ ] openpyxl `read_only=True` flag 검토 (대용량 raw xlsx)
- [ ] 응답 직렬화 전 `core.token_guard.auto_truncate` 통과

## 안전

- [ ] write 도구는 `output_path != file_path` 강제
- [ ] write 도구 진입 시 `core.backup.create_backup` 호출
- [ ] `dry_run=True` 시 원본 파일 sha256 불변
- [ ] `@audited("tool_name")` 데코레이터 적용 (`tools/__init__.register_all`에서)
- [ ] PII 컬럼은 aggregator 진입 전 drop (raw_bp26.PII_COLUMNS)
- [ ] 새 에러는 `core/errors.py`에 `_make("CODE")` 등록 후 raise

## 문체 / 카피

- [ ] 에러 메시지 한국어, 구체적 (어떤 파일/시트/셀)
- [ ] 도구 docstring 첫 줄 = 자연어 호출 가능한 한 줄 요약
- [ ] 과장어, vague attribution, 챗봇투 금지

## Dead Code 게이트

- [ ] `ruff check . --select F` (F401 미사용 import, F841 미사용 변수)
- [ ] `vulture src/ --min-confidence 80` (Phase 4에서 도입)
- [ ] `npm run gc` 대체: `bash scripts/gc.sh`에 포함

## 운영 인프라

- [ ] 새 도구는 `tools/__init__.py`의 `TOOL_NAMES` + `register_all`에 등록
- [ ] `docs/prd/mcp-design-plan.md`에 spec 추가
- [ ] `AGENTS.md` 도구 표 업데이트
- [ ] `docs/generated/schema-snapshot.md` 동기화 (스키마 변경 시)
- [ ] 변경 후 `bash scripts/gc.sh` 통과 확인

## 상태 종결

작업 종료 시 다음 중 하나로 보고:

- `DONE` — 모든 게이트 통과
- `DONE_WITH_CONCERNS` — 통과했지만 후속 검토 필요한 항목 있음 (tech-debt-tracker에 추가)
- `BLOCKED` — 외부 의존 (사용자 결정, 사내 IT 확인 등) 대기
- `NEEDS_CONTEXT` — 정보 부족, 추가 질문 필요

동일 접근 3회 실패 시 중단 + 에스컬레이션.
