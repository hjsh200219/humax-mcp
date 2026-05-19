"""JSONL audit logging per PRD §6.3."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Awaitable, Callable
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

from . import errors


def audit_dir() -> Path:
    base = Path(os.environ.get("HUMAX_MCP_AUDIT_DIR", ".humax-mcp/audit"))
    base.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(base, 0o700)
    except OSError:
        pass
    return base


def _write_record(record: dict[str, Any]) -> None:
    base = audit_dir()
    fname = base / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(fname, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    try:
        os.chmod(fname, 0o600)
    except OSError:
        pass


def audited(
    tool_name: str,
    *,
    file_path_arg: str = "file_path",
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Audit decorator. `file_path_arg` names the kwarg holding the primary file path
    for tools whose first arg is not literally `file_path` (e.g. `source_file`, `backup_path`)."""
    def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            t0 = time.time()
            primary_file = kwargs.get(file_path_arg)
            if primary_file is None and args:
                primary_file = args[0]
            record: dict[str, Any] = {
                "timestamp": datetime.now().astimezone().isoformat(),
                "tool": tool_name,
                "user": "system",
                "file_path": primary_file,
                "sheet_name": kwargs.get("sheet_name") or (args[1] if len(args) > 1 else None),
                "dry_run": kwargs.get("dry_run", False),
                "success": True,
                "error": None,
            }
            try:
                result = await fn(*args, **kwargs)
                record["duration_ms"] = int((time.time() - t0) * 1000)
                if hasattr(result, "data") and hasattr(result.data, "model_dump"):
                    pass
                record["action_summary"] = _summary(result)
                record["backup_path"] = getattr(result, "backup_path", None)
                _write_record(record)
                return result
            except errors.HumaxMCPError as exc:
                record["success"] = False
                record["error"] = {"code": exc.code, "message": exc.message}
                record["duration_ms"] = int((time.time() - t0) * 1000)
                _write_record(record)
                raise
            except Exception as exc:
                record["success"] = False
                record["error"] = {"code": "UNEXPECTED", "message": str(exc)}
                record["duration_ms"] = int((time.time() - t0) * 1000)
                _write_record(record)
                raise

        return wrapper

    return decorator


def _summary(result: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if hasattr(result, "summary"):
        try:
            out = result.summary.model_dump()
        except AttributeError:
            pass
    if hasattr(result, "metadata"):
        try:
            md = result.metadata
            if hasattr(md, "model_dump"):
                meta = md.model_dump()
            else:
                meta = md
            for k in ("returned_rows", "filtered_rows", "total_rows", "candidates_returned"):
                if isinstance(meta, dict) and k in meta:
                    out[k] = meta[k]
        except Exception:
            pass
    return out
