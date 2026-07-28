from mcp.server import Server

server = Server("basket-server")


@server.set_logging_level()
async def handle_set_logging_level(level):
    return None
