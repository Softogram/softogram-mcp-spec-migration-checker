from mcp.server import Server

server = Server("basket-server")


@server.subscribe_resource()
async def handle_subscribe(uri):
    return None
