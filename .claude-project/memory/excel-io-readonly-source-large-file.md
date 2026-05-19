---
name: excel-io-readonly-source-large-file
description: 큰 xlsx (15k+ rows) 를 source 로 읽을 때 openpyxl read_only=True 필수 — 30s+ → 0.2s
type: reference
created: 2026-05-19
---

openpyxl `load_workbook(path, data_only=True)` 기본은 **모든 cell formula 평가 + 전체 메모리 로드** 시도. 15k+ rows / 60+ cols 파일에서 100% CPU, 3GB+ RAM, 30s+ 소요. pytest 가 11 tests × aggregator 호출 시 5분 hang.

해결: source workbook 은 input-only 이므로 `read_only=True` 사용:
```python
src_wb = excel_io.load_workbook_safe(src, data_only=True, read_only=True)
```

**Why:** read_only=True 는 streaming read — formula 평가 skip, cell mutation 불가, 메모리 일정.

**How to apply:**
- Source workbook (input, read-only consumption) → 반드시 `read_only=True`
- Template workbook (cell write 필요) → `read_only=False` 기본
- `tools/template_engine.py:115` 패턴 참조
- `tests/e2e/test_real_data.py:51-66` 의 4 callsite 모두 `read_only=True` 사용 사례

**한계:**
- read_only ws 는 `ws.cell(r,c).value = X` 쓰기 불가
- merged_cells.ranges 접근 안 됨 (mutate path 가 아니라면 OK)
- iter_rows(values_only=True) 만 사용 권장

**관련:** [[mcp-tool-perf-15k-rows-baseline]]
