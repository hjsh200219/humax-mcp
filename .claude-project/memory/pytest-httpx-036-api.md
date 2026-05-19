---
name: pytest-httpx-036-api
description: pytest-httpx 0.36 URL 매칭은 url=re.compile(...) 형태로 (url__regex 아님)
type: reference
created: 2026-05-19
---

pytest-httpx 0.36에서 외부 HTTP 호출 mock 시 정규식 URL 매칭은 `url=re.compile(pattern)` 으로 전달한다. 이전 버전의 `url__regex=pattern` Django-style lookup은 인식되지 않고 조용히 모든 URL에 매칭되어 의도치 않은 mock이 걸린다.

```python
# OK
httpx_mock.add_response(url=re.compile(r"https://oapi\.koreaexim\.go\.kr/.*"), json=[...])

# NG (silently matches anything)
httpx_mock.add_response(url__regex=r"https://oapi\.koreaexim\.go\.kr/.*", json=[...])
```

추가 함정: fallback 체인 mock 카운트 = 1 (initial) + N (재시도) 이므로 7일 fallback 소진 테스트는 mock 8개 등록.

**Why:** test_exchange.py 작성 중 `url__regex`가 에러 없이 모든 호출에 매칭되어 fallback 로직 검증이 무력화됨.

**How to apply:** pytest-httpx로 외부 API mock 작성 시 `url=re.compile(...)` 형태만 사용. fallback/retry 테스트는 `(1 + max_attempts)` 만큼 mock 등록.
