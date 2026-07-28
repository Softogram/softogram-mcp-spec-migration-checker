from tests.helpers import FIXTURES_DIR, run_matcher

R5_DIR = FIXTURES_DIR / "r5"


def test_matches_a_renumbered_error_code():
    lines = run_matcher("R5", R5_DIR / "match_error_code.py")
    assert lines == [2]


def test_does_not_match_http_status_code():
    lines = run_matcher("R5", R5_DIR / "no_match_http_status.py")
    assert lines == []


def test_does_not_match_unrenumbered_mcp_code():
    """-32601 is a real MCP code, but not one of the four confirmed
    renumbered ones - see docs/LEARNINGS.md's 2026-07-28 entry.
    """
    lines = run_matcher("R5", R5_DIR / "no_match_unrenumbered_mcp_code.py")
    assert lines == []


def test_does_not_match_grandfathered_range():
    """-32000..-32019 is explicitly grandfathered as implementation-defined
    by the final changelog - must not be flagged.
    """
    lines = run_matcher("R5", R5_DIR / "no_match_grandfathered_range.py")
    assert lines == []
