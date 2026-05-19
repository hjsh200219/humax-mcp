---
created: 2026-05-19T23:05:00+09:00
project: humax-mcp
summary: harness engineering 셋업 + GC 2회 (L3 → L4 진입). source code 무수정, docs/scripts/config 추가만. 234 tests pass, 88.70% cov, vulture clean, pre-commit installed. Commit c18e05a push 완료.
---

## Session Digest

humax-excel-mcp에 agent-first harness 셋업. 기존 source code (src/, tests/, docs/prd/, README, progress.txt) 전혀 손대지 않고 다음을 추가: AGENTS.md (110 lines map), CLAUDE.md → AGENTS.md symlink, ARCHITECTURE.md (L1-L5 레이어), .claudeignore, .pre-commit-config.yaml, docs/ 하위 15개 파일 (QUALITY/RELIABILITY/SECURITY/PRODUCT_SENSE/PLANS + design-docs + exec-plans + generated/schema-snapshot + harness/{principles, maturity-framework, fix-catalog, gc-history, harness-setup}), scripts/{verify_docs.py, gc.sh}.

GC #1 (베이스라인): 63.75 / L3 Enforced. 약점 Top3: P6 Coverage=4, P3 Invariant=5, P7 GC-Auto=5.

TD-001/002/003 해소 작업:
- pyproject.toml에 pytest-cov + vulture + pre-commit 추가, [tool.coverage] / [tool.vulture] 설정 등록
- 실측 88.70% coverage (gate 70%+)
- vulture clean (pydantic v2 false positive ignore_names로 해소)
- pre-commit install 실행, ruff hooks + xlsx/.env 차단 hooks 활성

GC #2 (해소 후): 70.4 / **L4 Optimized** (+6.65). P6: 4→8, P3: 5→7, P7: 5→7.

신규 발견 TD-012 (도구 15 함수 >50줄), TD-013 (progress.txt 잔존).

Commit c18e05a (24 files, 1587+ lines) push 완료. Pre-commit 첫 run에서 scripts/verify_docs.py 자동 reformat 발생 (신규 파일이라 OK).

## Progress

### 완료
- [x] AGENTS.md / CLAUDE.md symlink / ARCHITECTURE.md / .claudeignore 신규 생성
- [x] docs/ 15개 파일 (5 routes + 2 design-docs + 2 exec-plans + 1 generated + 5 harness)
- [x] scripts/verify_docs.py (4 게이트: 도구 수 / 스키마 버전 / 레이어 import / AGENTS.md 크기)
- [x] scripts/gc.sh (ruff + pytest+cov + vulture + verify-docs 통합)
- [x] .pre-commit-config.yaml (ruff + 사내 데이터/.env 차단)
- [x] pyproject.toml [tool.coverage] / [tool.vulture] 등록 (기존 deps 보존)
- [x] pre-commit install (TD-003 해소)
- [x] pytest-cov 실측 88.70% (TD-001 해소)
- [x] vulture clean (TD-002 해소, pydantic v2 ignore 패턴 등록)
- [x] GC #1 + GC #2 시행, gc-history.md 4행 기록
- [x] progress.txt 내용을 docs/exec-plans/completed/v0.1.0-tdd-session.md로 이관
- [x] Memory 2건 신규 추가: vulture-pydantic-v2-false-positives, ruff-format-as-advisory-not-blocking
- [x] commit c18e05a, push 3543e9d..c18e05a

### 미완료
- [ ] **TD-012 (도구 함수 >50줄)**: 15 함수 (4개 100줄+: extract_filtered=154, apply_golden_template=154, verify_sums=145, allocation_set=123). 비즈니스 helper 추출 검토. 회의적: workflow orchestrator는 자연 증가 — 선택적 분할.
- [ ] **TD-013 (progress.txt 잔존)**: 이관 사본 작성됨, 원본 삭제는 사용자 결정.
- [ ] **README.md PowerShell-only**: Mac/Linux 진입 마찰 (TD-011, P3).
- [ ] **L5 진입 (80+)**: 잔존 약점 P5 Disclosure (ADR 없음), P9 Knowledge (용어집 없음). 다음 sprint 후보.

