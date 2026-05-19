# layer-rules.md

> 레이어 종속성 규칙. ARCHITECTURE.md의 detail.

## 레이어 (다시)

| Layer | Dir | Imports from |
|---|---|---|
| L1 Server | `src/humax_excel_mcp/server.py` | L2 |
| L2 Tools | `src/humax_excel_mcp/tools/` | L3, L4, L5 |
| L3 Core | `src/humax_excel_mcp/core/` | L4, L5 |
| L4 Config | `src/humax_excel_mcp/config.py` | L5 |
| L5 Schemas | `src/humax_excel_mcp/schemas/` | (없음) |

## 허용 방향

```
L1 Server ──> L2 Tools ──> L3 Core ──> L4 Config ──> L5 Schemas
                  │            │             │             ▲
                  │            └─────────────┴─────────────┤
                  └──────────────────────────────────────────┘
```

`L1 → L2` 단독. `L2 → L3/L4/L5` 가능. `L3 → L4/L5`. `L4 → L5`. `L5`는 외부 라이브러리 외 import 없음.

## 금지

- L5 (`schemas/`) → 다른 어떤 humax_excel_mcp 모듈 import 금지
- L4 (`config.py`) → L1/L2/L3 import 금지
- L3 (`core/`) → L1/L2 import 금지
- L2 (`tools/*.py`) → 다른 L2 tool import 금지 (공통 로직은 L3로 추출)
- 순환 참조 절대 금지 (ruff `I` + 수동 grep)

### Sanctioned 예외 (L2 orchestrator)

`tools/report.py`는 PRD §4.10 / US-017에 의해 명시적 orchestrator로 정의된다. `apply_golden_template` + `verify_sums`를 조합하는 워크플로 도구이며 다른 L2 도구를 직접 import한다. `scripts/verify_docs.py`의 `L2_ORCHESTRATOR_ALLOWLIST`에 등록되어 게이트를 통과한다.

> 신규 orchestrator 추가 시: PRD에 명시 + `verify_docs.py` allowlist에 추가 + 이 섹션에 항목 추가. 추출 가능하면 `core/`로 옮기는 것을 우선 검토.

## 위반 사례 예시

❌ `from ..tools.write import write_cells` in `core/backup.py` (L3 → L2 역방향)
❌ `from .extract import extract_filtered` in `tools/verify.py` (L2 ↔ L2 횡방향)
❌ `from ..config import get` in `schemas/bp26.py` (L5 → L4 역방향)

✅ `from .errors import HumaxMCPError` in `core/backup.py` (L3 → L3 같은 레이어)
✅ `from ..core.audit import audited` in `tools/__init__.py` (L2 → L3 정방향)
✅ `from ..schemas import bp26` in `core/excel_io.py` (L3 → L5 정방향)

## 점검 방법

```bash
# L2 → L2 위반 점검
grep -rE "^from \.[a-z_]+ import" src/humax_excel_mcp/tools/ | grep -v "^from \.__init__"

# L3 → L2 역방향 점검
grep -rE "from \.\.tools" src/humax_excel_mcp/core/

# L5 외부 의존 점검
grep -rE "^from \.\." src/humax_excel_mcp/schemas/
# 출력 없어야 함

# 자동화: scripts/verify_docs.py에 포함 (Phase 3에서 lint-rule-designer가 등록)
```

## 공통 로직 추출 가이드

L2 도구 두 개 이상에서 동일 패턴이 보이면:
1. `core/`에 helper 추출
2. 두 도구 모두 helper 호출
3. 추출 시 테스트도 함께 이동

기존 예시:
- 백업 로직 → `core/backup.create_backup` (write, allocation_set, template_engine, restore에서 공유)
- 감사 로깅 → `core/audit.audited` 데코레이터 (전 도구 등록 시점에서 적용)
- 토큰 가드 → `core/token_guard` (전 도구 응답 직렬화 전 통과)

## 신규 도구 추가 시

1. `src/humax_excel_mcp/tools/<new_tool>.py` 신규
2. `tools/__init__.py`의 `TOOL_NAMES` + `register_all`에 등록
3. `@audited("<tool_name>")` 자동 적용 (register_all에서)
4. write 도구면 `core/backup.create_backup` 호출
5. `tests/unit/test_<new_tool>.py` 추가 (TDD 우선)
6. `docs/prd/mcp-design-plan.md`에 spec 추가
7. `AGENTS.md` 도구 표 업데이트
