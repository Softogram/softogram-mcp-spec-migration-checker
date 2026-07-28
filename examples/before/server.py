"""A small shopping-basket MCP server, written the old way.

Every request remembers which basket it belongs to using the session the
transport hands the server - the pattern the 2026-07-28 spec update
removes. See examples/README.md for what changes in examples/after/.
"""

import os

from mcp.server import Server

BASKETS = {}

mcp = Server("basket-server")


@mcp.tool()
async def add_item(ctx, item: str) -> str:
    """Add an item to the caller's basket."""
    session_id = ctx.request_context.headers.get("Mcp-Session-Id")
    BASKETS.setdefault(session_id, []).append(item)
    return f"Added {item} to basket {session_id}"


@mcp.tool()
async def get_basket(ctx) -> list[str]:
    """Return the caller's current basket contents."""
    return BASKETS.get(ctx.session_id, [])


def handle_error(err) -> None:
    """Raise a friendlier error for a known MCP error code."""
    if err.code == -32601:
        raise ValueError("Unknown basket method")


mcp.run(transport=os.environ.get("BASKET_TRANSPORT", "stdio"))
