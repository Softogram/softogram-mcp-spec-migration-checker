"""A basket-server debug tool that logs through the MCP session itself.

Uses the real MCP Python SDK's FastMCP API: a tool function that takes a
Context parameter and calls the session's logging capability directly.
Roots, Sampling, and Logging are reported as being phased out - this is
the Logging one. Validated importable against a real installed
`mcp` package (FastMCP + Context).
"""

from mcp.server.fastmcp import Context, FastMCP

mcp = FastMCP("basket-server-debug-tools")


@mcp.tool()
async def enable_debug_logging(ctx: Context) -> str:
    """Send a debug-level log message back through the client's MCP session."""
    await ctx.session.send_log_message("debug", "Basket server debug logging enabled.")
    return "debug logging enabled"
