# NOTES - Scope for Week 1 (Jul 13-19, 2026)

This file is the scope contract for the week.
If a task isn't on the "in" list, it waits.
Full detail and reasoning live in `docs/PRD.md`; this is the short version we check against daily.

## The problem, in one sentence

MCP servers written in Python against the current spec will quietly break when the 2026-07-28 spec update lands, and developers have no quick way to find out what in their code needs to change.

## The one command

```
mcp-migration-check <path-to-server-code>
```

Run it, read a plain-language report of what will break and what is worth checking, each finding labeled with how sure we are and linked to its source.
Exits with an error code if anything "will break" is found.

## In scope this week (the MVP)

- One CLI entry point, checks the current folder if no path is given.
- Five checks, read from a rule set kept as data separate from the engine:
  1. Old-style session usage - "This will break" (Confirmed).
  2. Server memory not using the new visible-handle style - "This will break" (Confirmed).
  3. Web-exposed servers missing the two new required request fields - "This will break" (Confirmed); skipped for local-only servers.
  4. Use of Roots / Sampling / Logging (being phased out) - "Worth checking" (Reported).
  5. Hand-written MCP error numbers - "Worth checking" (Reported).
- Report grouped by file, plain language, confidence label + source link per finding.
- Non-zero exit code when any "will break" finding exists.
- One real before/after example: a small old-style sample server, the tool's report on it, and the migrated version with a clean report.
- Tests per rule (one fixture that must match, one that must not) and a small end-to-end check tool that runs the CLI against the examples and compares the report to what we expect.
- README with install, usage, the before/after, and where every rule came from.
- Public GitHub repo, tagged v0.1.0, shipped this weekend.

## Cut line - explicitly out this week

- Auto-fixing code (report only).
- Any language other than Python / any SDK other than the official MCP Python SDK.
- `--json` and `--explain` flags (stretch - only if hours remain after the MVP list above).
- GitHub Actions integration for users, hosted anything, dashboards, accounts.
- Guessing unconfirmed details (like which exact error number changes).
- Checks for the new task-handling, visual-interface, or auth features (they don't break existing code).

## Working agreement

- Implementation: user (+ Cursor). Planning, issues, and PR review: Claude. See this folder's `CLAUDE.md`.
- Budget: ~10 hours hands-on. If the MVP list isn't finishable by hour 10, cut from the bottom of the "in scope" list, never past the before/after example - the proof it works ships no matter what.

## What actually happened (2026-07-28, ship day)

The plan above assumed a Jul 18-19 weekend build.
That weekend passed with all planning settled (PRD, HLD 001, both LLDs) and zero build hours spent - see `docs/LEARNINGS.md`, 2026-07-21 entry, "a deadline that slipped changes what the deadline is."

On 2026-07-28 (the day the actual spec update lands, and the last day this project's plan allows for), the user asked for the project to be completed end to end in one session.
This project's `CLAUDE.md` (Section 0) restricts Claude to planning, documentation, issue management, and PR review - never implementation.
That rule was suspended for this session only, with the user's explicit confirmation, to make the ship date; a dated note recording the suspension is in this folder's `CLAUDE.md`.
Every item in the "in scope" list above shipped, including the two design gates (R3 detectability and signal order) that were still open going into today - closed as `docs/low-level-design/003-r3-transport-detection.md` before implementation started.
The normal working agreement (user/Cursor implements, Claude plans and reviews) resumes after this session.
