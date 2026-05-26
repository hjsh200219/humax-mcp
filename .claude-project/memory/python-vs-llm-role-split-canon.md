---
name: python-vs-llm-role-split-canon
description: "숫자는 Python, 말은 LLM" — 결정론·산술·안전은 Python, 의도파악·자연어·문맥은 LLM. humax-mcp 정체성 핵심 메시지
metadata:
  type: project
  created: 2026-05-26
---

humax-mcp의 존재 이유를 외부에 설명할 때 항상 다음 축으로 분리:

- **Python 담당**: 결정론, 산술, 백업/sha256, 셀 좌표 쓰기, 필터·피벗·누계, 안전 정책 강제
- **LLM 담당**: 사용자 의도 파악, 도구·파라미터 선택, 결과 해석·보고, 적요 윤문, 에러 안내
- **Python 결정 근거 4가지**: 결정론 / 감사추적 (JSONL) / 안전정책 (코드 강제) / 비용·속도

**Why:** 사용자가 `docs/prd/data-flow.md` 4회 iteration 끝에 이 비교 섹션을 핵심 차별화로 확정 (2026-05-26). CLAUDE.md 안전 정책 P2("결정론은 Python")의 사용자 대면 표현. 강의/영업/온보딩 자료 작성 시 동일 프레이밍 재사용 필요.

**How to apply:** 신규 문서(PRD/README/강의/영업자료)에서 "왜 MCP가 필요한가?" 답할 때 이 비교 표를 그대로 인용. 표 양식: 문제별 행 + Python/LLM 컬럼 2개. 실제 사고 사례 (3,000원 오차) 예시 함께 제시. SSOT는 [data-flow.md](../../docs/prd/data-flow.md) "Python 처리 vs LLM 직접 처리 비교" 섹션.
