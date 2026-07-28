from starlette.applications import Starlette

app = Starlette()


@app.route("/mcp", methods=["POST"])
async def mcp_endpoint(request):
    body = await request.json()
    return handle_jsonrpc(body)
