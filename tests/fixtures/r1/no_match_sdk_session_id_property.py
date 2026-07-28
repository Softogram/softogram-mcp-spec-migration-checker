# Regression guard: reading ctx.session_id through the SDK's own Context is
# a legitimate, still-supported convenience property in the real MCP Python
# SDK (mcp>=2.0's Context.session_id) - it must NOT match R1. Confirmed by
# installing the real package and reading mcp/server/context.py; see
# docs/LEARNINGS.md's 2026-07-28 entry.


def handler(ctx):
    return ctx.session_id
