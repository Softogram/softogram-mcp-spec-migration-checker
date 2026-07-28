# Regression guard: set_logging_level is not a method on ServerSession
# (confirmed against the real installed SDK) - it only exists as the
# low-level Server's decorator for registering the removed request
# handler, which belongs to R8, not this rule. See
# docs/LEARNINGS.md's 2026-07-28 entry.
from mcp.server import Server

server = Server("basket-server")


@server.set_logging_level()
async def handle_set_logging_level(level):
    return None
