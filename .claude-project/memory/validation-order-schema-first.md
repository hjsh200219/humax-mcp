---
name: validation-order-schema-first
description: pandas/openpyxl 데이터 검증 시 schema-mismatch 체크는 empty 체크보다 먼저
type: reference
created: 2026-05-19
---

Excel/DataFrame 도구에서 입력 검증 순서를 잘못 잡으면 schema 오류를 empty 응답으로 마스킹한다. 올바른 순서:

1. SCHEMA_MISMATCH (필요 컬럼 존재 여부) — 먼저
2. EMPTY_RESULT (필터 후 행 0) — 다음
3. 비즈니스 룰 (rate_sum, tolerance 등) — 마지막

이유: 컬럼이 없으면 `df.empty == True`가 되어 사용자가 "필터가 너무 좁다"로 오해. 실제 원인은 헤더 변경/시트 잘못 지정.

```python
# allocation_get.py 패턴
missing = REQUIRED_COLS - set(df.columns)
if missing:
    raise SchemaMismatchError(missing=list(missing))  # 먼저
if df.empty:
    return AllocationRatesResult(allocations=[], ...)  # 그 다음
```

**Why:** allocation_get.py 초기 구현에서 empty 체크를 먼저 두어 schema 깨진 케이스가 정상 empty로 반환되어 실무자 디버깅 어려움.

**How to apply:** 신규 read/diff 도구 작성 시 검증 순서 = 구조(schema) → 데이터(empty) → 룰(business). 테스트도 동일 순서로 케이스 작성.
