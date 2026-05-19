"""FastMCP tool registration. All 7 tools."""

from __future__ import annotations

from ..core.audit import audited
from .allocation_get import get_allocation_rates as _get_allocation_rates
from .allocation_set import update_allocation_rates as _update_allocation_rates
from .diff import generate_diff_candidates as _generate_diff_candidates
from .exchange import get_exchange_rates as _get_exchange_rates
from .extract import extract_filtered as _extract_filtered
from .verify import verify_sums as _verify_sums
from .write import write_cells as _write_cells

TOOL_NAMES = [
    "extract_filtered",
    "verify_sums",
    "write_cells",
    "generate_diff_candidates",
    "get_allocation_rates",
    "update_allocation_rates",
    "get_exchange_rates",
]


def register_all(mcp) -> None:
    """Register all 7 tools on the FastMCP instance."""
    mcp.tool()(audited("extract_filtered")(_extract_filtered))
    mcp.tool()(audited("verify_sums")(_verify_sums))
    mcp.tool()(audited("write_cells")(_write_cells))
    mcp.tool()(audited("generate_diff_candidates")(_generate_diff_candidates))
    mcp.tool()(audited("get_allocation_rates")(_get_allocation_rates))
    mcp.tool()(audited("update_allocation_rates")(_update_allocation_rates))
    mcp.tool()(audited("get_exchange_rates")(_get_exchange_rates))
