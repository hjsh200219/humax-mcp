---
created: 2026-07-09T00:00:00+09:00
project: humax-mcp
summary: 강의 4회차 Embedding·RAG 모듈(4-7) 추가 — Supabase pgvector 연계, 시간 3h로 증가(조정 보류)
---

## Session Digest

사용자 요청으로 `docs/prd/humax-lecture-plan-v2.md` 4회차에 **모듈 4-7 Embedding·RAG** 신설:
- Embedding = 텍스트→벡터(코사인 유사도), RAG = 질문→벡터 검색→LLM 컨텍스트 주입(환각↓)
- **Supabase pgvector** 확장으로 구현 (모듈 4-5 Supabase 직결 — 별도 인프라 불필요)
- Humax 실무 매칭: 적요→계정과목 자동 분류, SOP/규정 RAG 질의
- 회차 요약표 4회 행 갱신 (Embedding/RAG + pgvector 산출물 추가)

시간 초과 경고했으나 사용자가 **"시간 조정하지 말고"** 지시 → 조정 보류. 4회 = 7모듈 = 180분(3h), 2h 예산 1h 초과 상태로 확정.

코드 변경 0건(.md만) → 검증/harness-gc 자동 스킵, 문서 커밋·푸시. 이번엔 원격 분기 없이 clean push.

## Progress

- ✅ 모듈 4-7 Embedding·RAG 신설 (Supabase pgvector 뒤 배치)
- ✅ 회차 요약표 4회 행 갱신
- ✅ 커밋·푸시 완료 (`3e824f2`, clean fast-forward onto `a189981`)

## Next Steps

1. **`docs/prd/lecture-plan-playground.html` 동기화** — md↔html 1:1 불변식(memory `lecture-plan-playground-sync`)이 더 벌어짐. html엔 (a) 3회차 SAP OData 3건 잔존 (b) 하네스 모듈 4-1 미반영 (c) **이번 모듈 4-7 Embedding·RAG 미반영**. 두 파일 갱신 + `node --check` + 회차당 시간 합 재검증 필요
2. 4회차 시간 합 재검토 — 사용자가 조정 보류했으나 3h 확정 상태. 강의 당일 SQL/SQLite 축소 or 4-6/4-7 숙제 이관 실시간 판단 여지
3. 3회차 실행 로그에 실제 진행일·모듈 채우기 (여전히 계획 변경만 기록됨)

## Blockers

없음.

## Watch Out

- **md ↔ html 동기화 미완 (누적)**: 회차/모듈 3건(SAP OData 이월, 하네스 4-1, Embedding/RAG 4-7)이 html에 미반영. 반드시 두 파일 갱신 + `node --check` + 회차당 시간 합 검증 (memory `lecture-plan-playground-sync`)
- **문서-코드 드리프트**: 도구 실제 **11개**(`update_fc_month_report` 병합)인데 `AGENTS.md`/`CLAUDE.md`는 "도구 10개" 표기 (README만 11). 실파일 `AGENTS.md` 도구 표 갱신 필요 — `CLAUDE.md`는 심볼릭 링크
- 강의 진행 기록(일회성)은 Memory 저장 안 함 — repo 문서가 SSOT
- main 직접 push — 원격 분기 시 `git pull --rebase` 후 push

## Files Touched

- `docs/prd/humax-lecture-plan-v2.md` — 모듈 4-7 Embedding·RAG 추가 + 요약표 (22+/1-)
- `.claude-project/HANDOFF.md` — 본 파일