## Next Steps

1. **TD-012 진단**: 4개 100줄+ 도구의 분기 복잡도 측정 후 helper 추출 PR 1건씩 (input validation / load / business / response build 단계 분리)
2. **GC #3 정기 점검**: 1-2 sprint 후 또는 새 도구 추가 시 `bash scripts/gc.sh` 실행. gc-history.md에 자동 append됨.
3. **AGENTS.md 효과 측정**: 다음 새 세션이 AGENTS.md를 우선 읽고 작업 시작하는지 확인 (회의적 검증).
4. **(선택) ruff format apply**: 추후 별도 PR로 blanket apply 검토. 신규 파일은 pre-commit으로 자동 포맷.

## Blockers

없음. 모든 게이트 PASS (ruff check, pytest 234, cov 88.70%, vulture clean, verify-docs 4/4).

## Watch Out

- **vulture pydantic v2 false positive**: `ignore_names`에 `cls`, `model_config` 필수. positional path 인자 주면 pyproject 설정 무시됨. `vulture --min-confidence 80`만 호출.
- **ruff format은 advisory**: 기존 코드 blanket format 금지. gc.sh에서 WARN으로 처리. 신규 파일만 pre-commit ruff-format hook으로 자동 정리.
- **pre-commit 첫 run 지연**: ruff + pre-commit-hooks 환경 초기화에 1-2분. CI에서는 캐시 활용.
- **verify_docs.py allowlist**: 신규 L2 orchestrator 추가 시 PRD 명시 + `L2_ORCHESTRATOR_ALLOWLIST` 갱신 + `docs/design-docs/layer-rules.md` Sanctioned 예외 섹션 추가.
- **AGENTS.md 120줄 한도**: 도구/규칙 증가 시 docs/ 하위로 분리해서 ~100줄 유지. verify_docs.py 4번째 게이트가 강제.
- **_workspace/ gitignored**: GC raw 결과 (`00_audit.md`, `00_code_facts.json`, `01-04`)는 로컬만. 다른 PC 이어받기 시 재생성.

## Files Touched

### New (root)
- `AGENTS.md` (110 lines)
- `CLAUDE.md` (symlink → AGENTS.md)
- `ARCHITECTURE.md` (91 lines)
- `.claudeignore` (80 lines)
- `.pre-commit-config.yaml` (30 lines)

### New (docs/)
- `docs/PLANS.md`, `docs/PRODUCT_SENSE.md`, `docs/QUALITY.md`, `docs/RELIABILITY.md`, `docs/SECURITY.md`
- `docs/design-docs/{core-beliefs, layer-rules}.md`
- `docs/exec-plans/tech-debt-tracker.md` + `completed/v0.1.0-tdd-session.md`
- `docs/generated/schema-snapshot.md`
- `docs/harness/{principles, maturity-framework, fix-catalog, gc-history, harness-setup}.md`

### New (scripts/)
- `scripts/verify_docs.py` (4 게이트, executable)
- `scripts/gc.sh` (통합 게이트, executable)

### Modified
- `pyproject.toml`: pytest-cov + vulture + pre-commit 의존성, [tool.coverage] + [tool.vulture] 설정 추가
- `.gitignore`: `_workspace/` 추가

### New (.claude-project/memory/)
- `vulture-pydantic-v2-false-positives.md`
- `ruff-format-as-advisory-not-blocking.md`

### Untouched (보존)
- `src/humax_excel_mcp/**` (10 tools / core / schemas)
- `tests/**` (234 tests)
- `docs/prd/**` (SSOT 설계 문서)
- `docs/references/**` (사내 데이터 xlsx)
- `fixtures/templates/**`
- `README.md`, `progress.txt`, `LICENSE`

## Commit / Push

- Commit: `c18e05a` — `chore(harness): set up agent harness + GC infrastructure (L4 Optimized)`
- Push: `3543e9d..c18e05a main -> main` (origin/hjsh200219/humax-mcp)
- 24 files changed, 1587 insertions(+)
