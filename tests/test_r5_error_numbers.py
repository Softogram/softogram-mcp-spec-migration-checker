from tests.helpers import FIXTURES_DIR, run_matcher

R5_DIR = FIXTURES_DIR / "r5"


def test_matches_mcp_reserved_error_code():
    lines = run_matcher("R5", R5_DIR / "match_error_code.py")
    assert lines == [2]


def test_does_not_match_http_status_code():
    lines = run_matcher("R5", R5_DIR / "no_match_http_status.py")
    assert lines == []
