---
created: 2026-05-19T13:32:00+09:00
project: humax-mcp
summary: humax-excel-mcp v0.1 — 7 MCP 도구 TDD 구현 완주 (130 tests green, push b194dc6)
---

## Session Digest

humax-excel-mcp v0.1 MVP를 Ralph TDD 사이클로 완주했다. 14개 유저 스토리 (US-001~US-014)를 모두 통과시켰고, pyproject 스캐폴딩부터 7개 핵심 MCP 도구(extract_filtered, verify_sums, write_cells, generate_diff_candidates, get_allocation_rates, update_allocation_rates, get_exchange_rates), pydantic v2 schemas, 합성 26BP fixtures, FastMCP 서버 등록, JSONL 감사 로그, E2E 월결산 체인까지 구현. 총 130 테스트(unit 126 / integration 3 / e2e 1) 9.55초에 그린. 4044 라인이 신규 추가됐고 단일 커밋 `b194dc6 feat: implement humax-excel-mcp v0.1`로 origin/main에 푸시.

## Progress

- [x] US-001~014 (14/14 스토리) — 7개 MCP 도구 + core/schemas/tests
- [x] pydantic v2 스키마 (bp26 65컬럼 매핑, requests/responses)
- [x] core 유틸 (excel_io, backup-sha256, token_guard, artifact_hints, audit, errors)
- [x] 합성 26BP fixtures (144 detail rows + 총합계, 배부율 합=100)
- [x] FastMCP server.py + JSONL 감사 로그
- [x] E2E 체인: extract→verify→write→diff→alloc_get/set→verify 그린
- [x] pytest-httpx 환율 API 모킹 (7일 fallback, 12h 캐시, JPY/100 정규화)
- [x] Architect 리뷰 APPROVED, ai-slop-cleaner 패스 + ruff clean
- [x] origin/main push (b194dc6)
- [ ] 실배포 갭 10종 (PRD §9.5 GitHub Private 배포)
- [ ] v0.2 항목 (적요 분류, 건별 배부, restore_backup, PII/금액 마스킹)
- [ ] v0.3/v0.4 (SAP 연동, cron 자동화)

## Next Steps

1. **실배포 갭 10종** (PRD §9.5 기반):
   1. `scripts/install.ps1` + `install.sh` (각 PC 초기 설치)
   2. `scripts/update.ps1` (git pull + pip upgrade + Claude Desktop 재시작 안내)
   3. Claude Desktop config 자동 등록 PowerShell (`%APPDATA%\Claude\claude_desktop_config.json`)
   4. `.github/workflows/test.yml` CI (pytest + ruff + PII 정규식 스캔)
   5. `humax_config/.local` CC 마스터 분리 (gitignore)
   6. 배부율 마스터 submodule 또는 .env 분리
   7. `oapi.koreaexim.go.kr` 사내 방화벽 IT 사전 협의
   8. STDIO 실 핸드셰이크 smoke test (`python -m humax_excel_mcp.server` 실 stdio 검증)
   9. audit 로그 chmod 600 OS별 실측
   10. SOW에 hypercare 책임 소재 명시
2. **v0.2 우선순위**: `restore_backup` (안전망 시급) → `classify_by_text` (적요 PoC H1/H2/H3) → `allocate_costs` 건별 배부 → `mask_pii`/`mask_amounts` → CC 마스터 시트 연동
3. **운영 준비**: `pytest --cov` 커버리지 게이트, Windows 환경 smoke test, 실 26BP 1건 dry-run 검증

## Blockers

- 실 26BP raw 데이터 미접근 (합성 fixture만 검증 완료) — 실파일 컬럼 헤더 변형 케이스 미확인
- 사내 GitHub Org repo 생성 권한·정책 (사내 IT 확정 대기)
- `oapi.koreaexim.go.kr` 사내 방화벽 허용 여부 미확인
- Anthropic DPA/ZDR 정책 검토 (Claude Desktop 외부 호출)

## Watch Out

- pytest-httpx 0.36 API는 `url=re.compile(...)` 사용 (NOT `url__regex=`) — memory: pytest-httpx-036-api
- 스키마 mismatch 체크는 df-empty 체크보다 먼저 실행 — memory: validation-order-schema-first
- exchange API fallback 모킹은 1 initial + 7 attempts = 8 mocks 필요
- `.env`에 라이브 EXCHANGE_RATE_API_KEY 존재 — 테스트는 반드시 monkeypatch + `config.load_env()` bypass로 API_KEY_MISSING 검증
- write/alloc_set은 `output_path != file_path` 강제 + 항상 backup 선행 — memory: write-tool-output-path-safety
- diff 후보는 양쪽 파일 모두 key cols(company+cc+gl) 존재해야 함 — memory: pandas-multi-key-diff-pattern
- Railway/외부 클라우드 배포는 SAP 데이터 외부 전송 = 거버넌스 위반. 사내 서버 또는 stdio 유지

## Files Touched

- `pyproject.toml`, `.env.example`, `progress.txt`
- `src/humax_excel_mcp/`: `server.py`, `config.py`, `__init__.py`
- `src/humax_excel_mcp/tools/`: `extract.py`, `verify.py`, `write.py`, `diff.py`, `allocation_get.py`, `allocation_set.py`, `exchange.py`, `__init__.py`
- `src/humax_excel_mcp/schemas/`: `bp26.py`, `requests.py`, `responses.py`, `__init__.py`
- `src/humax_excel_mcp/core/`: `errors.py`, `excel_io.py`, `backup.py`, `token_guard.py`, `artifact_hints.py`, `audit.py`, `__init__.py`
- `tests/`: `conftest.py` + 13 unit tests + integration/`test_mcp_server.py` + e2e/`test_monthly_close.py`
