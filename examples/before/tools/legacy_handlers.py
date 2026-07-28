"""Old-style low-level request handlers, written before the 2026-07-28 update.

Demonstrates three things the update removes outright: the
resources/subscribe and resources/unsubscribe request handlers (replaced
by subscriptions/listen), the logging/setLevel request handler (log
level now travels per-request in _meta instead), and opting into SSE
stream resumability via event_store (resumability is removed from the
Streamable HTTP transport entirely). See examples/README.md for what
changes in examples/after/ - short answer: nothing replaces this file,
these patterns are just gone.

event_store is a FastMCP-level constructor argument; subscribe/
unsubscribe/set_logging_level are low-level Server decorators - checked
against the real SDK, these are two different classes' APIs, not
interchangeable, so this file uses both.

Validated importable against a real installed mcp==1.29.0.
"""

from mcp.server import Server
from mcp.server.fastmcp import FastMCP


class BasketEventStore:
    """Stores basket-change events so a dropped connection can resume."""


resumable_mcp = FastMCP("basket-server-legacy", event_store=BasketEventStore())

server = Server("basket-server-legacy")


@server.subscribe_resource()
async def handle_subscribe(uri: str) -> None:
    """Old-style handler for a client subscribing to a basket resource."""


@server.unsubscribe_resource()
async def handle_unsubscribe(uri: str) -> None:
    """Old-style handler for a client unsubscribing from a basket resource."""


@server.set_logging_level()
async def handle_set_logging_level(level: str) -> None:
    """Old-style handler for a client changing the server's log level."""
