---
name: pytest-httpx-036-api
description: pytest-httpx는 url=re.compile 매칭 + 응답 재사용 없음(요청 수=등록 수) + 병렬 fallback은 searchdate별 regex 등록
type: reference
created: 2026-05-19
updated: 2026-07-12
---

pytest-httpx 0.36에서 외부 HTTP 호출 mock 시 정규식 URL 매칭은 `url=re.compile(pattern)` 으로 전달한다. 이전 버전의 `url__regex=pattern` Django-style lookup은 인식되지 않고 조용히 모든 URL에 매칭되어 의도치 않은 mock이 걸린다.

```python
# OK
httpx_mock.add_response(url=re.compile(r"https://oapi\.koreaexim\.go\.kr/.*"), json=[...])

# NG (silently matches anything)
httpx_mock.add_response(url__regex=r"https://oapi\.koreaexim\.go\.kr/.*", json=[...])
```

## 응답 재사용 없음 (2026-07-12 추가)

이 프로젝트 버전 pytest-httpx는 **등록된 응답을 재사용하지 않는다** — 응답 1개는 요청 1개에만 소비된다. 따라서 **요청 수 == 등록 응답 수** 필수:
- 응답이 부족하면 초과 요청이 실패.
- 응답이 남으면 teardown에서 "not requested" assert 실패 가능.
- fallback 체인 mock 카운트 = 1 (initial) + N (재시도). 7일 fallback 소진 테스트는 mock 8개 등록.

## 병렬 fallback 테스트 (2026-07-12 추가)

`asyncio.gather` 병렬 fallback (D-1..D-7 동시 조회) 테스트는 **요청 도착 순서가 비결정적** — 등록 순서로 응답을 매칭하면 flaky. 각 날짜가 자기 응답을 받도록 **searchdate별 URL regex**로 고정 등록해야 결정론적:

```python
for date_str, payload in responses_by_date.items():
    httpx_mock.add_response(url=re.compile(rf".*searchdate={date_str}.*"), json=payload)
```

**Why:** `url__regex`가 에러 없이 모든 호출에 매칭되어 fallback 로직 검증이 무력화됐고, 병렬화 이후에는 등록 순서 매칭이 비결정적 실패를 만들었다.

**How to apply:** pytest-httpx mock은 `url=re.compile(...)` 형태만 사용. 요청 수와 등록 응답 수를 정확히 일치. 병렬 요청 테스트는 요청을 구분하는 쿼리 파라미터(searchdate 등) 단위 regex로 응답을 고정.

**관련:** [[exchange-sanity-prev-business-day]]
