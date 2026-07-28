"""Data shapes shared across the scan pipeline.

See docs/low-level-design/001-rule-definition-format.md and
docs/low-level-design/002-finding-model-report-and-exit-codes.md for the
contracts these classes implement.
"""

from __future__ import annotations

from dataclasses import dataclass

SEVERITY_WILL_BREAK = "will-break"
SEVERITY_WORTH_CHECKING = "worth-checking"
ALLOWED_SEVERITIES = (SEVERITY_WILL_BREAK, SEVERITY_WORTH_CHECKING)

CONFIDENCE_CONFIRMED = "confirmed"
CONFIDENCE_REPORTED = "reported"
ALLOWED_CONFIDENCES = (CONFIDENCE_CONFIRMED, CONFIDENCE_REPORTED)


class NeedsManualCheck:
    """The cannot-tell marker a matcher returns instead of a list of line numbers.

    A single shared instance is enough - it carries no per-call data, the
    file and rule it applies to are already known to whoever received it.
    """


NEEDS_MANUAL_CHECK = NeedsManualCheck()


@dataclass(frozen=True)
class Rule:
    """One rule's metadata, loaded as-is from rules.toml. Never edited at runtime."""

    id: str
    title: str
    severity: str
    confidence: str
    explanation: str
    source_url: str
    source_checked: str
    manual_check_text: str | None = None


@dataclass(frozen=True)
class Finding:
    """One concrete hit: a rule fired on one line of one file."""

    file: str
    line: int
    matched_text: str
    rule_id: str
    title: str
    severity: str
    confidence: str
    explanation: str
    source_url: str
    source_checked: str


@dataclass(frozen=True)
class ManualCheckResult:
    """A rule's cannot-tell outcome for one file. No line, no matched text."""

    file: str
    rule_id: str
    title: str
    manual_check_text: str
    source_url: str
    source_checked: str


@dataclass(frozen=True)
class SkippedFile:
    """A file the scan could not read as Python source."""

    file: str
    reason: str


@dataclass
class ScanResult:
    """Everything the reporter needs, already assembled by the engine."""

    scanned_root: str
    files_scanned: int
    findings: list[Finding]
    manual_checks: list[ManualCheckResult]
    skipped_files: list[SkippedFile]

    @property
    def will_break_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SEVERITY_WILL_BREAK)

    @property
    def worth_checking_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SEVERITY_WORTH_CHECKING)
