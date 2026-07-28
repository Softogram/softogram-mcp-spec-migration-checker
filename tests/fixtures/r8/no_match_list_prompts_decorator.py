from mcp.server import Server

server = Server("basket-server")


@server.list_prompts()
async def handle_list_prompts():
    return []
