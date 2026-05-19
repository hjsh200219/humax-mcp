---
name: pandas-multi-key-diff-pattern
description: 다중 키 컬럼 diff 시 양쪽 파일 모두에 key 컬럼이 있어야 — fixture 변형 시 한쪽만 mutate 금지
type: reference
created: 2026-05-19
---

`generate_diff_candidates`처럼 전월/당월 두 파일을 (company+cc+gl_account) 다중 키로 join하는 도구의 테스트 fixture에서 흔한 함정: 한쪽 DF만 `gl_account` 값을 바꾸고 나머지를 그대로 두면 outer join에서 양쪽 모두 NaN으로 들어가거나 매칭 실패. **key 컬럼은 양쪽 fixture에 모두 존재 + 의도한 매칭/비매칭만 발생하도록 양쪽을 함께 mutate**.

```python
# OK: 양쪽 모두 mutate 후 금액 차이만 도입
prev.loc[idx, "gl_account"] = "520099"
curr.loc[idx, "gl_account"] = "520099"
curr.loc[idx, "amount_krw"] = prev.loc[idx, "amount_krw"] + 15_000_000

# NG: 한쪽만 변경하면 diff 후보 추출이 의도한 row를 못 찾음
curr.loc[idx, "gl_account"] = "520099"
```

**Why:** test_diff.py 작성 시 한쪽만 mutate해서 |10M| 임계값 테스트가 ghost row를 잡아 디버깅에 시간 소모.

**How to apply:** 다중 키 diff 도구 테스트는 "key 변경 = 양쪽 동기 변경, value 변경 = 한쪽만 변경" 규칙으로 fixture 변형. join key는 절대 한쪽만 건드리지 않는다.
