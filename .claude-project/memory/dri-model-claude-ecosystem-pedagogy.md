---
name: dri-model-claude-ecosystem-pedagogy
description: DRI (Desktop/Remote/IDE) 3단계 모델 — Claude 생태계 도입 교육의 척추 구조
type: reference
created: 2026-05-26
---

실무자 대상 Claude 생태계 교육 시, "채팅창 + 파일 업로드"라는 1차원 인식을 깨기 위한 진화 경로 모델.

- **D (Desktop)**: Claude Desktop의 Chat / Cowork / Extension / Skill / MCP / Schedule / Dispatch / Computer Use / Live Artifact — 학습 곡선 낮음
- **R (Remote)**: Schedule + Dispatch로 무인 실행 (트리거 → 결과 자동) — 학습 곡선 중간
- **I (IDE)**: Claude Code (Terminal / VS Code / Desktop 내부) — 본인이 도구 빌드 — 학습 곡선 중간~높음

자동화 정의 분기점: "Claude에게 매번 물어봄(수동 보조)" vs "트리거(시간/이벤트/명령) → 결과(파일/DB/알림) 자동 실행(자동화 자산)". 매 회차 산출물은 후자 기준 충족 필수.

5회 강의 매핑 (2026-06-18 4→5회 재편): 1회=D풀+R도입 / 2회=I본격 / 3회=Playground·Git·환경변수·API·SAP OData·MCP테스트 / 4회=SQL·DB·Supabase / 5회=Vercel·웹·console.log·Playwright E2E.

**Why:** 기존 v1 강의(9.5h+10h, "토큰 한계" 진단 중심)는 문제 해결 강의였지만, v2는 "생태계 전환" 강의로 프레이밍 자체가 다름. 실무자 인식 전환에는 단순 기능 나열보다 진화 경로(D→R→I)가 효과적.

**How to apply:** Humax 후속 강의 / 타 재무팀 강의 / 사내 AX 컨설팅 자료 작성 시 DRI를 그대로 척추로 사용. 회차별 산출물 평가는 "자동화 자산(트리거→결과)" 기준만 적용. 1회차 hook으로 D vs I 학습 곡선 비교표를 먼저 깔면 동기부여 정렬됨.

**운영 메모 (2026-06-04):** 강의 실제 진행 기록은 `docs/prd/humax-lecture-plan-v2.md` 끝 "부록: 실행 로그"에 "### N회차 (날짜)" 형식으로 누적 (계획서 1파일 유지, 계획≠실행 섹션 분리). 2회차 실제 진행: Git/Node.js 설치 → VS Code(Claude Code+Codex/Gemini, 테트리스 실습) → PRD/MD/JSON 소개 → OMC+ralph/ralplan → humax-mcp 설치.

**갱신 (2026-06-18):** 강의 4→5회 재편 완료. 3회차에 Git clone/commit/push 기초(3-2)·GitHub(3-3) 명시(이전 "3회차 예정" git 기초 항목 반영), SAP OData(3-6)는 2회차→3회차 이동, MCP 로그분석 테스트(3-7)는 4회차→3회차 이동, 3회차 첫 모듈=Playground 스킬 소개(3-1). 인터랙티브 "강의 튜너" `docs/prd/lecture-plan-playground.html` 신설 — 계획서 md와 1:1 동기화 유지 필요. 상세: [[lecture-plan-playground-sync]]. 회차별 모듈 시간 합 120분 유지(1회차만 110).
