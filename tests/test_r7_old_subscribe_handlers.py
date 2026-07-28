from tests.helpers import FIXTURES_DIR, run_matcher

R7_DIR = FIXTURES_DIR / "r7"


def test_matches_subscribe_resource_decorator():
    lines = run_matcher("R7", R7_DIR / "match_subscribe_resource_decorator.py")
    assert lines == [6]


def test_does_not_match_list_tools_decorator():
    lines = run_matcher("R7", R7_DIR / "no_match_list_tools_decorator.py")
    assert lines == []
