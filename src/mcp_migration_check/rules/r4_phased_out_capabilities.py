"""R4 - use of Roots / Sampling / Logging, deprecated as of 2026-07-28.

Matches SDK-specific surfaces only: the MCP SDK's own roots/sampling/logging
calls and capability declarations. Must not match plain Python stdlib
`logging` module usage (import logging, logger.info(...)) - that is the
single most important must-not fixture for this rule. See docs/PRD.md
sections 1, 4.1 and rules.toml (now Confirmed via the official 2026-07-28
changelog, SEP-2577).

`set_logging_level` was removed from this rule's match set on 2026-07-28:
checking against the real installed SDK showed it is never a method on
`ServerSession` (the client-facing session app code consumes via
`ctx.session`) - it only exists as the low-level `Server`'s decorator for
*registering the incoming request handler*, a server-implementation
concern that belongs to R8 (the removed logging/setLevel RPC), not to
this rule's "consuming a deprecated capability" theme. See
docs/LEARNINGS.md's 2026-07-28 entry.
"""

from __future__ import annotations

import ast

_PHASED_OUT_CALL_NAMES = {
    "list_roots",
    "create_message",
    "send_log_message",
}
_PHASED_OUT_CAPABILITY_NAMES = {
    "RootsCapability",
    "SamplingCapability",
    "LoggingCapability",
}


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
        if isinstance(node, ast.Call):
            name = _call_target_name(node)
            if name in _PHASED_OUT_CALL_NAMES or name in _PHASED_OUT_CAPABILITY_NAMES:
                lines.add(node.lineno)
    return sorted(lines)
