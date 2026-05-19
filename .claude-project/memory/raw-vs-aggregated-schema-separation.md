---
name: raw-vs-aggregated-schema-separation
description: bp26 (aggregated) vs raw_bp26 (transaction-level) 별도 schema 파일 — additive, no breaking
type: reference
created: 2026-05-19
---

v0.1 `schemas/bp26.py` (60+ tests 검증) 은 pre-aggregated 모델 (m01_actual..m12_actual, cum01..cum12, annual_*). 실제 26BP 는 transaction-level (Year/Month/Posting Date/Amount(KRW) per row). 두 모델 mixing 시 spec 충돌.

해결: `schemas/raw_bp26.py` 신규 파일 — bp26 미수정. 같은 module dir, 다른 SCHEMA_VERSION ("2026.05-raw"), 다른 COLUMN_MAP (transaction cols + 13 배부율).

`excel_io.worksheet_to_dataframe(ws, *, schema_module: str = "bp26")` 가 둘 중 선택. `_SCHEMA_MODULES = {"bp26": bp26, "raw_bp26": raw_bp26}` dispatch.

**Why:** bp26 변경 = 177 v0.1.1 tests 회귀 위험. 별도 파일 = 0 regression. 두 schema 사이 변환은 aggregator 가 담당 (raw → aggregated).

**How to apply:**
- 기존 schema 가 일부 데이터 모델 안 맞는다면, schema 수정 X, **별도 schema 파일 추가** + 변환 layer
- aggregator/adapter 가 schema A → schema B 변환 책임
- 호출자는 명시적 schema_module 지정 (or auto-detect)
- bp26.py FROZEN 표시 (코드 comment 또는 ADR 에서) → 향후 개발자가 수정 안 하도록

**구조:**
- `schemas/bp26.py` — v0.1 aggregated (frozen)
- `schemas/raw_bp26.py` — v0.1.2 transaction (real 26BP)
- `core/aggregator.py` — raw → aggregated 변환

**관련:** [[aggregator-evcs-per-call-flag]], [[header-row-auto-detect-pattern]]
