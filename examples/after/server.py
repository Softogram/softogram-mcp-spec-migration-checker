"""The same shopping-basket MCP server, migrated to the 2026-07-28 spec.

The hand-rolled ASGI transport is gone entirely - this now uses the
official MCP Python SDK's own Streamable HTTP transport, which handles
the two new required headers internally. Every request carries an
explicit basket handle instead of an implicit session id. See
examples/README.md for exactly what changed and why. Validated
importable against a real installed `mcp` package (mcp>=2.0).
"""

from mcp.server.mcpserver import MCPServer
from mcp.types import METHOD_NOT_FOUND

BASKETS = {}

mcp = MCPServer("basket-server")


@mcp.tool()
async def add_item(basket_handle: str, item: str) -> str:
    """Add an item to the basket identified by basket_handle."""
    BASKETS.setdefault(basket_handle, []).append(item)
    return f"Added {item} to basket {basket_handle}"


@mcp.tool()
async def get_basket(basket_handle: str) -> list[str]:
    """Return the contents of the basket identified by basket_handle."""
    return BASKETS.get(basket_handle, [])


def handle_error(err) -> None:
    """Raise a friendlier error for a known MCP error."""
    if err.code == METHOD_NOT_FOUND:
        raise ValueError("Unknown basket method")


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
