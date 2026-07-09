---
created: 2026-07-09T00:00:00+09:00
project: humax-mcp
summary: 강의 4회차 Embedding·RAG 모듈(4-7) 추가 + 강의 튜너 html을 계획서 v2와 완전 동기화 (md↔html 드리프트 해소)
---

## Session Digest

1. `docs/prd/humax-lecture-plan-v2.md` 4회차에 **모듈 4-7 Embedding·RAG** 신설 (Supabase pgvector 연계, 적요→계정과목 분류·SOP RAG 질의). 시간 3h로 증가 — 사용자 "시간 조정하지 말고" 지시로 조정 보류.
2. `docs/prd/lecture-plan-playground.html`(강의 튜너)를 md SSOT에 맞춰 **완전 동기화**. 그동안 누적된 드리프트 3건(SAP OData 3→4 이월, 하네스 4-1 신설, Embedding·RAG 4-7) 모두 반영. 3회차 9→8모듈 재번호, 4회차 4→7모듈. `node --check` OK.

메타 파일(.md/.html doc)만 변경 → Python lint/test/harness-gc 미적용. 각각 clean push.

## Progress

- ✅ 모듈 4-7 Embedding·RAG 신설 (md) — `3e824f2`
- ✅ 강의 튜너 html md와 1:1 동기화 (드리프트 3건 해소) — `8fe221b`
- ✅ 검증: node --check OK, 회차별 min 합 md 일치 (1회 110·2회 120·3회 105·4회 180·5회 120)
- ✅ 커밋·푸시 완료 (clean fast-forward)

## Next Steps

1. 4회차 시간 3h 확정 상태 — 강의 당일 SQL/SQLite 축소 or 4-6/4-7 숙제 이관 실시간 판단 여지 (사용자가 사전 조정 보류)
2. 3회차 실행 로그에 실제 진행일·진행 모듈 채우기 (여전히 계획 변경만 기록됨)
3. **문서-코드 드리프트**: 도구 실제 **11개**인데 `AGENTS.md`/`CLAUDE.md`는 "도구 10개" 표기. 실파일 `AGENTS.md` 도구 표 갱신 (`CLAUDE.md`는 심볼릭 링크)

## Blockers

없음.

## Watch Out

- **md ↔ html 동기화 (이번 세션 해소, 유지 필수)**: 회차/모듈 변경 시 두 파일 모두 갱신 + `node --check` + 회차별 min 합 검증 (memory `lecture-plan-playground-sync`). 현재 완전 일치 상태
- 회차 min 합 120 목표는 aspirational — md가 SSOT. 현재 3회 105·4회 180은 의도된 상태(SAP 이월·4회 3h)
- 강의 진행 기록(일회성)은 Memory 저장 안 함 — repo 문서가 SSOT
- main 직접 push — 원격 분기 시 `git pull --rebase` 후 push

## Files Touched

- `docs/prd/humax-lecture-plan-v2.md` — 모듈 4-7 Embedding·RAG + 요약표 (`3e824f2`)
- `docs/prd/lecture-plan-playground.html` — SESSIONS 3·4회 재작성, 프롬프트 문구 (`8fe221b`)
- `.claude-project/HANDOFF.md` — 본 파일
