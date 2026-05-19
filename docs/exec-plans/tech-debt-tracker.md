# tech-debt-tracker.md

> 알려진 기술 부채. 우선순위 / 영향 / 조치 후보.

## 분류

| 우선 | 의미 |
|---|---|
| P0 | 안전 / 보안 / 데이터 무결성 위협 — 즉시 |
| P1 | 명백한 회귀 위험 / 운영 마찰 — 다음 sprint |
| P2 | 품질 / 가독성 / 성능 — 시간 날 때 |
| P3 | nice-to-have |

## 현황 (2026-05-19)

| ID | 우선 | 영역 | 항목 | 영향 | 조치 후보 |
|---|---|---|---|---|---|
| ~~TD-001~~ | ~~P1~~ | ~~Quality~~ | ~~커버리지 게이트 없음~~ | ✅ 해소 (2026-05-19): pyproject `[tool.coverage]` fail_under=70 + `pytest-cov>=5.0` 추가. 실측 88.70% |
| ~~TD-002~~ | ~~P1~~ | ~~Quality~~ | ~~dead code 탐지 없음~~ | ✅ 해소 (2026-05-19): `vulture>=2.10` 추가 + `[tool.vulture]` 설정 (pydantic validator decorator 제외) + `gc.sh`에 vulture 단계 |
| ~~TD-003~~ | ~~P1~~ | ~~Reliability~~ | ~~pre-commit 훅 없음~~ | ✅ 해소 (2026-05-19): `pre-commit>=3.7` dev extras 추가 + `pre-commit install` 실행 완료 |
| TD-004 | P2 | Security | `pip-audit` / `safety` 미사용 | 의존성 취약점 미인지 | 정기 실행 + `gc.sh` 옵션 |
| TD-005 | P2 | Architecture | `tools/template_*.py` 3개 모듈 (template_engine, report, restore) 공통 helper 추출 여지 | 중복 가능성 | 공통 패턴 점검 후 `core/template_common.py` |
| TD-006 | P2 | Performance | openpyxl `read_only=True` 활용 미점검 | 대용량 raw xlsx 메모리 | 벤치마크 후 read 도구 전환 |
| TD-007 | P2 | Performance | token_guard 사후 절단 방식 | 사전 row count 페이지네이션 부재 | extract에 `page` / `page_size` 파라미터 |
| TD-008 | P2 | Docs | progress.txt 비구조 | 학습 메모 검색 어려움 | `docs/exec-plans/completed/`로 이관 후 삭제 |
| TD-009 | P3 | Quality | mypy / pyright 미사용 | 타입 회귀 미탐지 | `pyright` 또는 `mypy --strict` 도입 |
| TD-010 | P3 | Architecture | `core/aggregator.py` 388줄 | 단일 모듈 거대화 | 분할 (e.g. `aggregator/{base, evcs, virtual_rows}.py`) |
| TD-011 | P3 | DX | `scripts/install.ps1` / `update.ps1`만 존재 | Mac/Linux 진입 마찰 | `scripts/install.sh` 추가 |
| TD-012 | P2 | Architecture | 도구 entry point 15 함수 50줄 초과 (4개 100줄+: extract_filtered=154, apply_golden_template=154, verify_sums=145, update_allocation_rates=123) | 가독성 / 테스트 분할 / 유지보수 마찰 | 비즈니스 로직 단계별 helper 추출 (입력 검증 / load / core 로직 / response 빌드). 분기 복잡도 높은 도구 우선 |
| TD-013 | P3 | Docs | progress.txt 원본이 root에 잔존 (이관 사본 `docs/exec-plans/completed/v0.1.0-tdd-session.md` 존재) | dual source | 사용자 확인 후 progress.txt 삭제 |

## 처리 워크플로

1. 해결 시 ID 표에서 제거 + `docs/exec-plans/completed/<slug>.md`에 사후 정리
2. 신규 발견 시 다음 ID로 추가
3. 우선순위 재평가: 매 minor 버전 (v0.x.0)마다 review
