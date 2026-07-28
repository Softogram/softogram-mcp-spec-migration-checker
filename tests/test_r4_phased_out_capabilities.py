from tests.helpers import FIXTURES_DIR, run_matcher

R4_DIR = FIXTURES_DIR / "r4"


def test_matches_roots_usage():
    lines = run_matcher("R4", R4_DIR / "match_roots_usage.py")
    assert lines == [2]


def test_does_not_match_stdlib_logging():
    lines = run_matcher("R4", R4_DIR / "no_match_stdlib_logging.py")
    assert lines == []
