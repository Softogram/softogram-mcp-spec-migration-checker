from tests.helpers import FIXTURES_DIR, run_matcher

R8_DIR = FIXTURES_DIR / "r8"


def test_matches_set_logging_level_decorator():
    lines = run_matcher("R8", R8_DIR / "match_set_logging_level_decorator.py")
    assert lines == [6]


def test_does_not_match_list_prompts_decorator():
    lines = run_matcher("R8", R8_DIR / "no_match_list_prompts_decorator.py")
    assert lines == []
