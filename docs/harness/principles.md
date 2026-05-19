# principles.md

> 하네스 엔지니어링 12원칙. 자가 발전(`/sh:harness-gc`)에서 채점 기준으로 사용.

## P1. 리포지터리 = 기록 시스템

코드/문서/설정이 의사결정 기록. 사라지면 안 됨.

- L0 (0-2): 코드만 존재, 결정 근거 없음
- L3 (3-5): README 일부, 단편 학습 메모
- L6 (6-7): AGENTS.md + docs/ 구조 + exec-plans/completed
- L9 (8-10): 모든 결정에 추적 가능한 근거 (PRD, ADR, learning log)

## P2. 진입 문서는 map, not handbook

AGENTS.md ~100줄, 상세는 링크.

- L0: 단일 거대 README
- L3: AGENTS.md 있지만 200+줄
- L6: ~100줄 + docs/ 링크 80%
- L9: ~100줄 + 모든 상세 외부화 + symlink 일관

## P3. 아키텍처 기계적 강제

레이어 룰을 코드(lint/import 룰)가 강제. 문서 룰만으론 부족.

- L0: 룰 문서 없음
- L3: layer-rules.md 있지만 lint 미연결
- L6: ruff `I` + grep 점검 스크립트
- L9: import linter 또는 ruff 커스텀 룰로 자동 차단

## P4. Search Before Building

신규 모듈 작성 전 grep 의무. 중복 helper 차단.

- L0: 동일 패턴 3+ 곳 복제
- L3: 동일 패턴 2 곳 복제, 인지함
- L6: 공유 helper 추출 패턴 정착 (`core/backup`, `core/audit`)
- L9: 공유 모듈 레지스트리 명시 + Pre-Implementation 체크리스트에 포함

## P5. 작업은 상태로 끝난다

`DONE` | `DONE_WITH_CONCERNS` | `BLOCKED` | `NEEDS_CONTEXT`.

- L0: 작업 종료 시 상태 없음
- L3: 종종 명시
- L6: AGENTS.md에 프로토콜 명문화
- L9: 모든 PR/세션 종료 시 자동 명시

## P6. TDD 우선

실패 테스트 → 통과 → 리팩터.

- L0: 테스트 없음
- L3: 일부 도구만 테스트
- L6: 234 테스트 (현재) + Red→Green→Refactor 정착
- L9: 커버리지 게이트 + flaky 0건 + E2E 체인

## P7. 회의적 검증

자기 평가 편향 차단.

- L0: 자체 평가만
- L3: 가끔 외부 reviewer
- L6: setup-reviewer / code-reviewer 분리, "증명될 때까지 미흡"
- L9: GAN-style adversarial verifier 정기

## P8. 하네스 단순화

하네스 컴포넌트는 모델 능력 가정. 정기 재검증.

- L0: 가정 점검 없음
- L3: 임시방편 누적
- L6: tech-debt-tracker에 가정 명시
- L9: 정기 GC로 불필요 가정 제거

## P9. Phase 독립 에이전트

context reset > compaction.

- L0: 모든 작업 단일 컨텍스트
- L3: 큰 작업 split
- L6: harness-setup의 5 Phase 독립 실행
- L9: 모든 multi-step 작업 구조화 핸드오프

## P10. Sprint Contract

수정 전 평가자-수정자 기대 효과 합의.

- L0: 합의 없음
- L3: 가끔 PR description
- L6: exec-plans/active/<slug>.md 사전 작성
- L9: 모든 변경에 success criteria 사전 명시

## P11. 채점 앵커

점수대별 구체적 예시.

- L0: 룰만 있고 예시 없음
- L3: 일부 예시
- L6: 본 문서 (모든 P에 L0/3/6/9 예시)
- L9: 정기 보정 + 예시 업데이트

## P12. 운영 인프라

자동화 (gc, pre-commit, audit, coverage).

- L0: 수동
- L3: 일부 (현재: ruff + pytest 수동)
- L6: gc.sh + pre-commit + coverage 게이트 + audit
- L9: CI 통합 + 정기 보고
