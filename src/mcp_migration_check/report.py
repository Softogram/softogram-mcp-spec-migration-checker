"""Renders a ScanResult as the plain-text report.

See docs/low-level-design/002-finding-model-report-and-exit-codes.md
sections 1-4 for the layout and determinism contract this implements.
Plain text only: no color, no timestamps, no version string, no absolute
paths - what keeps the E2E snapshot stable across machines and runs.
"""

from __future__ import annotations

import textwrap
from collections import defaultdict

from mcp_migration_check.models import SEVERITY_WILL_BREAK, ScanResult

_SEVERITY_LABELS = {
    SEVERITY_WILL_BREAK: "THIS WILL BREAK",
    "worth-checking": "Worth checking",
}
_CONFIDENCE_LABELS = {
    "confirmed": "Confirmed",
    "reported": "Reported",
}
_EXPLANATION_WIDTH = 76
_INDENT = "      "


def _wrap(text: str) -> list[str]:
    return textwrap.wrap(text, width=_EXPLANATION_WIDTH) or [text]


def render_report(result: ScanResult, scanned_path_display: str) -> str:
    lines: list[str] = []
    lines.append(
        f"mcp-migration-check: scanned {result.files_scanned} Python files "
        f"under {scanned_path_display}"
    )
    lines.append("")

    files_with_findings = sorted({f.file for f in result.findings})
    if not files_with_findings and not result.manual_checks:
        lines.append("No migration findings found.")
        lines.append("")

    findings_by_file: dict[str, list] = defaultdict(list)
    for finding in result.findings:
        findings_by_file[finding.file].append(finding)

    for file in files_with_findings:
        lines.append(file)
        file_findings = sorted(findings_by_file[file], key=lambda f: (f.line, f.rule_id))
        for finding in file_findings:
            severity_label = _SEVERITY_LABELS[finding.severity]
            confidence_label = _CONFIDENCE_LABELS[finding.confidence]
            lines.append(
                f"  line {finding.line}  [{severity_label}]  ({confidence_label})  "
                f"{finding.rule_id} - {finding.title}"
            )
            lines.append(f"{_INDENT}> {finding.matched_text}")
            for wrapped_line in _wrap(finding.explanation):
                lines.append(f"{_INDENT}{wrapped_line}")
            lines.append(
                f"{_INDENT}Source: {finding.source_url} (checked {finding.source_checked})"
            )
            lines.append("")

    if result.manual_checks:
        lines.append(
            "NEEDS MANUAL CHECK - the tool could not tell whether these rules apply to you"
        )
        checks_by_rule: dict[str, list] = defaultdict(list)
        for check in result.manual_checks:
            checks_by_rule[check.rule_id].append(check)
        for rule_id in sorted(checks_by_rule):
            checks = checks_by_rule[rule_id]
            first = checks[0]
            lines.append(f"  {rule_id} - {first.title}")
            for wrapped_line in _wrap(first.manual_check_text):
                lines.append(f"{_INDENT}{wrapped_line}")
            affected_files = ", ".join(sorted({c.file for c in checks}))
            lines.append(f"{_INDENT}Files: {affected_files}")
            lines.append(f"{_INDENT}Source: {first.source_url} (checked {first.source_checked})")
            lines.append("")

    if result.skipped_files:
        lines.append("SKIPPED FILES - could not be parsed")
        for skipped in sorted(result.skipped_files, key=lambda s: s.file):
            lines.append(f"  {skipped.file}: {skipped.reason}")
        lines.append("")

    lines.append(
        f"Summary: {result.will_break_count} will break, "
        f"{result.worth_checking_count} worth checking, "
        f"{len(result.manual_checks)} needs manual check, "
        f"{len(result.skipped_files)} files skipped"
    )

    return "\n".join(lines) + "\n"
