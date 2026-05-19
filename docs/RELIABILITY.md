# RELIABILITY.md

> 안정성 기준 + 백업/복구/감사 정책.

## 백업 정책 (P1 핵심)

- write 도구 진입 시 `core/backup.create_backup` 호출 강제
- 백업 위치: `<src.parent>/.backup/<stem>_<YYYYMMDD_HHMMSS>.xlsx`
- sha256 검증: src와 dest 불일치 시 즉시 `BackupFailed` raise
- `prune_backups(keep=10)` — 가장 최근 10개만 유지

### 적용 도구

- `write_cells` (tools/write.py)
- `update_allocation_rates` (tools/allocation_set.py)
- `apply_golden_template` (tools/template_engine.py)
- `restore_backup` (tools/restore.py) — 복구 자체도 백업 후 진행

## Dry-run 정책

모든 mutate 도구는 `dry_run: bool = False` 파라미터 노출. dry_run=True 시:
- 백업 생성 X
- 원본 파일 sha256 변경 없음 (테스트로 검증)
- 의도된 변경 미리보기만 반환

## output_path 정책

- write 도구는 `output_path != file_path` 강제
- 동일 시 `OverwriteOriginalForbidden` raise

## 감사 로그

- `core/audit.audited(tool_name)` 데코레이터, `tools/__init__.register_all`에서 모든 도구에 적용
- JSONL 일일 로그: `.humax-mcp/audit/audit_YYYYMMDD.jsonl`
- 디렉토리 0o700, 파일 0o600 권한
- 기록 필드: timestamp, tool, user, file_path, sheet_name, dry_run, success, error, duration_ms, action_summary, backup_path
- 환경 변수 `HUMAX_MCP_AUDIT_DIR`로 위치 override

## 외부 API 안정성

### 한국수출입은행 환율 API (`tools/exchange.py`)

- 12시간 in-process 캐시
- 7-day fallback chain: D → D-1 → ... → D-7
- ±20% sanity check (전일 대비 급변 차단)
- JPY/IDR per-100 정규화
- 휴일 처리: `NO_DATA_FOR_DATE` → 자동 이전 영업일 시도
- 키 미설정: `API_KEY_MISSING` raise

## 에러 코드 (40+)

`core/errors.py` — PRD §4 매핑.

| 카테고리 | 코드 |
|---|---|
| File I/O | `FILE_NOT_FOUND`, `FILE_LOCKED`, `SHEET_NOT_FOUND` |
| Validation | `SCHEMA_MISMATCH`, `INVALID_COLUMN`, `INVALID_COMPANY` |
| Write Safety | `BACKUP_FAILED`, `OVERWRITE_ORIGINAL_FORBIDDEN`, `TOO_MANY_UPDATES`, `VERIFICATION_FAILED` |
| Allocation | `RATE_SUM_NOT_100`, `INVALID_RATE`, `CC_BASIS_NOT_FOUND` |
| Exchange | `API_KEY_MISSING`, `API_REQUEST_FAILED`, `FALLBACK_EXHAUSTED`, `FUTURE_DATE` |
| Template | `TEMPLATE_NOT_FOUND`, `TEMPLATE_MALFORMED`, `BINDING_NOT_FOUND` |
| Restore | `BACKUP_NOT_FOUND`, `RESTORE_FAILED` |

## 복구 절차

1. 사용자가 `.backup/` 디렉토리 확인 (또는 audit 로그에서 `backup_path` 조회)
2. `restore_backup(backup_path=..., target_path=...)` 호출
3. restore도 자동 백업 (현재 파일 → `.backup/`) 후 덮어쓰기
4. sha256 검증 후 완료

## SLA / 목표

- write 도구 호출 → 응답 < 5초 (10K 셀 기준)
- extract_filtered 응답 < 3초 (15,007행 raw)
- audit 로그 손실 0건 (디스크 풀 등 OSError 시 도구 호출은 진행, audit 실패 로그는 stderr)

## 회의적 검증

- "백업 생성됐다" ≠ "복구 가능하다" → restore E2E 테스트 필수
- "테스트 통과" ≠ "회귀 차단" → 커버리지 게이트 필수
- "에러 raise됨" ≠ "사용자가 이해 가능" → 한국어 메시지 검토
