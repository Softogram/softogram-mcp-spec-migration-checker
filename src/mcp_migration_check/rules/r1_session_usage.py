"""R1 - hand-rolled reading of the old session header.

Matches code that reads the "Mcp-Session-Id" header directly by string
literal (headers.get("Mcp-Session-Id"), headers["mcp-session-id"]). See
docs/PRD.md sections 1, 8 and docs/high-level-design/001-scan-pipeline.md.

Narrowed 2026-07-28 after checking against the real MCP Python SDK
(installed `mcp` package, both the pre-update and post-update releases):
the SDK's own `Context.session_id` is a legitimate, still-supported
convenience property in the new SDK (it exposes the transport's
connection id, not the removed protocol-level session handshake), so
matching bare `ctx.session_id`-style attribute access would flag correct,
migrated code. The header is not exposed to application code by either
SDK version at all - genuinely reading it by literal name only happens
in code that bypasses the SDK's transport/session handling entirely,
which is the real "will break" signal. See
docs/low-level-design/003-r3-transport-detection.md for the related R3
narrowing, and docs/LEARNINGS.md's 2026-07-28 entry for the full story.
"""

from __future__ import annotations

import ast

_SESSION_HEADER_NAME = "mcp-session-id"
_CONTAINER_KEY_METHODS = {"get", "setdefault", "pop"}


def _is_session_header_literal(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.lower() == _SESSION_HEADER_NAME
    )


class _Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.lines: set[int] = set()

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if _is_session_header_literal(node.slice):
            self.lines.add(node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr in _CONTAINER_KEY_METHODS:
            for arg in node.args:
                if _is_session_header_literal(arg):
                    self.lines.add(node.lineno)
        self.generic_visit(node)


def match(file_path: str, tree: ast.AST, source_lines: list[str]) -> list[int]:
    del file_path, source_lines
    visitor = _Visitor()
    visitor.visit(tree)
    return sorted(visitor.lines)
