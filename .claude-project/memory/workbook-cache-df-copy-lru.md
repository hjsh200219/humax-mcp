---
name: workbook-cache-df-copy-lru
description: workbook_cache는 (path, mtime_ns, size, …) 키 LRU 16 + 반환은 항상 df.copy() — 도구가 df를 mutate하므로
type: project
created: 2026-07-12
---

`src/humax_excel_mcp/core/workbook_cache.py` — Excel 재파싱 비용 제거용 DataFrame 캐시.

- **캐시 키:** `(resolved path, mtime_ns, size, sheet, schema, header_row, normalize)`. mtime_ns+size 포함으로 외부에서 파일이 바뀌면 키 자체가 달라져 자동 무효화.
- **용량:** LRU, `_MAX_ENTRIES = 16`.
- **반환은 항상 `df.copy()`** — 도구들이 반환 df를 mutate(컬럼 추가, 필터, 형변환)하므로 캐시 원본을 공유하면 다음 호출이 오염된 df를 받는다.
- **write/restore 도구는 저장 후 `invalidate(path)` 명시 호출** — mtime 키 무효화가 있어도 resolved-path 단위 즉시 무효화로 이중 안전.
- 적용 도구: extract / verify / allocation_get (read 경로 read_only=True). diff는 시트 fallback 특수성으로 미적용.

**Why:** DataFrame 캐시의 최대 함정은 mutation 공유로 인한 silent corruption. copy 비용은 15k+ rows 재파싱 비용보다 훨씬 싸다. "빠르지만 가끔 틀리는 캐시"는 이 프로젝트(결산 결정론)에서 존재 가치가 없다.

**How to apply:**
- 캐시에서 mutable 객체(df, dict, list)를 반환할 때는 항상 방어적 copy.
- 파일 기반 캐시 키에는 반드시 `mtime_ns + size` 포함.
- 파일을 쓰는 경로(write/restore)는 키 무효화에 기대지 말고 명시적 invalidate 병행.
- perf 회귀 감시는 `tests/benchmarks/` (pytest `-m benchmark`) — gc.sh에서 advisory 비차단 단계.

**관련:** [[excel-io-readonly-source-large-file]]
