---
created: 2026-07-01T09:34:12+09:00
project: humax-mcp
summary: 강의 3회차 SAP OData 미진행분 4회차 이월 + 4회차 초반 하네스 설정(CLAUDE.md 역할) 모듈 신설
---

## Session Digest

3회차 강의에서 "모듈 3-6: SAP OData 소개"를 진행 못함. `docs/prd/humax-lecture-plan-v2.md`에서:
- **3회차**: 모듈 3-6 SAP OData 제거 → 3-7~3-9를 3-6~3-8로 재번호 (총 8모듈)
- **4회차**: 초반에 모듈 4-1 하네스 설정 신설 + 모듈 4-2로 SAP OData 이월 → 기존 4-1~4-4를 4-3~4-6으로 재번호 (총 6모듈)
- 신설 모듈 4-1 핵심 = **CLAUDE.md 역할(Claude 관점)**: 매 세션 컨텍스트 자동 로드되는 프로젝트 지시서(장기 기억), `CLAUDE.md → AGENTS.md` 심볼릭 링크로 Claude·Codex·Gemini 공용, `/init`로 초안 생성
- 인트로(라인 34)·회차 요약표·회차 제목 동기화, 3회차 실행 로그에 계획 변경 기록

코드 변경 0건(.md만) → 검증/harness-gc 자동 스킵, 문서 커밋·푸시. push 시 non-fast-forward → `git pull --rebase` 후 재push 성공.

## Progress

- ✅ 3회차 SAP OData 모듈 제거 + 3-7~3-9 → 3-6~3-8 재번호
- ✅ 4회차 하네스 설정 모듈(4-1) 신설 — CLAUDE.md/AGENTS.md 역할
- ✅ 4회차 SAP OData 이월(4-2) + 4-1~4-4 → 4-3~4-6 재번호
- ✅ 요약표/인트로/제목/실행로그 동기화
- ✅ 커밋·푸시 완료 (`0ba0484`, rebase onto origin `04a5f6a`)

## Next Steps

1. **`docs/prd/lecture-plan-playground.html` 동기화** — md는 SAP OData를 4회로 옮겼으나 HTML(강의 튜너)엔 여전히 3회차 SAP OData 3건 잔존 + 하네스 모듈 미반영. md↔html 1:1 불변식 깨짐 (memory `lecture-plan-playground-sync`). 두 파일 갱신 + `node --check` + 회차당 시간 합 재검증 필요
2. 4회차 시간 합 재검토 — 6모듈 150분(15+15+30+25+35+30) = 2h 초과 30분. SQL/SQLite 축소 or Supabase 적재(4-6) 숙제 이관 검토 (사용자 결정 대기)
3. 3회차 실행 로그에 실제 진행일·진행 모듈 채우기 (현재 날짜 미상 → 계획 변경만 기록)

## Blockers

없음.

## Watch Out

- **문서-코드 드리프트**: 원격서 `update_fc_month_report` 병합되어 도구 **11개**인데 `AGENTS.md`/`CLAUDE.md`는 여전히 "도구 10개" 표기 (README만 11 갱신됨). 다음 문서 세션에서 실파일 `AGENTS.md` 도구 표 갱신 필요 — `CLAUDE.md`는 심볼릭 링크라 실파일 수정
- **md ↔ html 동기화 필수**: 회차/모듈 바꾸면 두 파일 모두 갱신 + `node --check` + 회차당 시간 합 검증 (memory `lecture-plan-playground-sync`)
- 강의 진행 기록(일회성)은 Memory 저장 안 함 — repo 문서가 SSOT
- main 직접 push — 원격 분기 시 `git pull --rebase` 후 push (이번에도 원격 신규 커밋과 분기 → rebase 처리)

## Files Touched

- `docs/prd/humax-lecture-plan-v2.md` — 3회 SAP OData 제거·4회 하네스+SAP OData 이월 (69+/35-)
- `.claude-project/HANDOFF.md` — 본 파일
