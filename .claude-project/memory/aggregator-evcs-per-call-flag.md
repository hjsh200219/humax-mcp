---
name: aggregator-evcs-per-call-flag
description: EVCS 가상행 expansion 은 per-call expand_evcs flag — additive is_virtual 컬럼 패턴 거부
type: reference
created: 2026-05-19
---

aggregator.aggregate_to_bp26(df, target_month, *, expand_evcs=False):
- `expand_evcs=False` (default): base aggregation only (조직 단위 그대로)
- `expand_evcs=True`: rate-bearing rows × rate/100 → virtual EVCS국내/EVCS해외 rows. **NO base rows in output.**

generate_report 라우팅:
- evcs_account → expand_evcs=True
- humax_allocation / humax_account → expand_evcs=False

**Why:** Plan v0.1.2 초안의 additive 패턴 (`is_virtual` column + binding filter) 은 architect 검토에서 **leak bug** 발견. humax_allocation/humax_account binding 이 division/company 로 filter — `is_virtual=True` 행 차단 못 함. 가상행이 base 템플릿에도 leak → double-count.

per-call flag 는 구조적으로 두 호출 결과를 단일 DataFrame 으로 섞을 수 없음. caller 가 명시적 선택. 단일 책임 원칙 충족.

**How to apply:**
- 신규 derivative row 추가 시 always-additive 회피
- 같은 input/같은 함수에서 다른 output shape 필요 시 named flag (Literal) 사용
- 호출자 명시 책임 — 잘못 사용 시 즉시 빈 출력 visible failure (silent corruption 없음)
- 관련: ADR-003 in .omc/plans/v012-real-data-adapter.md

**관련:** [[raw-vs-aggregated-schema-separation]]
