from tests.helpers import FIXTURES_DIR, run_matcher

R1_DIR = FIXTURES_DIR / "r1"


def test_matches_session_header_literal():
    lines = run_matcher("R1", R1_DIR / "match_session_header.py")
    assert lines == [2]


def test_does_not_match_unrelated_session_word():
    lines = run_matcher("R1", R1_DIR / "no_match_session_word.py")
    assert lines == []


def test_does_not_match_sdk_session_id_property():
    """Regression guard: ctx.session_id is a real, still-supported SDK
    property (confirmed against the actual installed mcp package) - it
    must not be flagged as old-style session usage. See
    docs/LEARNINGS.md's 2026-07-28 entry.
    """
    lines = run_matcher("R1", R1_DIR / "no_match_sdk_session_id_property.py")
    assert lines == []
