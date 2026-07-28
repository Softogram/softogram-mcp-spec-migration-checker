from tests.helpers import FIXTURES_DIR, run_matcher

R6_DIR = FIXTURES_DIR / "r6"


def test_matches_event_store_kwarg():
    lines = run_matcher("R6", R6_DIR / "match_event_store_kwarg.py")
    assert lines == [8]


def test_does_not_match_event_store_none():
    lines = run_matcher("R6", R6_DIR / "no_match_event_store_none.py")
    assert lines == []
