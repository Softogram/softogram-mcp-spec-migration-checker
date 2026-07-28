"""A hand-rolled MCP-over-HTTP transport for a shopping-basket server.

This bypasses the official MCP Python SDK's transport entirely and parses
raw ASGI scope/receive/send directly - something real teams sometimes do
for custom auth or routing needs the SDK didn't support at the time. It's
written the old way: it reads the caller's session id straight out of the
raw HTTP headers and uses it as an implicit memory key, and it doesn't
know about the two new required headers.

Validated importable against real MCP servers by hand - see
examples/README.md for exactly what changes in examples/after/.
"""

import json

BASKETS = {}


async def app(scope, receive, send):
    """The raw ASGI entrypoint for this hand-rolled MCP endpoint."""
    assert scope["type"] == "http"

    headers = {key.decode("latin-1"): value.decode("latin-1") for key, value in scope["headers"]}
    session_id = headers.get("mcp-session-id")

    event = await receive()
    body = json.loads(event.get("body") or b"{}")

    if body.get("method") == "tools/call" and body["params"]["name"] == "add_item":
        item = body["params"]["arguments"]["item"]
        BASKETS.setdefault(session_id, []).append(item)
        result = {"basket": BASKETS[session_id]}
    elif body.get("method") == "tools/call" and body["params"]["name"] == "get_basket":
        if session_id not in BASKETS:
            error_code = -32002
            result = {"error": {"code": error_code, "message": "Basket not found"}}
        else:
            result = {"basket": BASKETS[session_id]}
    else:
        result = {"error": {"code": -32601, "message": "Unknown method"}}

    payload = json.dumps(result).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": payload})
