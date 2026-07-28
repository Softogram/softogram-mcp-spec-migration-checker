"""R1 - old-style session usage.

Matches code that reads or stores a session ID: attribute access to a
session id (ctx.session_id, request.session.id) or a header lookup for the
"Mcp-Session-Id" header by string literal. See docs/PRD.md sections 1, 8
and docs/high-level-design/001-scan-pipeline.md.

Boundary with R2 (docs/low-level-design, R1/R2 boundary note): a session-id
attribute access that is syntactically the key of a subscript, or an
argument to a container's get/setdefault/pop, belongs to R2 only - this
matcher skips those nodes so an ambiguous line fires exactly one rule.
"""

from __future__ import annotations

import ast

_SESSION_HEADER_NAME = "mcp-session-id"
_CONTAINER_KEY_METHODS = {"get", "setdefault", "pop"}


def _is_session_attribute(node: ast.Attribute) -> bool:
    attr = node.attr.lower()
    if attr.replace("_", "") == "sessionid":
        return True
    if attr == "id" and isinstance(node.value, ast.Attribute):
        return node.value.attr.lower() == "session"
    return False


def _is_session_header_literal(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.lower() == _SESSION_HEADER_NAME
    )


class _Visitor(ast.NodeVisitor):
    """Walks the tree once, collecting session-id and session-header lines.

    Attribute matches nested inside a subscript key or a container
    get/setdefault/pop argument are skipped - those belong to R2.
    """

    def __init__(self) -> None:
        self.lines: set[int] = set()
        self._skip_ids: set[int] = set()

    def _mark_skip(self, node: ast.AST) -> None:
        for child in ast.walk(node):
            self._skip_ids.add(id(child))

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if _is_session_header_literal(node.slice):
            self.lines.add(node.lineno)
        self._mark_skip(node.slice)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr in _CONTAINER_KEY_METHODS:
            for arg in node.args:
                if _is_session_header_literal(arg):
                    self.lines.add(node.lineno)
                self._mark_skip(arg)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if id(node) not in self._skip_ids and _is_session_attribute(node):
            self.lines.add(node.lineno)
        self.generic_visit(node)


def match(file_path: str, tree: ast.AST, source_lines: list[str]) -> list[int]:
    del file_path, source_lines
    visitor = _Visitor()
    visitor.visit(tree)
    return sorted(visitor.lines)
