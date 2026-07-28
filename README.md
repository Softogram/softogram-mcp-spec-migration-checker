# mcp-migration-check

A small command-line tool that reads your Python MCP server's code and tells you what will break under the 2026-07-28 MCP spec update.
It never runs your code.
It only reads it (this is called static analysis).

## What's the problem?

MCP (Model Context Protocol) is a shared rulebook that lets AI apps talk to outside tools and data.
A big update to that rulebook lands on **2026-07-28**.
The update removes some patterns that older MCP servers rely on, so code written the old way can quietly stop working.
This tool reads your server's code and reports exactly what needs to change, in plain language, before that happens.

## Download and run - no Python required

Grab the file for your platform from the [latest release](https://github.com/Softogram/softogram-mcp-spec-migration-checker/releases/latest), make it executable, and run it:

```
chmod +x mcp-migration-check-*
./mcp-migration-check-* path/to/your/server
```

This is a single, standalone file (built by [PyInstaller](https://pyinstaller.org/)) - no Python install, no `pip install`, no cloning this repo. Leave off the path and it checks the current folder.

macOS and Windows may show a first-run warning since the binary isn't code-signed (normal for a small open-source tool) - right-click and choose "Open" on macOS, or click "More info -> Run anyway" on Windows, to bypass it once.

## Or install with pip, if you already have Python

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

## Other options

**`--json`** - prints the same findings as machine-readable JSON instead of the human report, for CI wrappers or editor integrations to consume. Same exit-code contract as the human report.

```
mcp-migration-check --json path/to/your/server
```

**`--explain <rule-id>`** - prints one rule's full story (what it checks, why, how sure we are, and its source) straight from the rule metadata, without scanning anything.

```
$ mcp-migration-check --explain R1

R1 - Hand-rolled reading of the old session header

Severity: This will break
Confidence: Confirmed

The 2026-07-28 update removes protocol-level sessions and the Mcp-Session-Id
header from the Streamable HTTP transport (SEP-2567). ...

Source: https://modelcontextprotocol.io/specification/2026-07-28/changelog.md (checked 2026-07-28)
```

An unknown rule id exits 2 and lists the known ones.

## A real before/after

`examples/` in this repo has a small shopping-basket MCP server, written two ways.
`examples/before/` hand-rolls its own MCP-over-HTTP transport, bypassing the official SDK entirely - and both examples are validated against the real, installed `mcp` package (not just hand-written to look plausible; see `examples/README.md`).
Running the tool on it looks like this:

```
$ mcp-migration-check examples/before

mcp-migration-check: scanned 3 Python files under examples/before

server.py
  line 19  [THIS WILL BREAK]  (Confirmed)  R3 - Hand-rolled transport missing Mcp-Method / Mcp-Name
      > async def app(scope, receive, send):
      The 2026-07-28 update requires the Mcp-Method and Mcp-Name headers on every
      Streamable HTTP POST request (SEP-2243). This only applies to hand-rolled
      MCP-over-HTTP transport code - servers using the official SDK's built-in
      Streamable HTTP transport get this handled for them. If you wrote your own
      transport wiring instead of using the SDK's, add both headers.
      Source: https://modelcontextprotocol.io/specification/2026-07-28/changelog.md (checked 2026-07-28)

  line 24  [THIS WILL BREAK]  (Confirmed)  R1 - Hand-rolled reading of the old session header
      > session_id = headers.get("mcp-session-id")
      ...

  ...

tools/legacy_handlers.py
  line 28  [THIS WILL BREAK]  (Confirmed)  R6 - SSE resumability opt-in (event_store)
      ...

  ...

Summary: 10 will break, 1 worth checking, 0 needs manual check, 0 files skipped
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
| **Confirmed** | Listed on the [official MCP changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog.md) | "This will break" |
| **Reported** | Described by trusted secondary sources, not yet on the official page | "Worth checking" |

The spec's final text published on 2026-07-28, so every rule below is now Confirmed - every claim traces to the official changelog itself, not a secondhand source.

A separate, fourth thing a finding can say is **"we couldn't tell if this applies to you"** (`NEEDS-MANUAL-CHECK`).
This happens for R3 when your server's transport (web-reachable vs. local-only) is decided at runtime - something reading the code alone can never resolve.
It's not a severity and it never affects the exit code.
See `tests/fixtures/r3/cannot_tell_runtime_transport.py` for a worked example.

## The eight rules

| ID | What it checks for | Severity | Confidence |
|---|---|---|---|
| R1 | Hand-rolled reading of the raw `Mcp-Session-Id` header by name (bypassing the SDK's own session handling) | This will break | Confirmed |
| R2 | Server memory keyed to a session instead of an explicit handle | This will break | Confirmed |
| R3 | Hand-rolled HTTP transport missing the two new required headers, `Mcp-Method` and `Mcp-Name` | This will break | Confirmed |
| R4 | Use of Roots, Sampling, or Logging (deprecated, twelve-month grace period) | Worth checking | Confirmed |
| R5 | Hand-written use of one of the four MCP error codes the spec renumbered | This will break | Confirmed |
| R6 | Opting into SSE stream resumability via `event_store` (removed entirely) | This will break | Confirmed |
| R7 | Old-style `resources/subscribe` or `resources/unsubscribe` request handler | This will break | Confirmed |
| R8 | Old-style `logging/setLevel` request handler | This will break | Confirmed |

Source for every rule: the [official MCP changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog.md), last checked 2026-07-28. See `src/mcp_migration_check/rules/rules.toml` for each rule's exact SEP citation and full explanation.

**A note on R3:** `Mcp-Method` and `Mcp-Name` are headers added at the transport layer (the part of the code that turns MCP messages into HTTP requests), not something most application code touches directly.
If your server uses the official MCP Python SDK's built-in Streamable HTTP transport, the SDK handles these headers for you automatically - there is nothing in your own code for this tool to flag, and R3 stays silent.
R3 only fires "This will break" on servers that hand-roll their own HTTP transport code instead of using the SDK's.
See `docs/low-level-design/003-r3-transport-detection.md` for the full reasoning.

**A note on R1:** reading `ctx.session_id` through the SDK's own `Context` object is a legitimate, still-supported convenience property in the real MCP Python SDK (confirmed by installing it directly) - it exposes the transport's connection id, not the removed protocol-level session handshake, so this tool does not flag it. R1 only fires on code that reads the raw `Mcp-Session-Id` header by its literal name, which only happens in code that bypasses the SDK's session handling entirely. See `docs/LEARNINGS.md`'s 2026-07-28 entries for how this was caught, and for R6/R7/R8's own real-SDK verification.

**A note on R4 vs. R8:** both involve "logging," but they're different facts. R4 is about *consuming* the deprecated Logging capability from a tool (twelve-month grace period, still works). R8 is about a server *implementing the specific removed `logging/setLevel` request handler* itself (no grace period - the request is gone). Checking the real SDK showed `set_logging_level` is never a method on the client-facing session object app code uses - only a low-level `Server` decorator for registering that handler - so it was moved out of R4 entirely into R8.

**Known unknowns - not checked in this version:** two backlog rule candidates (the removed `initialize`/`notifications/initialized` handshake, and the new required `server/discover` RPC) were investigated against the real SDK and found to have no clean, low-false-positive signal in application code - both are handled internally by the SDK for any server using it, with no public hook a developer would write custom code against. Flagging their absence would mean guessing. See `docs/LEARNINGS.md` for the investigation.
This tool also does not check for the new task-handling, visual-interface, or stricter login/security features in the same update, since those are new additions rather than things that break existing code.
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

## Building the standalone executable

The downloadable, no-Python-required file above is built with [PyInstaller](https://pyinstaller.org/) from `mcp-migration-check.spec`.
`.github/workflows/release.yml` builds one for each of macOS, Linux, and Windows and attaches them to the GitHub Release whenever a `v*` tag is pushed.
To build one yourself:

```
pip install ".[build]"
pyinstaller mcp-migration-check.spec
./dist/mcp-migration-check path/to/your/server
```

See `tests/README.md` for the per-rule fixture convention.
