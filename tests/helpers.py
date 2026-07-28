"""Shared assertion helper for per-rule fixture tests.

See tests/README.md for the fixture convention this supports: one
match_*.py and one no_match_*.py fixture per rule, asserting exactly which
(rule, line) pairs a matcher yields for a given fixture file.
"""

from __future__ import annotations

import ast
from pathlib import Path

from mcp_migration_check.models import NeedsManualCheck
from mcp_migration_check.rules import REGISTRY

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def run_matcher(rule_id: str, fixture_path: Path) -> list[int] | NeedsManualCheck:
    """Run one rule's matcher against one fixture file and return its raw answer."""
    source = fixture_path.read_text()
    tree = ast.parse(source, filename=str(fixture_path))
    source_lines = source.splitlines()
    return REGISTRY[rule_id](str(fixture_path), tree, source_lines)
