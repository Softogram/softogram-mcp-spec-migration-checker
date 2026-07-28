from tests.helpers import FIXTURES_DIR, run_matcher

R2_DIR = FIXTURES_DIR / "r2"


def test_matches_session_keyed_subscript():
    lines = run_matcher("R2", R2_DIR / "match_session_keyed.py")
    assert lines == [5]


def test_does_not_match_handle_keyed_subscript():
    lines = run_matcher("R2", R2_DIR / "no_match_handle_keyed.py")
    assert lines == []
