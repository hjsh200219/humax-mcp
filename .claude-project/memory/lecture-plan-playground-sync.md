---
name: lecture-plan-playground-sync
description: 강의 계획서 md와 인터랙티브 강의 튜너 html은 1:1 동기화 — 한쪽만 고치면 드리프트
type: project
created: 2026-06-18
---

`docs/prd/humax-lecture-plan-v2.md`(SSOT 계획서)와 `docs/prd/lecture-plan-playground.html`(인터랙티브 강의 튜너)는 같은 회차/모듈/시간 데이터를 양쪽에 담는다. 회차·모듈을 바꾸면 **두 파일 모두** 갱신해야 한다.

- html의 `SESSIONS` 배열 = md의 회차/모듈 구조 미러. 모듈 `min` 합은 회차당 120분(1회차만 110) 목표.
- html은 단일 파일(인라인 CSS/JS, 외부 의존성 0). 컨트롤(대상/페이스/실습비율/모듈토글/산출물칩) 조정 → 라이브 보드 + 하단에 "계획서 수정 프롬프트" 생성 → 복사해 Claude에 붙여넣는 흐름.
- 검증: `python3`로 `<script>` 추출 후 `node --check`, 그리고 회차별 `min` 합 = 120 확인.
- DRI 색상: D=파랑 R=보라 I=초록 web=주황 intro=회색. 현재 2~4회차=I(초록), 5회차=web(주황).

**Why:** playground 스킬로 만든 튜너라 md만 고치면 html이 옛 회차 구조로 남아 강의 중 혼선. 사용자가 회차 구성을 반복적으로 재편함(4→5회 등).

**How to apply:** "강의 계획 N회차 …" 요청 시 md Edit + html `SESSIONS`/프리셋/산출물칩/프롬프트 문구까지 같이 수정하고, node --check + 120분 합으로 검증 후 `open`으로 브라우저 새로고침. 척추 모델은 [[dri-model-claude-ecosystem-pedagogy]].
