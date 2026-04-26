"""Tools registration for Yandex MCP Server."""

import os

from mcp.server.fastmcp import FastMCP


def register_all_tools(mcp: FastMCP) -> None:
    """Register Metrika, Wordstat, and optionally Direct tools.

    Direct tools are registered by default. Set YANDEX_ENABLE_DIRECT=false
    in the environment to skip Direct registration (useful when running
    without a service account, or to keep Direct tools out of clients'
    context).
    """
    from .metrika import register_metrika_tools
    from . import wordstat
    from .webmaster import register_webmaster_tools

    register_metrika_tools(mcp)
    wordstat.register(mcp)
    register_webmaster_tools(mcp)

    if os.environ.get("YANDEX_ENABLE_DIRECT", "true").lower() == "true":
        from .direct import register_direct_tools
        register_direct_tools(mcp)
