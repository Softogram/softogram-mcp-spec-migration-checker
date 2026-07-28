"""R8 - old-style logging/setLevel request handler registration.

The 2026-07-28 update removes the ping, logging/setLevel, and
notifications/roots/list_changed requests outright (SEP-2575). Log
level is now set per-request via a _meta key instead.

This rule covers only the logging/setLevel piece: checked against the
real installed SDK, the pre-update low-level Server class exposes
`set_logging_level()` as a decorator-factory method for registering the
handler for that exact request (`@server.set_logging_level()`); it does
not exist at all on the post-update SDK's low-level Server. `ping` and
notifications/roots/list_changed were investigated too, but neither has
an equivalent app-code-visible registration point in the pre-update
SDK's public surface (ping is handled internally with a built-in
default; roots/list_changed has no dedicated handler-registration
method) - so, per this project's rule of not guessing at undetectable
patterns, only the logging/setLevel piece became a rule. See
docs/LEARNINGS.md's 2026-07-28 entry.

Distinct from R4: R4 is about *consuming* the deprecated Logging
capability (Confirmed/worth-checking, 12-month grace period); this rule
is about a server *implementing the specific removed RPC handler*
(Confirmed/will-break, no grace period - the request itself is gone).
"""

from __future__ import annotations

import ast


def _call_target_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return None


def match(file_path: str, tree: ast.AST, source_lines: list[str]) -> list[int]:
    del file_path, source_lines
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_target_name(node) == "set_logging_level":
            lines.add(node.lineno)
    return sorted(lines)
