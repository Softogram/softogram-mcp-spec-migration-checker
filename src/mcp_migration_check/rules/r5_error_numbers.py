"""R5 - hand-written use of a specific MCP error number that got renumbered.

Narrowed 2026-07-28 after the final (non-draft) changelog published its
error-code allocation policy: -32000 to -32019 is explicitly
"implementation-defined... existing SDK usage is grandfathered" (safe,
not flagged), -32020 to -32099 is newly reserved for MCP, and exactly
four pre-existing codes were renumbered into that new range:

    -32001 (HeaderMismatch)                -> -32020
    -32002 (resource not found)            -> -32602 (Invalid Params)
    -32003 (MissingRequiredClientCapability) -> -32021
    -32004 (UnsupportedProtocolVersion)    -> -32022

Code that hardcodes one of these four *old* numbers - in a comparison,
a raise, or an assignment to a code-ish name - will silently stop
matching the real error once a client/server upgrades, since the wire
value changes. This is now Confirmed/will-break, not a guess: the
previous version of this rule flagged the whole -32768..-32000 range as
"worth checking" without naming a number, since nothing was confirmed
yet (docs/PRD.md section 9). No other number in that range is
confirmed changing, so nothing else is flagged - guessing would be
worse than not checking.
"""

from __future__ import annotations

import ast

_RENUMBERED_CODES = {-32001, -32002, -32003, -32004}


def _renumbered_code_value(node: ast.expr) -> int | None:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        operand = node.operand
        if isinstance(operand, ast.Constant) and isinstance(operand.value, int):
            value = -operand.value
            return value if value in _RENUMBERED_CODES else None
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value if node.value in _RENUMBERED_CODES else None
    return None


def _is_renumbered_code(node: ast.expr) -> bool:
    return _renumbered_code_value(node) is not None


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
            if any(_is_renumbered_code(c) for c in candidates):
                lines.add(node.lineno)
        elif isinstance(node, ast.Raise) and node.exc is not None:
            if any(_is_renumbered_code(n) for n in ast.walk(node.exc)):
                lines.add(node.lineno)
        elif isinstance(node, ast.Assign):
            if _is_renumbered_code(node.value) and any(
                _target_name_suggests_code(t) for t in node.targets
            ):
                lines.add(node.lineno)
        elif isinstance(node, ast.AnnAssign):
            has_value = node.value is not None
            is_code = has_value and _is_renumbered_code(node.value)
            if is_code and _target_name_suggests_code(node.target):
                lines.add(node.lineno)

    return sorted(lines)
