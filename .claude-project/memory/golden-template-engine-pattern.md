---
name: golden-template-engine-pattern
description: 결정론 골든 템플릿 엔진 — 디자인 드리프트 차단 패턴 (apply_golden_template + binding spec + fixture build)
type: reference
created: 2026-05-19
---

PRD 에러 #3 (디자인 드리프트, "10번 재명령") 구조적 해결 패턴.

핵심 분해:
1. **Reference 산출물 (실데이터, LOCAL ONLY)** — `docs/references/*.xlsx`, gitignored
2. **Fixture template (데이터 클리어드, 커밋)** — `fixtures/templates/{type}.xlsx` + `{type}.template.json` sidecar
3. **Binding spec (pydantic v2 모델)** — `core/template_bindings.py`의 TemplateBinding/SheetBinding/RowSelection
4. **Loader + 검증** — `core/template_loader.py`가 sidecar `schema_version`/`sheet_names` 일치 확인
5. **Engine** — `apply_golden_template` 가 source df를 RowSelection로 필터/정렬 후 SheetBinding.column_map (template_col_letter → source_col_key) 으로 셀 채움. MergedCell 스킵, formula cell 보존
6. **Build script** — `scripts/build_fixture_templates.py` 가 reference를 로드해 비-수식 값만 None 처리 후 fixture 저장 + post-build per-sheet formula count assertion

핵심 규칙:
- Cell-clearing: `if isinstance(v, str) and v.startswith("="): pass; else: cell.value = None`. MergedCell 분기.
- column_map 방향: `{"B": "gl_account", "C": "gl_account_name", ...}` (template letter → source key). Iterate template cells.
- Sidecar `formula_count_per_sheet` 는 sheet마다 비균일 (월별 ~676, 누계 ~1224, Diff ~252). 균일 assertion 금지.
- 산출물 `.gitignore` 정책: `!fixtures/templates/*.xlsx` 예외만. `docs/references/*.xlsx`는 절대 커밋 금지.

**Why:** LLM이 매번 산출물 통째 재생성하던 패턴 → 데이터만 결정론적으로 채우는 구조로 전환. 강의 모듈 2 "골든 템플릿 패턴" 자동화.

**How to apply:** 새 산출물 유형 추가 시 (1) reference 1건 docs/references/ 적재, (2) `core/template_bindings.py`에 SheetBinding 추가, (3) `SOURCES` dict + build script 재실행, (4) sidecar 자동 생성, (5) test_fixture_templates.py 파라미터 추가.
