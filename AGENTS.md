# AGENTS.md — humax-excel-mcp

> 에이전트 진입 맵. 상세 규칙은 docs/ 하위 문서 링크 참조. ~100줄 유지.

## 응답 스타일

Be concise. No filler. Straight to the point. Use fewer words.

## 프로젝트 한 줄

Humax 고정비 결산 워크플로우의 5개 에러 + 적요/환율/배부율 한계를 Python 결정론 + MCP로 근본 해결하는 stdio MCP 서버.

## 기술 스택

Python 3.10+ · FastMCP (`mcp>=1.0`) · openpyxl 3.1+ · pandas 2.0+ · pydantic 2.0+ · python-dotenv · httpx · pytest+asyncio · ruff

## Health Stack

```bash
ruff check . && ruff format --check .   # lint + format
pytest -q                                # 286 tests (unit + integration + e2e + benchmark)
python -m build                          # wheel + sdist (배포 검증)
bash scripts/gc.sh                       # 통합 게이트 (lint+test+build+verify-docs+bench advisory)
python scripts/verify_docs.py            # 문서-코드 동기화 검증
```

## 도구 11개 (MCP)

| # | 도구 | 위치 | 기능 |
|---|---|---|---|
| 1 | `extract_filtered` | tools/extract.py | Excel raw 필터링 (시트/월/회사/컬럼) |
| 2 | `verify_sums` | tools/verify.py | 5계층 합계 결정론 검증 |
| 3 | `write_cells` | tools/write.py | 셀 단위 편집 + 자동 백업 + dry-run |
| 4 | `generate_diff_candidates` | tools/diff.py | \|10백만\| 이상 Diff 후보 |
| 5 | `get_allocation_rates` | tools/allocation_get.py | 배부율 조회 + 합 100% 검증 |
| 6 | `update_allocation_rates` | tools/allocation_set.py | 배부율 변경 (안전 정책 + tolerance) |
| 7 | `get_exchange_rates` | tools/exchange.py | 한국수출입은행 환율 + 휴일 fallback + JPY 정규화 |
| 8 | `apply_golden_template` | tools/template_engine.py | 디자인 드리프트 차단 골든 템플릿 |
| 9 | `generate_report` | tools/report.py | 결과 리포트 생성 |
| 10 | `restore_backup` | tools/restore.py | 백업 복구 |
| 11 | `update_fc_month_report` | tools/fc_month_update.py | FC 월 결산 리포트 갱신 (AC/누계 시트) |

전 도구: `@audited()` 데코레이터, `render_format`, `artifact_hints` 공통.

## 레이어 (L1=Runtime ← L5=Schemas)

| Layer | Dir | Imports from |
|---|---|---|
| L1 Server | `server.py` | L2 only |
| L2 Tools | `tools/` | L3, L4, L5 (서로 X) |
| L3 Core | `core/` | L4, L5 |
| L4 Config | `config.py` | L5 |
| L5 Schemas | `schemas/` | (없음) |

> 상세: [ARCHITECTURE.md](./ARCHITECTURE.md)

## 안전 정책 (P1-P5)

1. **원본 보존** — read-only 기본, write는 명시적 + 백업 강제
2. **결정론은 Python** — LLM 산술 금지
3. **토큰 효율** — 필터링 응답, 페이지네이션
4. **안전** — 백업 + dry-run + 감사 로그 + sha256 검증
5. **자연어 호출** — 실무자 CLI 학습 부담 0

> 상세: [docs/PRODUCT_SENSE.md](./docs/PRODUCT_SENSE.md) · [docs/SECURITY.md](./docs/SECURITY.md) · [docs/RELIABILITY.md](./docs/RELIABILITY.md)

## Critical Constraints

