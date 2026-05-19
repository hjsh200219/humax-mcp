# maturity-framework.md

> L1-L5 성숙도 등급 + 4차원 가중평균.

## 등급

| Level | 의미 | 12원칙 평균 |
|---|---|---|
| L1 Reactive | 임시방편 누적 | 0-2 |
| L2 Documented | 룰 문서화 시작 | 3-4 |
| L3 Enforced | 룰을 도구가 강제 | 5-6 |
| L4 Self-improving | 정기 GC + 메트릭 | 7-8 |
| L5 Adaptive | 자동 보정 + 채점 앵커 진화 | 9-10 |

## 4차원 가중평균

| 차원 | 가중치 | 포함 원칙 |
|---|---|---|
| **Knowledge** (지식 시스템) | 0.25 | P1, P2, P5, P10 |
| **Architecture** (구조 강제) | 0.25 | P3, P4, P9 |
| **Quality** (품질 게이트) | 0.30 | P6, P7, P12 |
| **Adaptability** (자가 발전) | 0.20 | P8, P11 |

종합 점수 = 0.25·Knowledge + 0.25·Architecture + 0.30·Quality + 0.20·Adaptability

## 현재 추정 (2026-05-19 setup 직후)

| 차원 | 원칙별 점수 | 평균 |
|---|---|---|
| Knowledge | P1=6, P2=7, P5=6, P10=4 | 5.75 |
| Architecture | P3=5, P4=7, P9=6 | 6.0 |
| Quality | P6=7, P7=5, P12=4 | 5.3 |
| Adaptability | P8=4, P11=6 | 5.0 |

**종합 ≈ 5.55 → L3 Enforced 진입**

## 다음 목표 (L4)

- P12 운영 인프라: coverage 게이트 + pre-commit + vulture 추가 → 6+
- P7 회의적 검증: setup-reviewer / code-reviewer 정기 실행 → 7+
- P10 Sprint Contract: exec-plans/active/ 사전 작성 정착 → 6+
- P11 채점 앵커: gc-history.md 누적 → 7+

목표 종합 7.0+ → L4 Self-improving.
