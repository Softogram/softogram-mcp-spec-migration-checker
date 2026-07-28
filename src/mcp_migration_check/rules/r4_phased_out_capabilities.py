"""R4 - use of Roots / Sampling / Logging, reported as being phased out.

Matches SDK-specific surfaces only: the MCP SDK's own roots/sampling/logging
calls and capability declarations. Must not match plain Python stdlib
`logging` module usage (import logging, logger.info(...)) - that is the
single most important must-not fixture for this rule. See docs/PRD.md
sections 1, 4.1 and the AAIF source cited in rules.toml.
"""

from __future__ import annotations

import ast

_PHASED_OUT_CALL_NAMES = {
    "list_roots",
    "create_message",
    "set_logging_level",
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
