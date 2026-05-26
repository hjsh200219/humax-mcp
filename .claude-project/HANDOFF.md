---
created: 2026-05-26T13:00:00+09:00
project: humax-excel-mcp
summary: Humax 재무팀 4회×2h 자동화 강의 교안 v2 작성 (466 lines, 자동화 19회 강조). DRI 모델 (Desktop→Remote→IDE) 4단계 스택. pandoc .docx 변환본 동봉. Commit c73ceab push 완료.
---

## Session Digest

humax-excel-mcp 본 코드는 손대지 않고, 사내 재무팀 대상 4회×2h (총 8h) 자동화 강의 교안을 신규 작성. `docs/prd/humax-lecture-plan-v2.md` (466 lines) + pandoc 변환 .docx (20KB) 동봉.

설계 골격: **DRI 모델** (Desktop → Remote → IDE) 3축으로 도구 학습 곡선 분리. 4회차 스택 누적:
- **1회 Desktop full**: Claude Desktop + MCP 기본기 (humax-excel-mcp stdio 연결, 자연어 호출)
- **2회 VS Code + Claude Code**: IDE 통합 + agent 위임 패턴
- **3회 API + Git**: Anthropic API 직접 호출 + 버전 관리 워크플로
- **4회 SQL + Next.js + Vercel**: 사내 데이터 → 웹 대시보드 배포까지

핵심 메시지: 재무팀 실무자가 LLM "자동화"로 결산/리포팅을 단계적으로 자동화 (키워드 19회 반복 강조). 편집 3회 거쳐 메타 헤더 제거 / 자동화 목표 강화 / 클로징 메시지 4개 제거 (군더더기 정리).

Commit c73ceab 단일 push 완료. 본 MCP 서버 source code / tests / harness 모두 무수정.

## Progress

### 완료
- [x] `docs/prd/humax-lecture-plan-v2.md` 초안 작성 (4회×2h 구조)
- [x] DRI 모델 (Desktop→Remote→IDE) 3축 도구 분리 정의
- [x] 1회차 Desktop full (Claude Desktop + MCP 자연어 호출)
- [x] 2회차 VS Code + Claude Code (IDE agent 위임)
- [x] 3회차 Anthropic API + Git (직접 호출 + 버전 관리)
- [x] 4회차 SQL + Next.js + Vercel (데이터 → 웹 배포)
- [x] pandoc로 .docx 변환본 생성 (20KB, 사내 배포용)
- [x] 편집 3회: 메타 헤더 제거 / "자동화" 목표 강화 / 클로징 메시지 4개 제거
- [x] "자동화" 키워드 19회 노출 확인 (메시지 일관성)
- [x] commit c73ceab, push origin/main

### 미완료
- [ ] **사내 리허설 미실시**: 실제 재무팀원 대상 1회차 dry-run 필요. 2h 페이싱 / MCP 설치 시간 / Q&A 비중 검증.
- [ ] **회차별 실습 자산 분리**: 현재는 교안 1파일. 회차별 `samples/`, `exercises/`, `solutions/` 폴더 미생성.
- [ ] **사내 데이터 마스킹 샘플**: 1회차 실습용 PII 제거된 xlsx 미준비 (현재 `docs/references/` 원본은 git push 금지).
- [ ] **3회차 API key 정책**: Anthropic API 키 사내 발급/공유 절차 미정. `.env` 템플릿만 존재.
- [ ] **4회차 Vercel 권한**: 사내 계정 / 도메인 정책 미확인.

## Next Steps

1. **1회차 dry-run**: 재무팀 1-2명 대상 90분 압축 리허설. 페이싱 / MCP 설치 마찰 / Q&A 비중 측정 → 교안 미세 조정.
2. **실습 자산 폴더 구성**: `docs/lecture/session-{1..4}/{samples,exercises,solutions}/` 생성. 1회차부터 우선.
3. **PII 마스킹 샘플 1건**: `docs/references/` 원본 1개를 익명화 → `docs/lecture/samples/` 배치 (git OK).
4. **API key 정책 합의**: 3회차 전 사내 발급 절차 확정. 개인키 vs 팀키.
5. **(선택) v3 교안 분기**: 8h 압축 vs 16h 확장 (실습 비중 ↑) 양 갈래 검토.

## Blockers

없음. 교안 v2 자체는 완성. 사내 리허설 + 실습 자산은 본 세션 범위 밖.

## Watch Out

- **"자동화" 메시지 톤**: 19회 노출이 과한지 모니터. 재무팀 청중이 "AI가 일자리 뺏는다" 방어 반응 보일 가능성 — 1회차 도입에서 "보조 도구" 프레이밍 강조 필요.
- **MCP 설치 마찰**: 1회차 Claude Desktop + humax-excel-mcp 연결이 최대 병목. 사전 설치 가이드 별도 배포 권장.
- **pandoc .docx 스타일**: 기본 변환이라 사내 PPT 톤과 격차. 발표 시 .md → 본인 슬라이드 재포맷 필요.
- **버전 관리**: v2 파일명 고정. v3 작성 시 `v2`는 보존하고 신규 파일로. 덮어쓰기 금지.
- **사내 데이터 git push**: 강의 실습용 xlsx도 `.gitignore` + 정규식 스캔 2중 차단 대상. PII 마스킹 후에도 신중히.

## Files Touched

### New (docs/prd/)
- `docs/prd/humax-lecture-plan-v2.md` (466 lines, 자동화 19회)
- `docs/prd/humax-lecture-plan-v2.docx` (20KB, pandoc 변환)

### Untouched (보존)
- `src/humax_excel_mcp/**` (10 tools / core / schemas)
- `tests/**` (234 tests)
- `docs/prd/mcp-design-plan.md` (SSOT Rev 4)
- `AGENTS.md` / `CLAUDE.md` / `ARCHITECTURE.md` / harness 전체
- `scripts/**`, `.pre-commit-config.yaml`, `pyproject.toml`

## Commit / Push

- Commit: `c73ceab` — `docs: add 4-session lecture plan v2 (8h, Desktop→Code→API→Web stack)`
- Push: `c73ceab main -> main` (origin)
- 2 files added (.md 466 lines + .docx 20KB)
