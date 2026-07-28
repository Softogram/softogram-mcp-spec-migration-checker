from mcp.server import Server

server = Server("basket-server")


@server.list_tools()
async def handle_list_tools():
    return []
