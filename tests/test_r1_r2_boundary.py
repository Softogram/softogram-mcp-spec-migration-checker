"""Proves R1 and R2 never double-fire on the same line.

R1 was narrowed on 2026-07-28 to only match hand-rolled reads of the raw
"Mcp-Session-Id" header by string literal (see r1_session_usage.py's
module docstring for why the earlier attribute-based check was dropped -
ctx.session_id turned out to be a legitimate, still-supported SDK
property). Since R1 no longer inspects attribute nodes at all, its
pattern space (string-literal header reads) and R2's (subscript/method
keys named like a session) are now disjoint by construction - this test
is the regression guard for that.
"""

from tests.helpers import FIXTURES_DIR, run_matcher

FIXTURE = FIXTURES_DIR / "boundary" / "r1_r2_ambiguous.py"


def test_r1_does_not_fire_on_the_ambiguous_line():
    assert run_matcher("R1", FIXTURE) == []


def test_r2_fires_on_the_ambiguous_line():
    lines = run_matcher("R2", FIXTURE)
    assert lines == [5]
