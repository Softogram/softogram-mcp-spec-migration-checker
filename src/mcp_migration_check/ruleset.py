"""Loads rules.toml and cross-checks it against the matcher registry.

See docs/low-level-design/001-rule-definition-format.md sections 1-3.
Failing fast here is what makes the rules file trustworthy: a typo in the
data can never silently become a wrong label in a report.
"""

from __future__ import annotations

import tomllib
from datetime import date
from pathlib import Path

from mcp_migration_check.models import ALLOWED_CONFIDENCES, ALLOWED_SEVERITIES, Rule

_REQUIRED_FIELDS = (
    "title",
    "severity",
    "confidence",
    "explanation",
    "source_url",
    "source_checked",
)


class RuleSetError(Exception):
    """Raised when rules.toml or the matcher registry is invalid. Stops the program."""


def _validate_date(rule_id: str, value: object) -> str:
    if not isinstance(value, str):
        raise RuleSetError(f"rule {rule_id!r}: source_checked must be a YYYY-MM-DD string")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise RuleSetError(
            f"rule {rule_id!r}: source_checked {value!r} is not a valid date"
        ) from exc
    return value


def _build_rule(rule_id: str, fields: dict) -> Rule:
    missing = [name for name in _REQUIRED_FIELDS if name not in fields]
    if missing:
        raise RuleSetError(f"rule {rule_id!r} is missing required field(s): {', '.join(missing)}")

    severity = fields["severity"]
    if severity not in ALLOWED_SEVERITIES:
        raise RuleSetError(
            f"rule {rule_id!r}: severity {severity!r} is not one of {ALLOWED_SEVERITIES}"
        )

    confidence = fields["confidence"]
    if confidence not in ALLOWED_CONFIDENCES:
        raise RuleSetError(
            f"rule {rule_id!r}: confidence {confidence!r} is not one of {ALLOWED_CONFIDENCES}"
        )

    _validate_date(rule_id, fields["source_checked"])

    return Rule(
        id=rule_id,
        title=fields["title"],
        severity=severity,
        confidence=confidence,
        explanation=fields["explanation"],
        source_url=fields["source_url"],
        source_checked=fields["source_checked"],
        manual_check_text=fields.get("manual_check_text"),
    )


def load_rules(rules_toml_path: Path) -> dict[str, Rule]:
    """Parse rules.toml into a dict of rule id -> Rule, or raise RuleSetError."""
    with rules_toml_path.open("rb") as fh:
        raw = tomllib.load(fh)

    rules: dict[str, Rule] = {}
    seen_ids: set[str] = set()
    for section_name, fields in raw.items():
        if not isinstance(fields, dict):
            raise RuleSetError(f"rules.toml: top-level key {section_name!r} must be a table")
        rule_id = fields.get("id", section_name)
        if rule_id in seen_ids:
            raise RuleSetError(f"duplicate rule id {rule_id!r} in rules.toml")
        seen_ids.add(rule_id)
        rules[rule_id] = _build_rule(rule_id, fields)

    return rules


def cross_check_registry(rules: dict[str, Rule], registry: dict[str, object]) -> None:
    """Raise RuleSetError unless rules.toml and the matcher registry agree exactly."""
    rule_ids = set(rules)
    registry_ids = set(registry)

    missing_matchers = rule_ids - registry_ids
    if missing_matchers:
        raise RuleSetError(
            f"rule(s) with no registered matcher: {', '.join(sorted(missing_matchers))}"
        )

    orphan_matchers = registry_ids - rule_ids
    if orphan_matchers:
        raise RuleSetError(
            f"matcher(s) registered with no rules.toml entry: {', '.join(sorted(orphan_matchers))}"
        )
