# fix-catalog.md

> 원칙 × 점수 구간별 개선 액션. `/sh:harness-gc --remediate`가 참조.

## P1. 리포지터리 = 기록 시스템

| 현재 점수 | 액션 |
|---|---|
| 0-2 | AGENTS.md + ARCHITECTURE.md 신규 작성 |
| 3-5 | docs/ 구조 확장, exec-plans/completed 이관 |
| 6-7 | ADR 패턴 도입 (`docs/design-docs/adr/`) |
| 8+ | learning log 자동화 |

## P2. 진입 문서 map

| 점수 | 액션 |
|---|---|
| 0-2 | AGENTS.md ~100줄 신규 |
| 3-5 | 거대 섹션을 docs/ 하위로 분리 |
| 6-7 | symlink 일관성 점검 + `.cursorrules` (해당 시) |
| 8+ | 인덱스 페이지 (PLANS.md) 자동 동기화 |

## P3. 아키텍처 기계적 강제

| 점수 | 액션 |
|---|---|
| 0-2 | layer-rules.md 작성 |
| 3-5 | grep 점검 스크립트 (verify_docs.py에 포함) |
| 6-7 | ruff `I` 활성화, import linter 도입 검토 |
| 8+ | 커스텀 lint rule (e.g. `flake8-import-order` 또는 자체) |

## P4. Search Before Building

| 점수 | 액션 |
|---|---|
| 0-2 | 공유 모듈 레지스트리 작성 (`harness-setup.md`) |
| 3-5 | Pre-Implementation 체크리스트에 grep 단계 추가 |
| 6-7 | 중복 코드 탐지 (`vulture`, `radon cc`) 정기 |
| 8+ | 신규 helper PR에서 grep evidence 요구 |

## P5. 작업 상태 종결

| 점수 | 액션 |
|---|---|
| 0-2 | AGENTS.md에 4 상태 명시 |
| 3-5 | PR template에 상태 필드 추가 |
| 6-7 | 세션 종료 시 자동 요청 |
| 8+ | CI에서 상태 메타데이터 파싱 |

## P6. TDD

| 점수 | 액션 |
|---|---|
| 0-2 | 첫 테스트 작성 |
| 3-5 | 도구별 unit 테스트 |
| 6-7 | E2E 체인 + 커버리지 측정 시작 |
| 8+ | 커버리지 게이트 80%+, flaky 0건 |

## P7. 회의적 검증

| 점수 | 액션 |
|---|---|
| 0-2 | 외부 reviewer 도입 |
| 3-5 | code-reviewer 정기 |
| 6-7 | setup-reviewer "증명될 때까지 미흡" 적용 |
| 8+ | adversarial verifier (회귀 의도 주입) |

## P8. 하네스 단순화

| 점수 | 액션 |
|---|---|
| 0-2 | tech-debt-tracker 신규 |
| 3-5 | 주기적 검토 (월 1회) |
| 6-7 | "이 가정 아직 유효한가?" 정기 질문 |
| 8+ | 자동 가정 재검증 스크립트 |

## P9. Phase 독립 에이전트

| 점수 | 액션 |
|---|---|
| 0-2 | 큰 작업 split |
| 3-5 | Phase별 핸드오프 문서 (`_workspace/`) |
| 6-7 | 5-Phase 패턴 정착 (harness-setup) |
| 8+ | 모든 multi-step 자동 구조화 |

## P10. Sprint Contract

| 점수 | 액션 |
|---|---|
| 0-2 | exec-plans/ 신설 |
| 3-5 | active/ 사전 작성 정착 |
| 6-7 | success criteria 명시 |
| 8+ | 평가자-수정자 명시 매칭 |

## P11. 채점 앵커

| 점수 | 액션 |
|---|---|
| 0-2 | principles.md에 점수 예시 작성 |
| 3-5 | gc-history.md 누적 시작 |
| 6-7 | 보정 회의 (분기 1회) |
| 8+ | 예시 자동 추출 (PR history → 앵커) |

## P12. 운영 인프라

| 점수 | 액션 |
|---|---|
| 0-2 | scripts/gc.sh 신설 |
| 3-5 | pre-commit + coverage 추가 |
| 6-7 | CI 통합 |
| 8+ | 자동 보고 + 트렌드 알림 |
