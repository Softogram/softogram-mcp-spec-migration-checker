"""Sets up ordinary Python logging for the basket server.

The old logging_setup.py asked the MCP client to raise its logging
verbosity via the SDK's Logging capability - one of the three features
reported as being phased out. The migrated version just uses Python's
own logging module instead, which the spec update does not affect.
"""

import logging

logger = logging.getLogger("basket-server")


def enable_debug_logging() -> None:
    """Raise this server's own log verbosity for troubleshooting."""
    logger.setLevel(logging.DEBUG)
