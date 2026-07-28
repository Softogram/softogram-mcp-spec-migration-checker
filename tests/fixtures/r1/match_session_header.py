def handler(request):
    session_id = request.headers.get("Mcp-Session-Id")
    return session_id
