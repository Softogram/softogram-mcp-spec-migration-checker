"""R2 - session-keyed server memory instead of visible handles.

Matches state kept between requests keyed by a session identity - a
container subscripted or looked up by something session-shaped - instead
of an explicit handle the client passes back. See docs/PRD.md sections 1,
8 and docs/high-level-design/001-scan-pipeline.md.

Complements R1 (r1_session_usage.py): R1 is reading/storing the session id
itself, R2 is remembering things by it. A handle-keyed access
(BASKETS[basket_handle]) must not match - that is the new, correct
pattern.
"""

from __future__ import annotations

import ast

_CONTAINER_KEY_METHODS = {"get", "setdefault", "pop"}


def _is_session_key(node: ast.expr) -> bool:
    if isinstance(node, ast.Name):
        return "session" in node.id.lower()
    if isinstance(node, ast.Attribute):
        attr = node.attr.lower()
        if attr.replace("_", "") == "sessionid":
            return True
        if attr == "id" and isinstance(node.value, ast.Attribute):
            return node.value.attr.lower() == "session"
        return "session" in attr
    return False


class _Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.lines: set[int] = set()

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if _is_session_key(node.slice):
            self.lines.add(node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr in _CONTAINER_KEY_METHODS:
            if node.args and _is_session_key(node.args[0]):
                self.lines.add(node.lineno)
        self.generic_visit(node)


def match(file_path: str, tree: ast.AST, source_lines: list[str]) -> list[int]:
    del file_path, source_lines
    visitor = _Visitor()
    visitor.visit(tree)
    return sorted(visitor.lines)
