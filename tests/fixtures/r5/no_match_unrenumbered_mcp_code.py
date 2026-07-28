# Regression guard: -32601 (METHOD_NOT_FOUND) is a real MCP/JSON-RPC error
# code, but the final changelog's error-code allocation policy does not
# list it as renumbered - only -32001, -32002, -32003, and -32004 moved.
# Flagging every MCP-shaped code would mean guessing at ones nobody
# confirmed are changing (docs/PRD.md section 9).


def handle(err):
    if err.code == -32601:
        raise ValueError("unknown method")
