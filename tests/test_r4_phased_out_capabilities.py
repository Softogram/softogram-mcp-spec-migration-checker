from tests.helpers import FIXTURES_DIR, run_matcher

R4_DIR = FIXTURES_DIR / "r4"


def test_matches_roots_usage():
    lines = run_matcher("R4", R4_DIR / "match_roots_usage.py")
    assert lines == [2]


def test_does_not_match_stdlib_logging():
    lines = run_matcher("R4", R4_DIR / "no_match_stdlib_logging.py")
    assert lines == []


def test_does_not_match_set_logging_level_handler():
    """set_logging_level is not a ServerSession method (confirmed against
    the real SDK) - it belongs to R8's removed-RPC-handler theme, not
    this rule's capability-consumption theme. See
    docs/LEARNINGS.md's 2026-07-28 entry.
    """
    lines = run_matcher("R4", R4_DIR / "no_match_set_logging_level_handler.py")
    assert lines == []
