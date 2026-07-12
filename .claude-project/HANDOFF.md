---
created: 2026-07-12T00:00:00+09:00
project: humax-excel-mcp
summary: 정확도·속도 개선 PRD 작성 + 12개 US 전체 구현 완료, 286 tests green, gc.sh 전체 PASS, 코드 푸시 완료
---

## Session Digest

`docs/prd/accuracy-speed-improvement.md` (Rev 2) 작성 후 12개 User Story 전체 구현. 코드 감사로 발견한 "검증했다 보고하지만 실제 검증 안 하는" 정확도 결함 3건(P0)과 구조적 속도 낭비를 근본 해결. 커밋 `eeafc00` origin/main 푸시 완료.

## Progress

**완료**
- 정확도 P0: verify_sums 실계층 rollup(+SKIPPED 상태), exchange sanity 전영업일 비교 실동작화, 수식 검사 침묵 실패 제거
- 속도 P1: exchange async+병렬 fallback, core/workbook_cache.py 신설(mtime 키 LRU + df.copy), read_only 전환
- 정밀도 P2: EVCS 행 단위 round-half-even, month_parse_warning, auto_truncate 비례 축소, extract page/page_size, 필터 벡터화
- 인프라: tests/benchmarks/ + gc.sh advisory 벤치, ruff pre-commit v0.5.0→v0.15.13 정렬 + known-first-party 명시, AGENTS.md 11도구 동기화, TD-006/007 해소
- 검증: 286 tests green, gc.sh 전체 게이트 PASS, 코드 커밋·푸시 완료

**미완료**
- 없음 (본 PRD 범위 전부 완료)

## Next Steps

1. **TD-004** — `pip-audit`/`safety` 도입 + gc.sh 보안 스캔 단계 (P2)
2. **TD-005** — `tools/template_*.py` 3개 모듈 공통 helper → `core/template_common.py` 추출 (P2)
3. **레포 전체 ruff 0.15.13 포맷 마이그레이션** — 이번 커밋은 세션 파일만 포맷. 미변경 파일은 구 포맷 잔존. 별도 포맷-only 커밋으로 `pre-commit run --all-files` 일괄 정리 권장 (선택)
4. **verify_sums 실데이터 회귀 확인** — 5계층 실검증 활성화로 실제 결산 파일에서 중간 계층 FAIL 발생 여부 점검 (PRD §8 리스크)

## Blockers

없음

## Watch Out

1. **verify_sums 5계층 실검증 활성화** — 기존 실데이터에서 중간 계층 FAIL 다발 가능. tolerance 유지 + SKIPPED 상태로 점진 도입 (PRD §8).
2. **exchange sanity는 세션 스코프** — 프로세스 재시작 직후 첫 조회는 비교 대상 데이터 없어 sanity skip (정상 동작, PRD Rev 2 명시).
3. **workbook_cache 무효화** — write/restore 후 path invalidate 필수. 신규 write 경로 추가 시 invalidate 호출 확인.
4. **ruff 버전 정렬 side effect** — pre-commit이 0.15.13이므로 이후 구 파일 touch 시 포맷 변경 발생 (정상 동작).

## Files Touched

**신규**
- docs/prd/accuracy-speed-improvement.md, src/humax_excel_mcp/core/workbook_cache.py
- tests/benchmarks/{__init__,test_perf_baseline}.py, tests/unit/test_workbook_cache.py

**핵심 수정**
- tools/verify.py (5계층 rollup + 수식 에러 표면화 + read_only)
- tools/exchange.py (async + gather 병렬 fallback + 전영업일 sanity)
- tools/extract.py (캐시 통합 + page/page_size + 필터 벡터화)
- core/{aggregator,token_guard,excel_io,errors}.py, schemas/responses.py (SKIPPED status)
- tools/{allocation_get,write,restore}.py (캐시 통합/invalidate)

**설정·문서·테스트**
- pyproject.toml, .pre-commit-config.yaml, scripts/gc.sh
- AGENTS.md, docs/exec-plans/tech-debt-tracker.md, docs/harness/gc-history.md
- tests/conftest.py + unit 테스트 5종 (verify/exchange/extract/aggregator/excel_io)
