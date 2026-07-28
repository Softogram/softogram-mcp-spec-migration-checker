"""Registers the basket server's optional debug logging capability."""

from mcp.server import Server


def enable_debug_logging(mcp: Server) -> None:
    """Ask the client to raise our logging verbosity for troubleshooting."""
    mcp.set_logging_level("debug")
