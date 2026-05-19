# QUALITY.md

> humax-excel-mcp 품질 기준 + 게이트.

## 도구

| 도구 | 명령 | 게이트 |
|---|---|---|
| ruff lint | `ruff check .` | 0 violations |
| ruff format | `ruff format --check .` | diff 없음 |
| pytest | `pytest -q` | 234/234 통과 |
| pytest --cov | `pytest --cov=src/humax_excel_mcp --cov-fail-under=80` | line ≥ 80% |
| vulture (dead code) | `vulture src/ --min-confidence 80` | 출력 없음 (false positive는 whitelist) |
| python -m build | `python -m build` | wheel + sdist 빌드 성공 |
| verify-docs | `python scripts/verify_docs.py` | 도구 수, 스키마 버전, 레이어 매핑 동기화 |

통합: `bash scripts/gc.sh`가 위 전부를 순차 실행 + 결과 `docs/harness/gc-history.md`에 append.

## ruff 룰

`pyproject.toml`:
- `select = ["E", "F", "I", "W", "UP"]` — 기본 + import 정렬 + pyupgrade
- `ignore = ["E501"]` — line-length 룰은 100자 기준이지만 long string 허용
- `line-length = 100`
- `target-version = "py310"`

## 테스트 분류 (234 total)

| 계층 | 디렉토리 | 개수 | 목적 |
|---|---|---|---|
| Unit | `tests/unit/` | ~220 | 함수/클래스 단위, fixture 기반 |
| Integration | `tests/integration/` | 3-5 | FastMCP 서버 기동 + tool invocation + JSONL audit |
| E2E | `tests/e2e/` | 2-3 | 도구 체인 (extract → verify → write → diff → alloc → restore) + 실 데이터 어댑터 |

## 커버리지 임계값 (목표)

- statements ≥ 80%
- branches ≥ 70%
- 안전 경로 (`core/backup`, `core/audit`, `tools/restore`) ≥ 95%

미달 시 PR 차단. `pyproject.toml [tool.coverage.run]`에 정의 (Phase 4 setup-reviewer 등록 예정).

## 함수 품질

- 함수 50줄 이내 (권장 20-30), 매개변수 4개 이하, 중첩 3단계
- early return 우선, 깊은 nested if 금지
- try-except 에러 삼키지 않기 — 로깅 또는 `HumaxMCPError` 재raise

## 매직 넘버

- 모든 상수는 `core/token_guard.py`, `core/excel_io._AUTO_DETECT_*`, `schemas/bp26.SCHEMA_VERSION` 등 모듈 상단 명명
- 매직 0.01 (tolerance), 100 (rate sum), 10_000_000 (diff threshold) 등은 module-level constant로 추출
