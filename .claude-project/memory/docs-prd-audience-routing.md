---
name: docs-prd-audience-routing
description: docs/prd/ = 사용자/이해관계자용, docs/design-docs/ = 개발자용. 청중 기준으로 디렉터리 분기
metadata:
  type: project
  created: 2026-05-26
---

문서 위치 결정 기준:

- `docs/prd/` — **비개발자 청중** (실무자·강의 수강생·이해관계자). 비유/그림/플로우 위주. `mcp-design-plan.md` (스펙 SSOT), `data-flow.md` (워크플로우), `humax-lecture-plan*.md` (강의안)
- `docs/design-docs/` — **개발자 청중**. 레이어 규칙·디자인 결정 기술 정밀도 우선
- `docs/exec-plans/` — 실행 계획·트래커
- `docs/harness/` — 에이전트 셋업/원칙
- root `README/ARCHITECTURE` — 최상위 진입

**Why:** `data-flow.md` 작성 시 `docs/prd/` 선택 — 비개발자도 읽을 수 있어야 한다는 사용자 명시 요구 (2026-05-26). 스펙(mcp-design-plan)과 흐름(data-flow)이 같은 디렉터리에 공존 = "사용자 대면 산출물 집합" 정의.

**How to apply:** 신규 문서 작성 전 청중부터 확인. 비개발자/혼합 청중 → `docs/prd/` + [[non-dev-doc-style-analogy-first]] 포맷 적용. 순수 개발자 → `docs/design-docs/`. 결정 시 AGENTS.md "문서 인덱스" 섹션 업데이트 검토.
