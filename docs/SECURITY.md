# SECURITY.md

> 보안 정책 + PII 차단 + 비밀 관리.

## 신뢰 경계

| 경계 | 안 (trusted) | 바깥 (untrusted) |
|---|---|---|
| 사내 PC ↔ Claude Desktop | MCP stdio (로컬) | — |
| MCP 서버 ↔ Excel 파일 | 사내 데이터 | — |
| MCP 서버 ↔ 환율 API | `oapi.koreaexim.go.kr` (공공 데이터) | — |
| MCP 서버 ↔ Anthropic API | 사내 IT 정책 확인 필수 | LLM 응답 |

## 비밀 (Secrets)

- `EXCHANGE_RATE_API_KEY` — 한국수출입은행 발급. `.env`만, 코드/로그/audit 절대 금지.
- `ANTHROPIC_API_KEY` — (사용 시) `.env`만.
- `.env`, `.env.*` `.gitignore` + `.claudeignore` 2중 차단.

### 누출 차단

- pre-commit 훅에서 `.env` 스테이지 차단 (`.pre-commit-config.yaml`)
- CI에서 정규식 스캔 (xlsx/csv/jsonl 파일 + `EXCHANGE_RATE_API_KEY=` 패턴)
- `audit_*.jsonl`은 0o600 권한, `.humax-mcp/audit/` 디렉토리 0o700

## PII 차단

`schemas/raw_bp26.PII_COLUMNS = ["Text", "Vendor\nName", "URL", "Doc no."]`

- aggregator 진입 전 `core/aggregator`에서 drop
- 응답 직렬화 전 `core/token_guard` 정규식 2차 점검 (RRN, KR phone, 사번)
- 정규식 패턴은 `core/token_guard.py` 상수로 명시

### 정규식 (한국 PII)

- 주민등록번호: `\b\d{6}-\d{7}\b`
- 휴대전화: `\b01[0-9]-\d{4}-\d{4}\b`
- 사번: 프로젝트 규칙 (e.g. `\b[A-Z]\d{6}\b`)

## 사내 데이터 거버넌스

- 사내 데이터 (`docs/references/*.xlsx`) git push 금지 — `.gitignore` 강제
- 단, `fixtures/templates/*.xlsx`는 데이터 클리어드 → 커밋 허용 (`scripts/build_fixture_templates.py`)
- 백업 파일 (`.backup/`) git push 금지

## 외부 통신

- 한국수출입은행 API: 사내 방화벽 허용 필요. PII 무관 공공 데이터.
- Anthropic API: 사내 IT 정책 확인 필수.
- 다른 외부 호출 없음.

## 의존성

- `mcp`, `openpyxl`, `pandas`, `pydantic`, `python-dotenv`, `httpx` — 모두 mainstream
- `pip-audit` 또는 `safety` 정기 실행 권장 (Phase 4 setup-reviewer에서 `scripts/gc.sh`에 후보)

## OWASP-ish 점검

| 항목 | 적용 여부 |
|---|---|
| Injection (SQL/Command) | 해당 없음 (DB/shell 호출 없음) |
| Broken Auth | 해당 없음 (stdio, 로컬) |
| Sensitive Data Exposure | PII 정규식 + .env + .gitignore 3중 차단 |
| XXE | XLSX 파싱 openpyxl 위임 (XXE 대비 stdlib 기본) |
| Path Traversal | `core/excel_io.assert_xlsx_path` + write `output_path != file_path` |
| Insecure Deserialization | pydantic v2 strict mode |
| Components w/ Known Vulns | pip-audit (TODO) |
| Insufficient Logging | audit JSONL 전 도구 적용 ✅ |

## 회의적 검증

- ".env가 gitignored" ≠ "이미 커밋된 적 없다" → `git log -p --all -- .env`로 history 확인
- "PII 정규식 있음" ≠ "모든 PII 잡힌다" → 신규 PII 발견 시 즉시 추가
- "audit 로그 남는다" ≠ "감사 가능하다" → 정기 로그 검토 절차 필요 (v0.2)
