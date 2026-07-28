"""R7 - old-style resources/subscribe and resources/unsubscribe handlers.

The 2026-07-28 update replaces the HTTP GET endpoint and
resources/subscribe / resources/unsubscribe with a single
subscriptions/listen long-lived stream (SEP-2575).

Checked against the real installed SDK: the pre-update low-level
Server class exposes `subscribe_resource()` and `unsubscribe_resource()`
as decorator-factory methods for registering these exact request
handlers (`@server.subscribe_resource()`); the post-update SDK's
low-level Server has no such methods at all - handler registration moved
to a generic add_request_handler()/constructor-callback style entirely.
A server still decorating a function with either of the old names is
registering a handler for a request type the new spec no longer has.
See docs/LEARNINGS.md's 2026-07-28 entry.
"""

from __future__ import annotations

import ast

_OLD_HANDLER_NAMES = {"subscribe_resource", "unsubscribe_resource"}


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
        if isinstance(node, ast.Call) and _call_target_name(node) in _OLD_HANDLER_NAMES:
            lines.add(node.lineno)
    return sorted(lines)
