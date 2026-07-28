"""The scan engine: parses files, runs matchers, assembles findings.

See docs/high-level-design/001-scan-pipeline.md stages 3-5 and
docs/low-level-design/001-rule-definition-format.md section 3-4 for the
matcher contract this implements. The engine holds zero rule-specific
knowledge - adding or removing a rule never touches this file.
"""

from __future__ import annotations

import ast
from pathlib import Path

from mcp_migration_check.discovery import discover_python_files
from mcp_migration_check.models import (
    NEEDS_MANUAL_CHECK,
    Finding,
    ManualCheckResult,
    Rule,
    ScanResult,
    SkippedFile,
)
from mcp_migration_check.ruleset import RuleSetError, cross_check_registry, load_rules

_RULES_TOML = Path(__file__).parent / "rules" / "rules.toml"


def _relative_posix(path: Path, root: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    return rel.as_posix()


def _load_ruleset_and_registry() -> tuple[dict[str, Rule], dict[str, object]]:
    from mcp_migration_check.rules import REGISTRY

    rules = load_rules(_RULES_TOML)
    cross_check_registry(rules, REGISTRY)
    return rules, REGISTRY


def run_scan(root: Path) -> ScanResult:
    """Scan every Python file under root and return the assembled ScanResult."""
    rules, registry = _load_ruleset_and_registry()

    py_files = sorted(discover_python_files(root))
    findings: list[Finding] = []
    manual_checks: list[ManualCheckResult] = []
    skipped: list[SkippedFile] = []
    files_scanned = 0

    for file_path in py_files:
        rel_path = _relative_posix(file_path, root)
        try:
            source = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            skipped.append(SkippedFile(file=rel_path, reason=f"could not read file: {exc}"))
            continue

        try:
            tree = ast.parse(source, filename=rel_path)
        except SyntaxError as exc:
            skipped.append(SkippedFile(file=rel_path, reason=f"could not parse file: {exc}"))
            continue

        files_scanned += 1
        source_lines = source.splitlines()

        for rule_id, matcher in registry.items():
            rule = rules[rule_id]
            result = matcher(rel_path, tree, source_lines)

            if result is NEEDS_MANUAL_CHECK:
                if not rule.manual_check_text:
                    raise RuleSetError(
                        f"rule {rule_id!r} returned NEEDS-MANUAL-CHECK but has no "
                        "manual_check_text in rules.toml"
                    )
                manual_checks.append(
                    ManualCheckResult(
                        file=rel_path,
                        rule_id=rule.id,
                        title=rule.title,
                        manual_check_text=rule.manual_check_text,
                        source_url=rule.source_url,
                        source_checked=rule.source_checked,
                    )
                )
                continue

            for line_number in result:
                matched_text = ""
                if 1 <= line_number <= len(source_lines):
                    matched_text = source_lines[line_number - 1].strip()
                findings.append(
                    Finding(
                        file=rel_path,
                        line=line_number,
                        matched_text=matched_text,
                        rule_id=rule.id,
                        title=rule.title,
                        severity=rule.severity,
                        confidence=rule.confidence,
                        explanation=rule.explanation,
                        source_url=rule.source_url,
                        source_checked=rule.source_checked,
                    )
                )

    return ScanResult(
        scanned_root=str(root),
        files_scanned=files_scanned,
        findings=findings,
        manual_checks=manual_checks,
        skipped_files=skipped,
    )
