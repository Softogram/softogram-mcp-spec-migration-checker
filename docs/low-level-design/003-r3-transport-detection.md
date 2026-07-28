# LLD 003 - R3 Detectability and Transport Signal Order

**Status:** Settled - written 2026-07-28 to close issues #20 and #21, the last two design gates blocking implementation, on the day of the ship push.
**Links:** [HLD 001](../high-level-design/001-scan-pipeline.md) ("R3: transport detection and the 'can't tell' case") - [LLD 001](001-rule-definition-format.md) (matcher contract, the cannot-tell marker) - [LLD 002](002-finding-model-report-and-exit-codes.md) (NEEDS-MANUAL-CHECK rendering) - `docs/PRD.md` sections 1, 4.1, 8 - GitHub issues [#20](https://github.com/Softogram/softogram-mcp-spec-migration-checker/issues/20), [#21](https://github.com/Softogram/softogram-mcp-spec-migration-checker/issues/21), [#9](https://github.com/Softogram/softogram-mcp-spec-migration-checker/issues/9).
**Last updated:** 2026-07-28

This document uses the same terms as HLD 001's glossary (Rule, Matcher, Finding, Severity, Confidence tier).

## Why this LLD exists

HLD 001 already settled R3's shape in prose: three outcomes (will-break, silent, NEEDS-MANUAL-CHECK), a four-signal detection order strongest-first, and the governing rule that only confidence - not mere plausibility - promotes a finding to "This will break." What it left as an open prerequisite, tracked as issue #20, is a sharper question: does R3 even have a real target in application code to match against, given that `Mcp-Method` and `Mcp-Name` are transport-layer HTTP headers, not something application code typically touches directly?

## #20 - Does R3 have an app-code match target?

**Answer: narrowed, not abandoned.**

`Mcp-Method` and `Mcp-Name` are required on Streamable HTTP POST requests (PRD section 1, official changelog). Streamable HTTP is a *transport* - the layer that turns MCP messages into HTTP requests and responses. In the official MCP Python SDK, a server that mounts the SDK's own Streamable HTTP transport (the `streamable_http_app()` / `transport="streamable-http"` style of wiring) gets its request/response handling done by the SDK. If the SDK's transport implementation adds these two headers internally, every server that uses it gets compliance for free after an SDK version bump - with nothing in *that server's own code* for a static reader to flag. Firing "This will break" on such a server would be a false alarm: the code the tool is reading isn't what would actually break.

The genuine, honest target is different: a server whose author did **not** use the SDK's built-in transport, and instead hand-rolled their own HTTP endpoint for MCP - a raw ASGI callable, or a Starlette/FastAPI route that reads a JSON-RPC-shaped body and dispatches it manually. That code owns its own request/response handling, including headers, so whether it reads or sets `Mcp-Method`/`Mcp-Name` is a real, visible fact about that file - and a real gap if absent.

**R3's redefined match target:** hand-rolled MCP-over-HTTP endpoint code that shows no evidence of handling the two required headers. Not "any Streamable HTTP server missing the headers" in the abstract - that broader claim isn't honestly detectable from application source alone.

## #21 - Signal order and the NEEDS-MANUAL-CHECK outcome

Applying HLD 001's settled signal order (strongest first) to the narrowed target above:

| # | Signal | What it looks like in code | Outcome |
|---|---|---|---|
| 1 | Hand-rolled MCP HTTP endpoint present, no reference to either header name anywhere in the file | An ASGI app / Starlette or FastAPI route that parses a JSON-RPC-shaped request body, with no string literal `"Mcp-Method"` or `"Mcp-Name"` in the file | **This will break** (Confirmed) |
| 2 | Hand-rolled MCP HTTP endpoint present, both header names appear as string literals in the file | Same shape as above, but the code reads or sets both headers | Silent - genuinely compliant |
| 3 | SDK's own Streamable HTTP transport is mounted (`transport="streamable-http"` argument, or the SDK's `streamable_http_app()` / equivalent construct) | The literal transport value at the server's run call site | Silent - the SDK complies on the server's behalf, per #20 |
| 4 | A literal stdio transport value, or a run call with no transport argument at all (SDK default is stdio) | `mcp.run()` with no argument, or `mcp.run(transport="stdio")` | Silent - this rule does not apply to local-only servers |
| 5 | Transport value is decided at runtime - a CLI flag, an environment variable, or a config file read at startup | `mcp.run(transport=os.environ["TRANSPORT"])`, or a value threaded in from `argparse` | **NEEDS-MANUAL-CHECK** - no static signal resolves this |
| 6 | A web framework (Starlette, FastAPI, uvicorn) is imported, but neither a hand-rolled endpoint (signal 1/2) nor any transport call (signal 3/4) is found | A bare `import starlette` with no matching endpoint or run call in scope | **NEEDS-MANUAL-CHECK** - the weakest signal alone must never promote to will-break, per HLD 001's governing rule |

This table is exhaustive over the file: the matcher evaluates signals in this order and stops at the first one that applies. Signals 1-2 require detecting a hand-rolled endpoint shape first (a decorated ASGI/Starlette/FastAPI route or callable, in a file whose body also references parsing a JSON-RPC-style request), since without that shape there is nothing to call "missing" - a plain script with no HTTP endpoint at all simply falls through to signals 3-6.

## Report rendering (coordinates with LLD 002)

No change to LLD 002's shape is needed. R3's `NEEDS-MANUAL-CHECK` case already has a first-class outcome in the finding model (LLD 001 section 4, LLD 002 section 1): rule id plus affected files, no line number, rendered under its own "NEEDS MANUAL CHECK" section using R3's `manual_check_text`. R3's `manual_check_text` in `rules.toml` should plainly state the narrowing from #20 - that the tool can only see this from hand-rolled transport code, not from SDK-managed servers - so a reader who gets NEEDS-MANUAL-CHECK understands exactly what to go check by hand.

## R3's fourth fixture (issue #9 acceptance criteria)

Per HLD 001 stage testing strategy and issue #9, R3 needs four fixtures, now concretely defined:

1. **Web-exposed, missing headers** (signal 1) - hand-rolled ASGI/Starlette endpoint parsing MCP requests, no header literals anywhere. Must produce "This will break".
2. **Web-exposed, headers handled** (signal 2) - same shape, both header literals present. Must be silent.
3. **stdio-only** (signal 4) - `mcp.run()` with no transport argument, or an explicit `"stdio"` literal. Must be silent, and the test must assert silence explicitly (not just absence of a crash), since HLD 001 stage testing calls out must-not fixtures as the more important half.
4. **Can't tell** (signal 5) - transport value read from an environment variable at runtime. Must produce `NEEDS-MANUAL-CHECK`, must not affect the exit code, and must not appear in the same report section as "Worth checking" findings.

## Correction to HLD 001

HLD 001's "R3: transport detection and the 'can't tell' case" section ends with: *"Whether R3 has a real app-code target at all... is a dedicated LLD investigation... this must be answered before R3 ships as Confirmed/'This will break'."* That investigation is this document. R3 ships as Confirmed/"This will break" only for the narrowed hand-rolled-transport target defined in #20 above - not for the broader "any Streamable HTTP server" framing HLD 001 originally posed as an open question.

## Who's waiting on this

Directly: issue #9 (R3 implementation), now unblocked. Its acceptance criteria are updated per the four-fixture definition above.

## Next step

Settled. Issue #9 can proceed using the match target and signal table above.
