"""Scan engine behavior beyond individual rules: parse failures, relative
paths. See docs/high-level-design/001-scan-pipeline.md stage 3 and issue #5
acceptance criteria.
"""

from mcp_migration_check.engine import run_scan
from tests.helpers import FIXTURES_DIR

MALFORMED_ROOT = FIXTURES_DIR / "malformed"


def test_malformed_file_is_skipped_and_scan_continues():
    result = run_scan(MALFORMED_ROOT)
    skipped_names = {s.file for s in result.skipped_files}
    assert "broken.py" in skipped_names
    assert result.files_scanned == 1  # only good.py parsed cleanly
    assert "good.py" not in skipped_names


def test_finding_paths_are_relative_posix():
    result = run_scan(FIXTURES_DIR / "r1")
    assert result.findings, "expected at least one finding from the r1 fixtures"
    for finding in result.findings:
        assert not finding.file.startswith("/")
        assert "\\" not in finding.file