- 사내 데이터 (Excel raw / 배부율 / CC 마스터) git push 금지 — `.gitignore` + 정규식 스캔 2중 차단
- API 키 (`EXCHANGE_RATE_API_KEY`, `ANTHROPIC_API_KEY`) `.env` 보관, 절대 커밋 금지
- write 도구는 `output_path != file_path` 강제 (원본 덮어쓰기 금지)
- 백업 sha256 불일치 시 즉시 `BACKUP_FAILED` raise
- 모든 도구 `@audited()` 적용 — JSONL 일일 로그 (`.humax-mcp/audit/`)
- PII 컬럼 (`raw_bp26.PII_COLUMNS`) aggregator 진입 전 제거

## Pre-Implementation Checklist

> 상세 SSOT: [docs/harness/harness-setup.md](./docs/harness/harness-setup.md)

핵심 5:
1. **TDD 우선** — 실패 테스트 작성 → Green → Refactor
2. **레이어 방향 준수** — L5 → L4 → L3 → L2 → L1 단방향, 위반 시 `docs/design-docs/layer-rules.md` 참조
3. **Search Before Building** — 신규 helper 작성 전 `core/` `schemas/` 기존 모듈 grep
4. **함수 50줄 이내**, 매개변수 4개 이하, early return
5. **에러 코드 우선** — 새 에러는 `core/errors.py`에 `_make(CODE)` 등록 후 사용

## LLM 코딩 행동 원칙

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

Tradeoff: These guidelines bias toward caution over speed. For trivial tasks, use judgment.

Layer note: These four principles are the behavioral/judgment layer. They complement — not duplicate — the tool-enforced invariants (P3 lint, P6 layer-rules, P7 knip dead-code). Tools catch mechanical violations after code exists; these guide the decisions tools cannot check (surfacing assumptions, avoiding over-building, not touching adjacent code, defining verifiable goals). All four are judgment, not lint targets.

1. Think Before Coding — Don't assume. Don't hide confusion. Surface tradeoffs. State assumptions explicitly; if multiple interpretations exist, present them; if simpler approach exists, say so; if unclear, stop and ask.
2. Simplicity First — Minimum code that solves the problem. No speculative features, no single-use abstractions, no unrequested configurability, no error handling for impossible scenarios. If 200 lines could be 50, rewrite it.
3. Surgical Changes — Touch only what you must. Don't improve adjacent code. Match existing style. Mention unrelated dead code but don't delete it. Remove only imports/vars/functions YOUR changes made unused.
4. Goal-Driven Execution — Transform tasks into verifiable goals (write failing test first, then make it pass). For multi-step tasks, state a plan with verify steps. Loop independently until criteria met.

## Status Protocol

작업 보고는 다음 중 하나로 종결: `DONE` | `DONE_WITH_CONCERNS` | `BLOCKED` | `NEEDS_CONTEXT`.

## 문서 인덱스

- [README.md](./README.md) — 사용자 퀵스타트
- [ARCHITECTURE.md](./ARCHITECTURE.md) — 레이어 + 의존 + 교차 관심사
- [docs/prd/mcp-design-plan.md](./docs/prd/mcp-design-plan.md) — 도구 spec SSOT (Rev 4)
- [docs/prd/accuracy-speed-improvement.md](./docs/prd/accuracy-speed-improvement.md) — 정확도·속도 개선 (Rev 2, 구현 완료)
- [docs/prd/data-flow.md](./docs/prd/data-flow.md) — Excel 데이터 처리 흐름 (비개발자용, Python vs LLM 비교)
- [docs/QUALITY.md](./docs/QUALITY.md) · [docs/RELIABILITY.md](./docs/RELIABILITY.md) · [docs/SECURITY.md](./docs/SECURITY.md) · [docs/PRODUCT_SENSE.md](./docs/PRODUCT_SENSE.md) · [docs/PLANS.md](./docs/PLANS.md)
- [docs/design-docs/core-beliefs.md](./docs/design-docs/core-beliefs.md) · [docs/design-docs/layer-rules.md](./docs/design-docs/layer-rules.md)
- [docs/exec-plans/tech-debt-tracker.md](./docs/exec-plans/tech-debt-tracker.md)
- [docs/harness/](./docs/harness/) — principles / maturity-framework / fix-catalog / harness-setup / gc-history
