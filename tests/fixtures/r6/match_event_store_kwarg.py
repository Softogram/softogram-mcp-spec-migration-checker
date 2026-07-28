from mcp.server.fastmcp import FastMCP


class DummyEventStore:
    """A placeholder implementing the EventStore interface for resumability."""


mcp = FastMCP("basket-server", event_store=DummyEventStore())
