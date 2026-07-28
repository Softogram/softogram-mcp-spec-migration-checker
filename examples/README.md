# Before/after example: a shopping-basket MCP server

This folder has two copies of the same small MCP (Model Context Protocol) server: a tool that lets an AI app add items to a shopping basket and read it back.

`before/` is written the old way: a hand-rolled MCP-over-HTTP transport that bypasses the official SDK entirely.
`after/` is the same server, migrated to the 2026-07-28 spec update using the official MCP Python SDK's own transport.

Both are real, runnable code, checked against the actual `mcp` package (not just hand-written to look plausible):

- `before/server.py` was driven end-to-end with a real ASGI call (fake `scope`/`receive`/`send`) to confirm it genuinely works.
- `before/tools/logging_setup.py` was imported against a real installed `mcp==1.29.0` (the last release before the spec update).
- `after/server.py` and `after/tools/logging_setup.py` were imported against a real installed `mcp==2.0.0` (the first release after the spec update, published the same day it landed).

Run the checker on both to see the difference for yourself:

```
mcp-migration-check examples/before
mcp-migration-check examples/after
```

## What's different, and why

**A hand-rolled transport became the SDK's own (R1, R3).**
The old server reads the raw `Mcp-Session-Id` header directly out of the ASGI request, and never sends the two new required headers (`Mcp-Method`, `Mcp-Name`) at all - because it never uses the SDK's transport in the first place, it hand-rolls its own ASGI app.
Checking the real installed SDK confirmed neither of these headers is exposed to application code by any documented API - genuinely reading them by name only happens in code that bypasses the SDK's transport and session handling entirely.
The migrated server drops the hand-rolled transport and uses the SDK's own `mcp.run(transport="streamable-http")` instead, which manages both headers internally - there's nothing left in the migrated server's own code for either rule to flag.

**Sessions became explicit handles (R2).**
The old server used the extracted session ID as the key for a `BASKETS` dictionary - so the server had to "remember" which basket belonged to which session.
The migrated server instead takes a `basket_handle` argument directly on each tool call - an explicit, visible ID the client passes back every time, instead of something hidden inside a session.

**Hand-written error numbers became SDK constants (R5).**
The old server computed the error code `-32601` by hand and assigned it to a variable before using it.
Trusted sources report that MCP's error numbers may change in this update, but nobody has confirmed exactly which ones - so hard-coding a number is a bet that might not pay off.
The migrated server imports the real `mcp.types.METHOD_NOT_FOUND` constant instead, so if the number ever changes, the SDK's own update carries the fix automatically.

**A phased-out logging capability became plain Python logging (R4).**
The old server's debug tool calls `ctx.session.send_log_message(...)` - the real MCP Python SDK's own Logging capability, which the SDK's own source now marks deprecated as of 2026-07-28.
The migrated server just uses Python's ordinary standard-library `logging` module, which the spec update has no effect on at all.

## A false positive we caught by checking the real SDK

An earlier version of this example used `ctx.session_id` (a plain attribute read) as the R1 trigger.
Installing the real `mcp` package and reading its source showed that `Context.session_id` is a legitimate, still-supported convenience property in the *new* SDK too - it exposes the transport's connection id, not the removed protocol-level session handshake.
Flagging it would have meant the tool cried wolf on correct, migrated code.
R1 was narrowed to the pattern that's actually only ever seen in hand-rolled, non-SDK transport code: reading the raw header by its literal name.
See `docs/LEARNINGS.md`'s 2026-07-28 entry for the full story, and `tests/fixtures/r1/no_match_sdk_session_id_property.py` for the regression test that guards it.
