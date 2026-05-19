---
name: mcp-tools-overview
description: humax-mcp 도구 7개 핵심 spec 요약 + Live Artifact 출력 + 안전 정책 P1-P5
type: project
created: 2026-05-19
---

`humax-mcp` 도구 7개 + 공통 옵션 + 안전 정책. 상세는 `docs/prd/mcp-design-plan.md` (1875 lines).

## 도구 7개

| # | 도구 | read/write | 핵심 |
|---|---|---|---|
| 1 | `extract_filtered` | R | Excel raw → 시트/월/회사/컬럼 필터링 추출 |
| 2 | `verify_sums` | R | 조직 5계층 합계 결정론 검증 (`tolerance: float = 0.01`) |
| 3 | `write_cells` | W | openpyxl 셀 단위 + 백업 강제 + output_path 검증 + dry_run |
| 4 | `generate_diff_candidates` | R | \|10백만\| 이상 Diff 후보 추출 |
| 5 | `get_allocation_rates` | R | 26BP raw C30-C34 배부율 조회 + 합 100% 검증 |
| 6 | `update_allocation_rates` | W | write_cells 안전 정책 상속 + `rate_tolerance: float = 0.01` |
| 7 | `get_exchange_rates` | R | 한국수출입은행 API (`oapi.koreaexim.go.kr/.../exchangeJSON`) + 휴일 fallback 7일 + JPY/IDR(100) 정규화 + 12h 캐시 |

## 공통 옵션

- `render_format: Literal["excel", "live_artifact", "both"] = "excel"` 모든 도구
- 응답 스키마에 `artifact_hints` 자동 생성 (Claude Desktop이 시각화 렌더링)
- 미명시 시 Claude가 자연어로 사용자 확인

## 안전 정책 P1-P5

1. **P1 원본 보존 우선** — read-only 기본, write는 명시적. `write_cells` / `update_allocation_rates` 4중 안전 (백업 강제 + output_path 검증 + dry_run + RATE_SUM_NOT_100)
2. **P2 결정론은 Python에 위임** — LLM 산술 금지
3. **P3 토큰 효율** — 필터된 응답, 페이지네이션
4. **P4 안전** — 백업 + dry-run + 감사 로그 (.humax-mcp/audit.log)
5. **P5 자연어 호출** — 실무자 CLI 학습 부담 0

## Pre-mortem 7 시나리오

- S1: write_cells 원본 깨짐 (백업 실패)
- S2: 토큰 응답 200K 초과
- S3: 적요/PII 외부 전송 거버넌스 위반
- S4: Anthropic API 신뢰 경계 (입력 데이터 외부 경유)
- S5: Live Artifact 캡처/공유로 PII 유출
- S6: 배부율 합 100% 위반 → 결산 오류
- S7: 환율 API 장애 / 잘못된 환율 적용

## 외부 API

| API | 용도 | PII | 거버넌스 |
|---|---|---|---|
| Anthropic API (Claude Desktop 내장) | LLM 호출 | 잠재 위험 | DPA/ZDR 확인 필수 |
| oapi.koreaexim.go.kr | 환율 조회 | 무관 (공공 데이터) | 사내 방화벽 허용 필요 |

## 배포 모델

- **v0.1 현재**: GitHub Private Repo (hjsh200219/humax-mcp) + stdio + `git pull` + `install.ps1` / `update.ps1`
- v0.2: 사내 PC 1대 서버화 (HTTP/SSE)
- v0.3: SAP API 직접 연동
- v0.4: 전사 확대 + 사내 MCP 마켓플레이스

## 4 minor (구현 시 적용 완료, plan v3에 반영됨)

- M2: test_write.py에 OVERWRITE_ORIGINAL_FORBIDDEN / FILE_LOCKED / SCHEMA_MISMATCH 테스트 추가됨
- M3: update_allocation_rates에 `rate_tolerance` 파라미터 추가됨
- M5: Section 4.8 step 11 — verify_sums chained 권고 추가됨
- M6: Section 4.8 step 6.5 — comma string-to-float 변환 (PARSE_ERROR) 추가됨
- M7: Section 9.5.10 — `oapi.koreaexim.go.kr` 방화벽 행 추가됨

**Why:** 4 이터레이션 ralplan consensus 완료. Architect APPROVE_WITH_MINOR_NOTES + Critic APPROVE. 모든 minor 구현 시 plan에 반영함.

**How to apply:** 도구 구현 시 plan v3 (Revision 3) 기준 spec 사용. write/update 도구는 반드시 4중 안전 정책 일관. 외부 API는 .env로 키 관리, .gitignore 강제.
