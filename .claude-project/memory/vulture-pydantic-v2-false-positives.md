---
name: vulture-pydantic-v2-false-positives
description: vulture가 pydantic v2 @field_validator 데코레이터의 cls 인자를 미사용 변수로 잘못 탐지함. ignore_names에 cls, model_config 추가 필수.
type: feedback
created: 2026-05-19
---

vulture (Python dead-code detector)는 pydantic v2 패턴 일부를 false positive로 잡는다:

1. `@field_validator` + `@classmethod` 조합의 `cls` 인자 → "unused variable" (100% confidence)
2. `model_config = ConfigDict(...)` 클래스 속성 → "unused attribute"

`pyproject.toml [tool.vulture]`의 `ignore_decorators`만으로는 cls 변수가 필터되지 않는다. **반드시 `ignore_names`에 직접 추가**해야 함:

```toml
[tool.vulture]
paths = ["src/humax_excel_mcp"]
min_confidence = 80
ignore_names = [
    "register_all", "main", "build_server",
    "cls",           # @field_validator + @classmethod 필수
    "model_config",  # pydantic v2 ConfigDict 패턴
]
ignore_decorators = [
    "@audited", "@mcp.tool", "@pytest.fixture",
    "@field_validator", "@model_validator", "@classmethod",
]
```

**또한**: `vulture <path>` 처럼 positional path 인자를 주면 pyproject 설정이 **무시**된다. `gc.sh`에서는 path 인자 없이 `vulture --min-confidence 80`로 호출해야 pyproject `paths`와 `ignore_*`가 적용된다.

**Why**: TD-002 해소 작업 중 첫 vulture run에서 schemas/requests.py의 5개 validator가 false positive 발생. decorator 필터만 추가하니 안 잡히던 문제. 결국 ignore_names + path 인자 제거 두 가지 fix 필요.

**How to apply**: 새 pydantic v2 validator 추가해도 vulture 깨지지 않음. vulture 결과가 0이 아니면 먼저 ignore_names / decorators 누락 점검 후 진짜 dead code인지 판정.
