"""Proves the R1/R2 boundary: one ambiguous line fires exactly one rule.

See docs/low-level-design/001-rule-definition-format.md and the R1/R2
boundary note in each matcher's module docstring. A session-id attribute
access used directly as a memory container's key belongs to R2 only - R1
must skip it.
"""

from tests.helpers import FIXTURES_DIR, run_matcher

FIXTURE = FIXTURES_DIR / "boundary" / "r1_r2_ambiguous.py"


def test_r1_skips_the_ambiguous_line():
    assert run_matcher("R1", FIXTURE) == []


def test_r2_fires_on_the_ambiguous_line():
    lines = run_matcher("R2", FIXTURE)
    assert lines == [5]
