---
name: audited-file-path-arg-extension
description: audited() decorator의 file_path_arg 파라미터 — 신규 도구의 첫 인자가 file_path가 아닐 때 audit 키 매핑
type: reference
created: 2026-05-19
---

`core/audit.py` `audited()` decorator는 도구의 첫 positional arg를 `file_path`로 audit log에 기록. 신규 v0.1.1 도구는 첫 인자가 `source_file` (apply_golden_template / generate_report) 또는 `backup_path` (restore_backup)라 매핑이 깨짐.

해결: decorator signature를 `audited(tool_name: str, *, file_path_arg: str = "file_path")` 로 확장. 기본값으로 기존 7 도구 무수정 유지.

```python
# 신규 도구 register
mcp.tool()(audited("apply_golden_template", file_path_arg="source_file")(_apply_golden_template))
mcp.tool()(audited("restore_backup", file_path_arg="backup_path")(_restore_backup))
```

내부 동작: `kwargs.get(file_path_arg) or (args[0] if args else None)` — kwargs 우선, 없으면 첫 positional arg.

**알려진 한계 (v0.1.2 deferred):**
- `restore_backup`의 destructive in-place restore는 `output_path` (write target) 가 forensic audit에 더 유용하지만 현재는 `backup_path` (read source) 만 기록. RestoreBackupResult.restored_path는 caller에 반환되지만 audit log에는 없음.
- audit.py:68 `record["backup_path"] = getattr(result, "backup_path", None)` 의 RestoreBackupResult에는 backup_path attr 없음 (restored_path / pre_restore_backup_path 만 존재) — 항상 None.

**Why:** 백워드 호환 + 신규 도구 시그니처 자유도 균형. 단일 파라미터로 7 → 10 도구 확장.

**How to apply:** 신규 MCP 도구 추가 시 첫 인자가 file_path 아니면 register_all에서 file_path_arg 명시. forensic 정확도가 critical하면 v0.1.2 추후 fix (output_path 로깅 + RestoreBackupResult.backup_path attr 추가).
