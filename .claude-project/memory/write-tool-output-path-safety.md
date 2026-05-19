---
name: write-tool-output-path-safety
description: openpyxl write 도구는 output_path != file_path 강제 + 백업 + dry_run + post-verify 4중 안전
type: reference
created: 2026-05-19
---

`write_cells` / `update_allocation_rates` 등 Excel write 도구의 4중 안전 패턴 (PRD P1 원본 보존):

1. **백업 강제**: `create_backup(file_path)` + sha256 verify, 실패 시 BACKUP_FAILED로 abort
2. **output_path 검증**: `output_path == file_path` 이면 OVERWRITE_ORIGINAL_FORBIDDEN raise (절대 원본 덮어쓰기 금지)
3. **dry_run**: 적용 전 변경 셀 리스트 반환, sha256는 원본과 동일해야 함 (no-op 보장)
4. **post-write verify**: 쓰기 직후 다시 load해서 실제 셀 값이 의도와 일치하는지 재확인

추가: `FILE_LOCKED` (PermissionError) / `SCHEMA_MISMATCH` 별도 에러 코드로 raise — 일반 IOError로 묶지 않는다.

```python
if output_path.resolve() == file_path.resolve():
    raise OverwriteOriginalForbiddenError(...)
backup = create_backup(file_path)  # sha256 verified
if dry_run:
    return WriteResult(updates=planned, sha256_after=sha256_before)
# apply
wb.save(output_path)
verify_cells(output_path, planned)  # re-read assertion
```

**Why:** S1 (원본 깨짐) pre-mortem 시나리오 대응. file #1 한계 1번 "원본 파일 훼손, 복구불가"의 직접 fix.

**How to apply:** 신규 Excel write/update 도구 모두 동일 4중 안전 정책 상속. test_write.py가 4중 패턴 테스트 템플릿. output_path 검증은 `.resolve()` 후 비교 (심볼릭링크 우회 차단).
