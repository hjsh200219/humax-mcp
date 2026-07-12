---
name: verify-sums-org-prefix-rollup
description: verify_sums 중간 계층은 org prefix 매칭 rollup — expected=actual 가짜 PASS 금지 + pd.isna 명시 처리
type: project
created: 2026-07-12
---

verify_sums의 기존 중간 계층(사업부/대조직/중조직) 검증은 expected와 actual에 **같은 값을 대입해 항상 PASS인 가짜 검증**이었다 (테스트도 통과, 실검증 0건).

교체 구현 (`src/humax_excel_mcp/tools/verify.py`):
- 각 소계 행의 **비어있지 않은 org 컬럼 prefix**로 소조직 상세 행을 스코핑해 합산 대조.
- 해당 계층의 소계 행이 없으면 `SKIPPED` 상태 — PASS로 뭉개지 않고 "검증 안 됨"을 구분 표기. summary에 skipped 카운트 포함.

**pandas 함정 (일반 교훈):** `raw_v or ""` 패턴에서 NaN(float)은 truthy → `nan or ""`가 nan을 반환하고 `str()` 시 `"nan"` 문자열이 prefix 스코핑에 유입되는 버그. 반드시 명시 처리:
```python
v = "" if raw_v is None or pd.isna(raw_v) else str(raw_v).strip()
```
(`tools/verify.py` `_check_rollup` 패턴)

**Why:** 가짜 PASS는 최악의 검증 — 존재만으로 신뢰를 만들고 실제로는 아무것도 잡지 않는다. expected와 actual이 독립 경로에서 나오는지가 검증 코드의 첫 번째 리뷰 포인트.

**How to apply:**
- 계층/합계 검증 추가 시 expected 소스와 actual 소스가 서로 다른 데이터 경로인지 먼저 확인.
- 데이터 부재로 검증 불가한 계층은 FAIL도 PASS도 아닌 SKIPPED로 상태 분리.
- pandas 값의 문자열 정규화는 `pd.isna` 명시 체크 — truthiness(`or ""`)에 의존 금지.

**관련:** [[validation-order-schema-first]]
