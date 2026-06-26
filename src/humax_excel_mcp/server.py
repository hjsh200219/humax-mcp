"""FastMCP server entry point. Tool registration in US-013."""

from __future__ import annotations


def main() -> None:
    """Run the MCP server over stdio."""

    mcp = build_server()
    mcp.run()


def build_server():
    """Build FastMCP server with all 11 tools registered (v0.2.0)."""
    from mcp.server.fastmcp import FastMCP

    from .tools import register_all

    mcp = FastMCP("humax-excel-mcp")
    register_all(mcp)
    return mcp


if __name__ == "__main__":
    main()
