from starlette.applications import Starlette

app = Starlette()


@app.route("/mcp", methods=["POST"])
async def mcp_endpoint(request):
    method = request.headers.get("Mcp-Method")
    name = request.headers.get("Mcp-Name")
    body = await request.json()
    return handle_jsonrpc(body, method, name)
