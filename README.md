# humax-mcp

Humax 고정비 결산 자동화 MCP 서버. Claude Desktop에서 자연어로 호출.

## 무엇

file #1 (`클로드 코워크 활용안_고정비.xlsx`) 워크플로우의 5개 에러 + 적요/환율/배부율 한계를 Python 결정론 + MCP로 근본 해결.

| 에러 | 원인 | 해결 도구 |
|---|---|---|
| 원본 파일 훼손 | LLM 통째 재생성 | `write_cells` (openpyxl 셀 단위 + 백업) |
| 디자인 변경 / 지시 누락 | 프롬프트 모호 | 골든 템플릿 패턴 (강의 모듈 2) |
| 10회+ 재명령 | 결정론 부재 | Python 코드 위임 |
| 토큰 소진 | raw 945K 셀 통째 전송 | `extract_filtered` (사전 필터링) |
| 숫자 검토 부담 | LLM 산술 비결정적 | `verify_sums` (5계층 합계 결정론) |
| 적요 인식 (한계) | 토큰 폭발로 컬럼 잘림 | `extract_filtered` columns 우선순위 |
| 환율 수기 입력 | Step 3 외부 데이터 | `get_exchange_rates` (한국수출입은행 API) |
| 배부율 수기 편집 | Step 3 raw 셀 편집 | `get/update_allocation_rates` |

## 도구 7개

| # | 도구 | 기능 |
|---|---|---|
| 1 | `extract_filtered` | Excel raw에서 필터링 추출 (시트/월/회사/컬럼) |
| 2 | `verify_sums` | 조직 5계층 합계 결정론 검증 |
| 3 | `write_cells` | openpyxl 셀 단위 편집 + 자동 백업 + dry-run |
| 4 | `generate_diff_candidates` | \|10백만\| 이상 Diff 후보 추출 |
| 5 | `get_allocation_rates` | 26BP raw 배부율 조회 + 합 100% 검증 |
| 6 | `update_allocation_rates` | 배부율 변경 (write_cells 안전 정책 + tolerance) |
| 7 | `get_exchange_rates` | 한국수출입은행 환율 API 조회 (휴일 fallback + JPY/IDR 정규화) |

전 도구 공통:
- `render_format: "excel" | "live_artifact" | "both"` Live Artifact 출력 옵션
- `artifact_hints` 자동 생성 → Claude Desktop이 시각화 자동 렌더링

## 사용 예시 (자연어)

```
"26BP 3월 raw에서 본사 인건비만 추출해서 합계 검증해줘"
→ extract_filtered + verify_sums

"3월 배부율 Live Artifact로 보여줘"
→ get_allocation_rates(render_format="live_artifact")

"오늘 환율 조회해서 26BP 환율 시트에 USD/EUR/JPY 적용하고 외화 환산 합계 검증해줘"
→ get_exchange_rates + write_cells + verify_sums
```

## 빠른 시작

```powershell
# Windows
git clone https://github.com/hjsh200219/humax-mcp.git
cd humax-mcp
.\scripts\install.ps1
# .env에 EXCHANGE_RATE_API_KEY 입력
# Claude Desktop 재시작
```

업데이트:

```powershell
.\scripts\update.ps1
```

## 설계 문서

- [MCP 설계서](docs/prd/mcp-design-plan.md) — 도구 7개 상세 spec, 안전 정책, Pre-mortem 7 시나리오, 테스트 plan
- [강의 계획서](docs/prd/humax-lecture-plan.md) — 2차 (Cowork + MCP) + 3차 (Code/바이브) 강의 구성

## 안전 정책 (P1-P5)

1. **원본 보존 우선** — read-only 기본, write는 명시적 + 백업 강제
2. **결정론은 Python에 위임** — LLM 산술 금지
3. **토큰 효율** — 필터된 응답, 페이지네이션
4. **안전** — 백업 + dry-run + 감사 로그
5. **자연어 호출 가능** — 실무자 CLI 학습 부담 0

## 거버넌스

- 사내 데이터 (Excel raw / 배부율 / CC 마스터) git push 금지 — `.gitignore` + CI 정규식 스캔 2중 차단
- API 키 (`EXCHANGE_RATE_API_KEY`, `ANTHROPIC_API_KEY`) `.env` 보관
- 외부 API: `oapi.koreaexim.go.kr` (공공 데이터, PII 무관) 사내 방화벽 허용 필요
- Anthropic API 외부 호출 정책 사내 IT 확인 필수

## 로드맵

| 버전 | 내용 |
|---|---|
| v0.1 | 도구 7개 + Live Artifact + GitHub Private repo 배포 (현재 설계) |
| v0.2 | 적요 활용 + 고급 배부 + 사내 PC 1대 서버화 (HTTP/SSE) |
| v0.3 | SAP API 직접 연동 (GUI Script / OData / RFC) |
| v0.4 | 전사 확대 — 부서별 MCP (sales/hr/scm 등) + 사내 마켓플레이스 |

## 라이선스

MIT
