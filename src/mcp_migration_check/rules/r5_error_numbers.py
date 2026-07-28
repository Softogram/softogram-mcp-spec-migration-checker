"""R5 - hand-written MCP (JSON-RPC) error numbers.

Matches integer literals in the JSON-RPC/MCP reserved error-code range
(-32768 to -32000) used in a comparison, a raise, or an assignment to a
code-ish name. Must not match HTTP statuses (404, 500) or positive
app-specific codes - those fall outside the reserved range entirely.
No specific number is named in the report text: no source confirms which
one changes (docs/PRD.md section 9).
"""

from __future__ import annotations

import ast

_MCP_ERROR_RANGE = range(-32768, -32000 + 1)


def _negative_int_value(node: ast.expr) -> int | None:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        operand = node.operand
        if isinstance(operand, ast.Constant) and isinstance(operand.value, int):
            return -operand.value
    if isinstance(node, ast.Constant) and isinstance(node.value, int) and node.value < 0:
        return node.value
    return None


def _is_mcp_error_code(node: ast.expr) -> bool:
    value = _negative_int_value(node)
    return value is not None and value in _MCP_ERROR_RANGE


def _target_name_suggests_code(target: ast.expr) -> bool:
    if isinstance(target, ast.Name):
        return "code" in target.id.lower()
    if isinstance(target, ast.Attribute):
        return "code" in target.attr.lower()
    return False


def match(file_path: str, tree: ast.AST, source_lines: list[str]) -> list[int]:
    del file_path, source_lines
    lines: set[int] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            candidates = [node.left, *node.comparators]
            if any(_is_mcp_error_code(c) for c in candidates):
                lines.add(node.lineno)
        elif isinstance(node, ast.Raise) and node.exc is not None:
            if any(_is_mcp_error_code(n) for n in ast.walk(node.exc)):
                lines.add(node.lineno)
        elif isinstance(node, ast.Assign):
            if _is_mcp_error_code(node.value) and any(
                _target_name_suggests_code(t) for t in node.targets
            ):
                lines.add(node.lineno)
        elif isinstance(node, ast.AnnAssign):
            has_value = node.value is not None
            is_code = has_value and _is_mcp_error_code(node.value)
            if is_code and _target_name_suggests_code(node.target):
                lines.add(node.lineno)

    return sorted(lines)
