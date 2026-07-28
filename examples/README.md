# Before/after example: a shopping-basket MCP server

This folder has two copies of the same small MCP (Model Context Protocol) server: a tool that lets an AI app add items to a shopping basket and read it back.

`before/` is written the old way, against the spec version MCP servers use today.
`after/` is the same server, migrated to the 2026-07-28 spec update.

Run the checker on both to see the difference for yourself:

```
mcp-migration-check examples/before
mcp-migration-check examples/after
```

## What's different, and why

**Sessions became explicit handles (R1, R2).**
The old server let the transport hand it a session ID, and used that ID as the key for a `BASKETS` dictionary - so the server had to "remember" which basket belonged to which session.
The 2026-07-28 update removes sessions entirely: every request must carry everything it needs on its own.
The migrated server instead takes a `basket_handle` argument directly - an explicit, visible ID the client passes back on every call, instead of something hidden inside a session.

**Hand-written error numbers became SDK constants (R5).**
The old server checked `err.code == -32601` by hand.
Trusted sources report that MCP's error numbers may change in this update, but nobody has confirmed exactly which ones - so hard-coding a number is a bet that might not pay off.
The migrated server imports `METHOD_NOT_FOUND` from the SDK instead, so if the number ever changes, the SDK's own update carries the fix automatically.

**A phased-out logging capability became plain Python logging (R4).**
The old server used the MCP SDK's own `set_logging_level` call - part of the SDK's Logging capability, which trusted sources report is being phased out (with a year's grace period).
The migrated server just uses Python's ordinary standard-library `logging` module, which the spec update has no effect on at all.

**Transport stayed explicit, not runtime-decided (R3).**
The old server picked its transport from an environment variable at run time (`os.environ.get("BASKET_TRANSPORT", "stdio")`).
Reading code alone can never resolve a value that is only known once the program is actually run - so the checker reports this case as `NEEDS-MANUAL-CHECK` rather than guessing either way.
The migrated server just calls `mcp.run(transport="stdio")` directly.
This one isn't really "fixed" so much as made checkable: a real server might still legitimately decide its transport at runtime, in which case a human still needs to check by hand whether it uses the SDK's own transport (compliant automatically) or hand-rolled transport code (not compliant until the two new headers are added).
