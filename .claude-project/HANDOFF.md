---
created: 2026-05-19T12:54:00+09:00
project: humax-mcp
summary: GitHub Private Repo 생성 + PRD/강의 계획 + scaffolding 초기 push 완료. 도구 7개 spec 합의됨, 코드 스켈레톤은 미작성.
---

## Session Digest

Humax AX 컨설팅 강의 + MCP 도구 7개 설계 완료. 4 iteration ralplan consensus (Planner/Architect/Critic) 통과. `hjsh200219/humax-mcp` Private repo 초기 push (5 files, 2594 insertions).

핵심 산출:
- `docs/prd/mcp-design-plan.md` (1875 lines, Revision 3) — 도구 7개 상세 spec + Pre-mortem 7 + 안전 정책 P1-P5
- `docs/prd/humax-lecture-plan.md` — 2차 (Cowork + MCP, 9h25min) + 3차 (Code/바이브, 10h) 강의 계획
- `.gitignore` / `LICENSE` / `README.md` 셋업

## Progress

### 완료
- [x] RFP 분석 (Q1 명령어 / Q2 결과물 품질 / Q3 유사 업무 확장)
- [x] 5개 에러 + 한계 2종 진단 (토큰 폭발 단일 원인 입증)
- [x] 26BP raw 직접 검증 (적요 60% / 배부율 / CC 마스터 위치 확정)
- [x] xlsx vs CSV vs JSONL 용량 실측 (0.75x / 1.7x)
- [x] 강의 계획서 (2차 9h25min + 3차 10h)
- [x] MCP 설계서 (도구 7개 + Live Artifact + Pre-mortem 7)
- [x] 4 iteration ralplan consensus (APPROVE)
- [x] 5 minor 모두 plan v3에 반영
- [x] GitHub Private Repo 생성 + 초기 push

### 미완료
- [ ] 코드 스켈레톤 작성 (`pyproject.toml` + `src/humax_excel_mcp/` 7 tool stub)
- [ ] `scripts/install.ps1` / `scripts/update.ps1` 실제 작성
- [ ] `.env.example` 작성 (EXCHANGE_RATE_API_KEY 등)
- [ ] GitHub Actions CI (`.github/workflows/test.yml`)
- [ ] CONTRIBUTING.md + CHANGELOG.md
- [ ] 첫 도구 구현 (`get_exchange_rates` 추천 — 외부 의존 적음, 즉시 테스트 가능)
- [ ] 합성/마스킹 데이터 fixture (`tests/fixtures/`)
- [ ] Claude Desktop 등록 가이드 문서 (`docs/deploy-guide.md`)

## Next Steps

1. **pyproject.toml 작성** — mcp / openpyxl / pandas / pydantic / python-dotenv / httpx / pytest 의존성 명시
2. **`src/humax_excel_mcp/server.py` 스켈레톤** — FastMCP entry, 도구 7개 import
3. **`tools/exchange.py` 우선 구현** — 외부 의존 가장 적음, 한국수출입은행 API 호출 + JPY(100) 정규화 + 12h 캐시
4. **fixture 데이터 생성** — 합성 raw (5-10 행 샘플) for unit test
5. **`tools/extract.py` 구현** — 강의 모듈 7 hands-on 메인 도구
6. **`scripts/install.ps1` Windows 자동 설치 스크립트** — Claude Desktop config 자동 등록
7. **GitHub Actions CI 추가** — pytest + PII 정규식 스캔
8. **첫 강의 실 데모용 통합 테스트** — `extract_filtered + verify_sums` chained

## Blockers

- 없음. 모든 결정 완료, 다음 작업은 실 구현만 남음.
- 다만 Humax 사내 IT 확인 필요 (배포 단계):
  - 사내 GitHub 접근 허용 (✅ 확정)
  - `oapi.koreaexim.go.kr` 방화벽
  - Anthropic API 외부 호출 정책 (DPA/ZDR)
  - Claude Desktop `config.json` 편집 권한

## Watch Out

1. **사내 데이터 push 금지** — `.gitignore`에 `.xlsx` 강제. 실수로 raw 파일 commit 안 되도록 매 커밋 전 `git status` 확인
2. **API 키 노출 금지** — `EXCHANGE_RATE_API_KEY`는 `.env`만, 절대 코드/문서에 hardcoding 금지
3. **원본 훼손 금지** — `write_cells` / `update_allocation_rates` 구현 시 백업 강제 + `output_path != file_path` 검증 + dry_run 동작 우선 검증
4. **String-to-float (M6)** — 한국수출입은행 API는 `"1,393.00"` 콤마 포함 string 반환. `.replace(",","")` 후 `float()` 처리
5. **JPY(100) 정규화** — 100단위 통화는 `unit_multiplier=100` 필드 추가 + `deal_bas_r_per_unit` 1단위 환율 계산
6. **휴일 fallback 7일** — 한국 장기 연휴 (설/추석 ~5일) 커버 가능. 더 늘리지 않음
7. **컨텍스트 토큰 절약** — raw 분석 시 시트/월/회사/컬럼 분할 필수. raw 통째 LLM 전달 금지
8. **iter 3-4 carryover M2/M3** — plan에는 반영했으나 코드 구현 시 빠뜨리지 않도록 sprint checklist에 명시

## Files Touched

세션 산출:
- `/Users/hoshin/workspace/humax-mcp/.gitignore` (신규)
- `/Users/hoshin/workspace/humax-mcp/LICENSE` (신규)
- `/Users/hoshin/workspace/humax-mcp/README.md` (신규)
- `/Users/hoshin/workspace/humax-mcp/docs/prd/mcp-design-plan.md` (humax/ 에서 복사)
- `/Users/hoshin/workspace/humax-mcp/docs/prd/humax-lecture-plan.md` (humax/ 에서 복사)

원본 (humax/):
- `/Users/hoshin/workspace/humax/docs/prd/mcp-design-plan.md` (4 iter ralplan 합의, Revision 3, 1875 lines)
- `/Users/hoshin/workspace/humax/docs/prd/humax-lecture-plan.md` (모듈 7 환율 실습 반영)
- `/Users/hoshin/workspace/humax/docs/prd/consulting-plan.md` (초기 컨설팅 plan)
- `/Users/hoshin/workspace/humax/docs/rfp/.omc/plans/mcp-architect-review.md` (4 iter 검토)
- `/Users/hoshin/workspace/humax/docs/rfp/.omc/plans/mcp-critic-review.md` (4 iter 검토)

## 컨텍스트 인계 노트

새 세션 시작 시 `.claude-project/HANDOFF.md` + memory 3개 필수 로드.

- `humax-closing-workflow.md` — Humax 7단계 + 5 에러 진단
- `bp26-schema-key-findings.md` — 26BP raw 컬럼 매핑
- `mcp-tools-overview.md` — 도구 7개 + 안전 정책 + Pre-mortem

다음 세션 prompt 예시:
> ".claude-project/HANDOFF.md 읽고 이어서 작업해줘. 첫 도구로 `get_exchange_rates` 구현 시작."
