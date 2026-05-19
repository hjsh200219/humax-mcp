---
created: 2026-05-19T15:55:00+09:00
project: humax-mcp
summary: humax-excel-mcp v0.1.1 — 디자인 드리프트 차단 3 도구 추가 (10 tools total, 177 tests green, push b972848)
---

## Session Digest

humax-excel-mcp v0.1.1 patch — PRD 에러 #3 (디자인 드리프트, "10번 재명령") 구조적 해결. ralplan consensus(Planner/Architect/Critic 2 iteration → APPROVED) 통과 후 ralph TDD 사이클로 US-015~US-020 6 스토리 완주. 3 신규 MCP 도구 추가:

- `apply_golden_template` — 골든 템플릿 결정론 적용 (매번 동일 산출물)
- `generate_report` — extract→template→verify 체이닝 orchestrator
- `restore_backup` — side-file default + 이중 확인 게이트 in-place restore

골든 템플릿 엔진: `core/template_bindings.py` (pydantic v2 binding models), `core/template_loader.py` (sidecar 검증), `scripts/build_fixture_templates.py` (docs/references/*.xlsx → fixtures/templates/*.xlsx 데이터 클리어드 + 수식/서식 보존).

총 도구 수 7→10. 테스트 130→177 (+47). 회귀 0. PRD Revision 4 + Pre-mortem S8-S10 + §12.3.1 ADR 추가. 단일 커밋 `b972848 feat: v0.1.1 — add 3 MCP tools for design drift elimination`로 origin/main 푸시.

## Progress

- [x] US-015 fixtures (18/18 tests) — 3 골든 템플릿 + sidecar JSON 생성
- [x] US-016 apply_golden_template (12/12) — 4-safety 패턴, 실제 post-write verify
- [x] US-017 generate_report (8/8) — orchestrator
- [x] US-018 restore_backup (5/5) — 이중 확인 게이트
- [x] US-019 PRD Revision 4 — 10 tools 정합성, §4.9-4.11, S8-S10, ADR
- [x] US-020 tool integrity + audited file_path_arg + integration 3/3 + e2e 2/2
- [x] Architect reviewer: REJECTED 5 blockers → 모두 fix → APPROVED
- [x] ai-slop-cleaner: 2 trivially-true assertions 강화 (>=0 → >0)
- [x] git push (b972848)
- [ ] v0.2 항목 (적요 분류, 건별 배부, PII 마스킹)
- [ ] v0.3/v0.4 (SAP 연동, cron 자동화)
- [ ] 실배포 갭 (install.ps1/CI/Claude Desktop config 등) — 강의 전 필수

## Next Steps

1. **실배포 갭 10종** (PRD §9.5 v0.1 그대로 carries over):
   1. `scripts/install.ps1` + `install.sh`
   2. `scripts/update.ps1`
   3. Claude Desktop config 자동 등록 PowerShell
   4. `.github/workflows/test.yml` CI
   5. `humax_config/.local` CC 마스터 분리
   6. 배부율 마스터 submodule
   7. `oapi.koreaexim.go.kr` 사내 방화벽 IT 협의
   8. STDIO 실 핸드셰이크 smoke test
   9. audit chmod 600 OS별 실측
   10. SOW hypercare 책임 소재
2. **남은 SheetBinding 30개 완성** (각 template_type 당 worked 1개만 현재; 나머지 30 sheet bindings를 conftest 검증 gate 후 추가 작성)
3. **v0.1.2 followups (architect deferred)**: restore_backup audit `restored_path` 기록 추가, audit `RestoreBackupResult.backup_path` attr 부재 fix
4. **v0.2 우선순위**: `classify_by_text` (적요 PoC) → `allocate_costs` 건별 배부 → `mask_pii`/`mask_amounts`

## Blockers

- 실 26BP raw 데이터 미접근 (합성 fixture + reference 산출물만 검증) — 실파일 dry_run 미실측
- 사내 GitHub Org repo 정책 (사내 IT 확정 대기)
- 사내 방화벽 `oapi.koreaexim.go.kr` 허용 여부
- Anthropic DPA/ZDR 정책

## Watch Out

- v0.1.1 신규 도구 ralph 가이드: docs/references/*.xlsx는 LOCAL ONLY (gitignored). 새 환경에서 `scripts/build_fixture_templates.py` 실행 불가하면 fixtures/templates/ 커밋분 사용
- `apply_golden_template` post-write verify는 첫 row만 spot-check (full row 비교 X) — 큰 buggy mapping은 binding spec 검토 의존
- restore_backup `confirm_overwrite_original=True` + `original_file_path` 양쪽 필요 — LLM 우발 트리거 방지
- audit `file_path_arg` extension은 백워드 호환이지만 신규 tool 등록 시 `register_all`에서 명시 지정 필요
- 강의 모듈 7 (2시간 25분) 시간 블록 변경 금지 — v0.1.1 도구는 보충 모듈 또는 v0.2 강의로 다룸

## Files Touched (b972848)

- `src/humax_excel_mcp/tools/`: `template_engine.py`, `report.py`, `restore.py` (NEW), `__init__.py` (10 tools)
- `src/humax_excel_mcp/core/`: `template_bindings.py`, `template_loader.py` (NEW), `audit.py` (file_path_arg), `errors.py` (5 new codes)
- `src/humax_excel_mcp/schemas/`: `requests.py` (3 new), `responses.py` (3 new + supporting)
- `src/humax_excel_mcp/`: `server.py`, `__init__.py` (v0.1.1)
- `pyproject.toml` (v0.1.1, 10 tools)
- `scripts/build_fixture_templates.py` (NEW)
- `fixtures/templates/`: 3 xlsx + 3 sidecar JSON (NEW, committed)
- `tests/unit/`: `test_fixture_templates.py`, `test_template_engine.py`, `test_report.py`, `test_restore.py` (NEW)
- `tests/integration/`: `test_template_chain.py` (NEW), `test_mcp_server.py` (10 tools)
- `tests/e2e/test_monthly_close.py` (Step 5/6/7 extension)
- `docs/prd/mcp-design-plan.md` (Revision 4), `humax-lecture-plan.md` (10개 도구 + 보충 모듈 정책)
- `.gitignore` (fixtures/templates 예외)
