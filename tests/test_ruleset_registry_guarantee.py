"""LLD 001's auditability guarantee, made mechanical: every rule in
rules.toml has a registered matcher and vice versa. See issue #6's
acceptance criteria and docs/low-level-design/001-rule-definition-format.md
section 5.
"""

from pathlib import Path

import pytest

from mcp_migration_check.ruleset import RuleSetError, cross_check_registry, load_rules

RULES_TOML = (
    Path(__file__).parent.parent / "src" / "mcp_migration_check" / "rules" / "rules.toml"
)


def test_rules_toml_and_registry_agree_in_both_directions():
    from mcp_migration_check.rules import REGISTRY

    rules = load_rules(RULES_TOML)
    cross_check_registry(rules, REGISTRY)  # must not raise


def test_missing_matcher_is_rejected():
    from mcp_migration_check.rules import REGISTRY

    rules = load_rules(RULES_TOML)
    incomplete_registry = {k: v for k, v in REGISTRY.items() if k != "R1"}
    with pytest.raises(RuleSetError, match="R1"):
        cross_check_registry(rules, incomplete_registry)


def test_orphan_matcher_is_rejected():
    from mcp_migration_check.rules import REGISTRY

    rules = load_rules(RULES_TOML)
    extra_registry = dict(REGISTRY)
    extra_registry["R99"] = lambda *a: []
    with pytest.raises(RuleSetError, match="R99"):
        cross_check_registry(rules, extra_registry)
