"""Fail-fast validation of rules.toml. See
docs/low-level-design/001-rule-definition-format.md section 2: a typo in
the data can never silently become a wrong label in a report.
"""

import tempfile
from pathlib import Path

import pytest

from mcp_migration_check.ruleset import RuleSetError, load_rules


def _write_toml(text: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False)
    tmp.write(text)
    tmp.close()
    return Path(tmp.name)


def test_missing_required_field_is_rejected():
    path = _write_toml('[R1]\ntitle = "x"\nseverity = "will-break"\n')
    with pytest.raises(RuleSetError, match="R1"):
        load_rules(path)


def test_invalid_severity_is_rejected():
    path = _write_toml(
        '[R1]\ntitle = "x"\nseverity = "maybe"\nconfidence = "confirmed"\n'
        'explanation = "e"\nsource_url = "u"\nsource_checked = "2026-01-01"\n'
    )
    with pytest.raises(RuleSetError, match="severity"):
        load_rules(path)


def test_invalid_confidence_is_rejected():
    path = _write_toml(
        '[R1]\ntitle = "x"\nseverity = "will-break"\nconfidence = "pretty-sure"\n'
        'explanation = "e"\nsource_url = "u"\nsource_checked = "2026-01-01"\n'
    )
    with pytest.raises(RuleSetError, match="confidence"):
        load_rules(path)


def test_unparseable_date_is_rejected():
    path = _write_toml(
        '[R1]\ntitle = "x"\nseverity = "will-break"\nconfidence = "confirmed"\n'
        'explanation = "e"\nsource_url = "u"\nsource_checked = "not-a-date"\n'
    )
    with pytest.raises(RuleSetError, match="source_checked"):
        load_rules(path)


def test_duplicate_id_is_rejected():
    path = _write_toml(
        '[R1]\nid = "R1"\ntitle = "x"\nseverity = "will-break"\nconfidence = "confirmed"\n'
        'explanation = "e"\nsource_url = "u"\nsource_checked = "2026-01-01"\n\n'
        '[R1_dup]\nid = "R1"\ntitle = "y"\nseverity = "will-break"\nconfidence = "confirmed"\n'
        'explanation = "e"\nsource_url = "u"\nsource_checked = "2026-01-01"\n'
    )
    with pytest.raises(RuleSetError, match="duplicate"):
        load_rules(path)
