from tests.helpers import FIXTURES_DIR, run_matcher

R1_DIR = FIXTURES_DIR / "r1"


def test_matches_session_attribute_access():
    lines = run_matcher("R1", R1_DIR / "match_session_attribute.py")
    assert lines == [2]


def test_matches_session_header_literal():
    lines = run_matcher("R1", R1_DIR / "match_session_header.py")
    assert lines == [2]


def test_does_not_match_unrelated_session_word():
    lines = run_matcher("R1", R1_DIR / "no_match_session_word.py")
    assert lines == []
