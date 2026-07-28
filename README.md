# mcp-migration-check

A small command-line tool that reads your Python MCP server's code and tells you what will break under the 2026-07-28 MCP spec update.
It never runs your code.
It only reads it (this is called static analysis).

## What's the problem?

MCP (Model Context Protocol) is a shared rulebook that lets AI apps talk to outside tools and data.
A big update to that rulebook lands on **2026-07-28**.
The update removes some patterns that older MCP servers rely on, so code written the old way can quietly stop working.
This tool reads your server's code and reports exactly what needs to change, in plain language, before that happens.

## Five-minute path

Requires Python 3.11 or newer.

```
git clone https://github.com/Softogram/softogram-mcp-spec-migration-checker.git
cd softogram-mcp-spec-migration-checker
pip install .
mcp-migration-check path/to/your/server
```

Leave off the path and it checks the current folder:

```
mcp-migration-check
```

## A real before/after

`examples/` in this repo has a small shopping-basket MCP server, written two ways.
`examples/before/` hand-rolls its own MCP-over-HTTP transport, bypassing the official SDK entirely - and both examples are validated against the real, installed `mcp` package (not just hand-written to look plausible; see `examples/README.md`).
Running the tool on it looks like this:

```
$ mcp-migration-check examples/before

mcp-migration-check: scanned 2 Python files under examples/before

server.py
  line 19  [THIS WILL BREAK]  (Confirmed)  R3 - Hand-rolled transport missing Mcp-Method / Mcp-Name
      > async def app(scope, receive, send):
      The 2026-07-28 update requires the Mcp-Method and Mcp-Name headers on every
      Streamable HTTP POST request. This only applies to hand-rolled MCP-over-HTTP
      transport code - servers using the official SDK's built-in Streamable HTTP
      transport get this handled for them. If you wrote your own transport wiring
      instead of using the SDK's, add both headers.
      Source: https://modelcontextprotocol.io/specification/draft/changelog (checked 2026-07-14)

  line 24  [THIS WILL BREAK]  (Confirmed)  R1 - Hand-rolled reading of the old session header
      > session_id = headers.get("mcp-session-id")
      ...

  ...

Summary: 5 will break, 2 worth checking, 0 needs manual check, 0 files skipped
```

`examples/after/` is the same server, migrated.
Running the tool on it gives a clean report:

```
$ mcp-migration-check examples/after

mcp-migration-check: scanned 2 Python files under examples/after

No migration findings found.

Summary: 0 will break, 0 worth checking, 0 needs manual check, 0 files skipped
```

See `examples/README.md` for exactly what changed between the two, and why - including a false positive the real-SDK check itself caught and fixed.

## How sure is the tool about each finding?

Not every claim about this spec update is equally solid.
Some come straight from the official changelog (very sure).
Others come from trusted sources describing the update more broadly, before the official page mentions them (less sure, but still worth knowing).
Every finding in the report is labeled with one of these two confidence tiers, so you can tell the difference yourself:

| Confidence | What it means | Shown in the report as |
|---|---|---|
| **Confirmed** | Listed on the [official MCP changelog](https://modelcontextprotocol.io/specification/draft/changelog) | "This will break" |
| **Reported** | Described by trusted secondary sources, not yet on the official page | "Worth checking" |

A separate, fourth thing a finding can say is **"we couldn't tell if this applies to you"** (`NEEDS-MANUAL-CHECK`).
This happens for R3 when your server's transport (web-reachable vs. local-only) is decided at runtime - something reading the code alone can never resolve.
It's not a severity and it never affects the exit code.
See `tests/fixtures/r3/cannot_tell_runtime_transport.py` for a worked example.

## The five rules

| ID | What it checks for | Severity | Confidence | Source | Last checked |
|---|---|---|---|---|---|
| R1 | Hand-rolled reading of the raw `Mcp-Session-Id` header by name (bypassing the SDK's own session handling) | This will break | Confirmed | [MCP changelog](https://modelcontextprotocol.io/specification/draft/changelog) | 2026-07-28 |
| R2 | Server memory keyed to a session instead of an explicit handle | This will break | Confirmed | [MCP changelog](https://modelcontextprotocol.io/specification/draft/changelog) | 2026-07-14 |
| R3 | Hand-rolled HTTP transport missing the two new required headers, `Mcp-Method` and `Mcp-Name` | This will break | Confirmed | [MCP changelog](https://modelcontextprotocol.io/specification/draft/changelog) | 2026-07-14 |
| R4 | Use of Roots, Sampling, or Logging (reported as being phased out) | Worth checking | Reported | [AAIF blog](https://aaif.io/blog/mcp-is-growing-up/) | 2026-07-14 |
| R5 | Hand-written MCP error numbers | Worth checking | Reported | [ChatForest builder's guide](https://chatforest.com/builders-log/mcp-spec-2026-07-28-release-candidate-stateless-breaking-changes-builder-guide/) | 2026-07-14 |

**A note on R3:** `Mcp-Method` and `Mcp-Name` are headers added at the transport layer (the part of the code that turns MCP messages into HTTP requests), not something most application code touches directly.
If your server uses the official MCP Python SDK's built-in Streamable HTTP transport, the SDK handles these headers for you automatically - there is nothing in your own code for this tool to flag, and R3 stays silent.
R3 only fires "This will break" on servers that hand-roll their own HTTP transport code instead of using the SDK's.
See `docs/low-level-design/003-r3-transport-detection.md` for the full reasoning.

**A note on R1:** reading `ctx.session_id` through the SDK's own `Context` object is a legitimate, still-supported convenience property in the real MCP Python SDK (confirmed by installing it directly) - it exposes the transport's connection id, not the removed protocol-level session handshake, so this tool does not flag it. R1 only fires on code that reads the raw `Mcp-Session-Id` header by its literal name, which only happens in code that bypasses the SDK's session handling entirely. See `docs/LEARNINGS.md`'s 2026-07-28 entry for how this was caught.

**Known unknowns - not checked in this version:** independent trackers mention MCP error numbers may change, but no source confirms which ones, so this tool never guesses a specific number.
It also does not check for the new task-handling, visual-interface, or stricter login/security features in the same update, since those are new additions rather than things that break existing code.
See `docs/PRD.md` section 4.2 for the full list of changes being tracked but not built into a rule yet.

## What this tool does NOT do

- It does not fix your code automatically. It only reports - a person decides what to change.
- It only understands Python code written against the official MCP Python SDK. Not TypeScript, not other SDKs.
- It only reads your code (static analysis). It never runs your server.
- It checks one spec update: the 2026-07-28 hop from the 2025-11-25 spec version. It assumes your server is already on 2025-11-25.
- It is a command-line tool, not a website or hosted service. No accounts, nothing sent anywhere.

## Rules are data

Every rule's metadata (its explanation, severity, confidence, and source link) lives in [`src/mcp_migration_check/rules/rules.toml`](src/mcp_migration_check/rules/rules.toml), separate from the code that finds it.
That means once the official spec fully publishes on July 28, updating a rule's claim is a plain-text data change, not a rewrite of the tool.
See `docs/high-level-design/001-scan-pipeline.md` for the full design.

## Development

```
pip install ".[dev]"
pytest                       # unit and fixture tests
ruff check .                 # lint
python scripts/e2e_check.py  # release gate: runs the CLI against examples/, diffs against snapshots
```

See `tests/README.md` for the per-rule fixture convention.
