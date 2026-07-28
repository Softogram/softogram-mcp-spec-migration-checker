"""Renders a ScanResult as the plain-text report.

See docs/low-level-design/002-finding-model-report-and-exit-codes.md
sections 1-4 for the layout and determinism contract this implements.
Plain text only: no color, no timestamps, no version string, no absolute
paths - what keeps the E2E snapshot stable across machines and runs.
"""

from __future__ import annotations

import json
import textwrap
from collections import defaultdict

from mcp_migration_check.models import SEVERITY_WILL_BREAK, Rule, ScanResult

_SEVERITY_LABELS = {
    SEVERITY_WILL_BREAK: "THIS WILL BREAK",
    "worth-checking": "Worth checking",
}
_SEVERITY_PROSE = {
    SEVERITY_WILL_BREAK: "This will break",
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


def render_json(result: ScanResult, scanned_path_display: str) -> str:
    """Render a ScanResult as machine-readable JSON.

    Same content and determinism guarantees as render_report (stable
    ordering, no absolute paths, no timestamps) - just a different
    shape, for CI wrappers and editors to consume. See issue #18.
    """
    findings = sorted(result.findings, key=lambda f: (f.file, f.line, f.rule_id))
    findings_json = [
        {
            "rule_id": f.rule_id,
            "title": f.title,
            "file": f.file,
            "line": f.line,
            "matched_text": f.matched_text,
            "severity": f.severity,
            "confidence": f.confidence,
            "explanation": f.explanation,
            "source_url": f.source_url,
            "source_checked": f.source_checked,
        }
        for f in findings
    ]

    checks_by_rule: dict[str, list] = defaultdict(list)
    for check in result.manual_checks:
        checks_by_rule[check.rule_id].append(check)
    manual_checks_json = [
        {
            "rule_id": rule_id,
            "title": checks_by_rule[rule_id][0].title,
            "files": sorted({c.file for c in checks_by_rule[rule_id]}),
            "manual_check_text": checks_by_rule[rule_id][0].manual_check_text,
            "source_url": checks_by_rule[rule_id][0].source_url,
            "source_checked": checks_by_rule[rule_id][0].source_checked,
        }
        for rule_id in sorted(checks_by_rule)
    ]

    skipped_files_json = [
        {"file": s.file, "reason": s.reason}
        for s in sorted(result.skipped_files, key=lambda s: s.file)
    ]

    payload = {
        "scanned_path": scanned_path_display,
        "files_scanned": result.files_scanned,
        "findings": findings_json,
        "manual_checks": manual_checks_json,
        "skipped_files": skipped_files_json,
        "summary": {
            "will_break": result.will_break_count,
            "worth_checking": result.worth_checking_count,
            "needs_manual_check": len(result.manual_checks),
            "files_skipped": len(result.skipped_files),
        },
    }
    return json.dumps(payload, indent=2) + "\n"


def render_explain(rule: Rule) -> str:
    """Render one rule's full story, straight from its metadata. See issue #19."""
    severity_label = _SEVERITY_PROSE[rule.severity]
    confidence_label = _CONFIDENCE_LABELS[rule.confidence]

    lines = [
        f"{rule.id} - {rule.title}",
        "",
        f"Severity: {severity_label}",
        f"Confidence: {confidence_label}",
        "",
    ]
    lines.extend(_wrap(rule.explanation))
    lines.append("")

    if rule.manual_check_text:
        lines.append("If the tool can't tell whether this applies to you, it says:")
        lines.extend(_wrap(rule.manual_check_text))
        lines.append("")

    lines.append(f"Source: {rule.source_url} (checked {rule.source_checked})")

    return "\n".join(lines) + "\n"
