---
name: non-dev-doc-style-analogy-first
description: 비개발자 대상 문서는 비유 + ASCII 다이어그램 + Before/After 표 우선, 코드 스니펫 최소화
metadata:
  type: feedback
  created: 2026-05-26
---

비개발자 대상 문서(`docs/prd/` 중 데이터 흐름·워크플로우·온보딩류) 작성 시 다음 포맷 우선:

- 각 단계마다 "비유:" 문장 1개 (도서관/장부/편지/지문 등 일상 비유)
- ASCII 박스 다이어그램으로 입력→가공→출력 시각화
- Before/After 표로 변환 결과 대비
- 코드 스니펫 대신 의사코드·표·플로우 사용
- 비교 표 (예: LLM vs Python)로 trade-off 명시
- 마지막에 FAQ + "코드 위치 (개발자용 참고)" 부록 분리

**Why:** 사용자가 [[docs-prd-audience-routing]]에서 `data-flow.md`를 4회 반복 수정하며 "기술 → 비개발자" 방향으로 단순화 요구. 초안의 코드 중심 설명을 거부하고 비유+그림+비교표 형태에서 수렴.

**How to apply:** PRD/Flow/Onboarding 문서 작성 시 1차 초안부터 이 포맷 적용. 개발자용 디테일은 끝에 "코드 위치" 표로 분리. `docs/design-docs/`는 기술 정밀도 우선이므로 이 규칙 미적용.
