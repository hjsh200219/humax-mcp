"""US-013 server integration test."""

from __future__ import annotations

from pathlib import Path

import pytest

from humax_excel_mcp.server import build_server
from humax_excel_mcp.tools import TOOL_NAMES

pytestmark = pytest.mark.asyncio


async def test_server_registers_eleven_tools() -> None:
    mcp = build_server()
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert names == set(TOOL_NAMES)
    assert len(names) == 11


async def test_module_imports_without_error() -> None:
    import humax_excel_mcp.server  # noqa: F401
    assert hasattr(humax_excel_mcp.server, "main")
    assert hasattr(humax_excel_mcp.server, "build_server")


async def test_audit_log_written(
    sample_26bp_path: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    audit_root = tmp_path / "audit"
    monkeypatch.setenv("HUMAX_MCP_AUDIT_DIR", str(audit_root))
    from humax_excel_mcp.core.audit import audited
    from humax_excel_mcp.tools.extract import extract_filtered

    wrapped = audited("extract_filtered")(extract_filtered)
    await wrapped(str(sample_26bp_path), "예산+실적", max_rows=5)
    files = list(audit_root.glob("audit_*.jsonl"))
    assert files
    content = files[0].read_text(encoding="utf-8")
    assert "extract_filtered" in content
    assert "duration_ms" in content
