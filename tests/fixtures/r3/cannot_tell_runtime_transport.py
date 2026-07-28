import os

from mcp.server import Server

mcp = Server("basket")

mcp.run(transport=os.environ["MCP_TRANSPORT"])
