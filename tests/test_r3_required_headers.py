from mcp_migration_check.models import NEEDS_MANUAL_CHECK
from tests.helpers import FIXTURES_DIR, run_matcher

R3_DIR = FIXTURES_DIR / "r3"


def test_handrolled_endpoint_missing_headers_is_will_break():
    lines = run_matcher("R3", R3_DIR / "handrolled_missing_headers.py")
    assert lines == [7]


def test_handrolled_endpoint_with_both_headers_is_silent():
    lines = run_matcher("R3", R3_DIR / "handrolled_compliant.py")
    assert lines == []


def test_stdio_only_is_silent():
    lines = run_matcher("R3", R3_DIR / "stdio_only.py")
    assert lines == []


def test_runtime_decided_transport_is_needs_manual_check():
    result = run_matcher("R3", R3_DIR / "cannot_tell_runtime_transport.py")
    assert result is NEEDS_MANUAL_CHECK
