"""R6 - opting into SSE stream resumability via event_store.

The 2026-07-28 update removes SSE stream resumability and message
redelivery (the Last-Event-ID header and SSE event IDs) from the
Streamable HTTP transport entirely (SEP-2575). A broken response stream
now loses the in-flight request; clients must re-issue it as a new
request with a new request ID.

Checked against the real installed SDK: the pre-update FastMCP/Server
constructors accept an `event_store` keyword argument specifically to
enable resumability (an EventStore implementing `replay_events_after`);
the post-update SDK's server constructor no longer accepts it at all.
Passing a non-None `event_store` is a genuine, low-false-positive
app-code signal that a server opted into a mechanism the new spec
removes outright. See docs/LEARNINGS.md's 2026-07-28 entry.
"""

from __future__ import annotations

import ast


def _is_non_none(node: ast.expr) -> bool:
    return not (isinstance(node, ast.Constant) and node.value is None)


def match(file_path: str, tree: ast.AST, source_lines: list[str]) -> list[int]:
    del file_path, source_lines
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg == "event_store" and _is_non_none(keyword.value):
                lines.add(node.lineno)
    return sorted(lines)
