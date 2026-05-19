---
created: 2026-05-19T22:30:00+09:00
project: humax-mcp
summary: humax-excel-mcp v0.1.2 — real-data adapter (raw_bp26 + aggregator + EVCS expand_evcs), 234 tests green, push b96b5d8
---

## Session Digest

humax-excel-mcp v0.1.2 — 실제 26BP raw 데이터 (header row 3, 15007 transactions, 13 배부율) 와 v0.1 bp26 (pre-aggregated cum cols) 사이 어댑터 레이어 추가. v0.1.1 구현 검증 중 발견: synthetic fixture 만 작동, 실제 reference xlsx 로는 빈 산출물. ralplan consensus (2 iterations, Critic ITERATE → APPROVE) 통과 후 ralph TDD 로 US-021~US-027 + US-024a 8 스토리 완주. 5-6s per `generate_report` real-data call. **commit b96b5d8 push 완료.**

## Progress

### 완료
- [x] schemas/raw_bp26.py (NEW): 63-col transaction schema, 4 PII drop, 13 배부율, 6 Humax companies
- [x] core/aggregator.py (NEW): aggregate_to_bp26(raw, target_month, *, expand_evcs) — base + EVCS-only paths
- [x] core/excel_io.py: worksheet_to_dataframe header_row + schema_module 옵션 + auto-detect (scan rows 1-10, threshold 5+ matches). detect_source_format() 추가. 4 기존 callers 무수정 backward-compat.
- [x] tools/template_engine.py: source_format + expand_evcs 라우팅, read_only=True src workbook fix (30s+ → 5s)
- [x] tools/report.py: source_format + expand_evcs report_type 자동 결정
- [x] template_bindings.py: HUMAX_ACCOUNT_BINDING filter ["HMX"] → 6 Humax 회사
- [x] tests +57 (177 → 234): unit 19 aggregator + 9 raw_bp26 + 7 excel_io + 2 template_engine + integration 3 + e2e 13
- [x] Real-data e2e (13 tests) `docs/references/26BP+...xlsx` 사용 — CI-safe @pytest.mark.skipif
- [x] Critic verification APPROVE (loop 2 — 4 MAJOR gaps fixed)
- [x] ruff clean (12 auto-fix + conftest pd top-level import)
- [x] git commit b96b5d8, push to origin/main

### 미완료
- [ ] template_bindings 의 sheet 24개 추가 (현재 1 worked sheet 만 / template type)
  - humax_allocation: '3월 누계' 만, 나머지 24 sheets (월별/누계/Diff) deferred
  - humax_account / evcs_account: '요약' 만, 나머지 sheets deferred
  - 운영 중 실제 채우는 sheet 발견 시 incremental 추가
- [ ] generate_report 산출물의 row5 D5/E5 None 이슈 확인 (formula 셀이지만 sum 결과 None — 데이터가 실제로 비어서?)

## Next Steps

1. **operational verification** — Cowork 환경에서 `generate_report(source_file, report_type, output_path, month=3)` 실제 호출 → Live Artifact 렌더 확인
2. **bindings 확장** — 추가 sheet 발견 시 template_bindings.py 의 각 _BINDING 에 SheetBinding 추가
3. **performance budget** — 150k row 가정 시 polars 도입 검토 (현재 pandas, 15k → 5s; linear scale 시 50s 한계 가까움)
4. **MCP integration test** — Claude Desktop / Cowork 실제 stdio 호출로 5s 응답 시간 검증

## Blockers

없음. 실제 데이터 검증 완료 (4108 populated cells, formula 보존, 디자인 보존).

## Watch Out

- **read_only=True 한계**: `ws.cell(r,c).value = X` 쓰기 불가. mutate path 인 template_wb 는 read_only=False 유지.
- **EVCS expand_evcs flag**: 잘못 호출 시 빈 출력 — silent corruption 없음 (visible failure 보장).
- **bp26.py FROZEN**: v0.1.2 에서도 손대지 말 것. 변경 필요 시 raw_bp26 또는 신규 schema 파일.
- **template_bindings 24+ sheets deferred**: 1 worked sheet/type 만 검증됨. 운영 중 빈 sheet 발견 시 binding 추가.

## Files Touched

### New
- `src/humax_excel_mcp/schemas/raw_bp26.py`
- `src/humax_excel_mcp/core/aggregator.py`
- `tests/unit/test_aggregator.py`
- `tests/e2e/test_real_data.py`
- `.claude-project/memory/{excel-io-readonly-source-large-file,aggregator-evcs-per-call-flag,raw-vs-aggregated-schema-separation}.md`

### Modified
- `src/humax_excel_mcp/core/excel_io.py` (worksheet_to_dataframe + detect_source_format)
- `src/humax_excel_mcp/core/template_bindings.py` (humax_account 6 companies)
- `src/humax_excel_mcp/tools/template_engine.py` (source_format + read_only)
- `src/humax_excel_mcp/tools/report.py` (source_format + expand_evcs routing)
- `tests/conftest.py` (synthetic_raw_26bp_df fixture + pd import)
- `tests/unit/test_schemas.py` (TestRawBP26Schema)
- `tests/unit/test_excel_io.py` (header_row + auto-detect tests)
- `tests/unit/test_template_engine.py` (6 companies filter test + aggregator flow)
- `tests/integration/test_template_chain.py` (raw→template + aggregated negative path)
- `.claude-project/memory/MEMORY.md` (3 entries)

### Deleted
- `.env.example` (사용자 의도)

### Plan
- `.omc/plans/v012-real-data-adapter.md` (1836 lines, RALPLAN-DR Deliberate consensus APPROVED)
- `.omc/plans/open-questions-v012.md`
