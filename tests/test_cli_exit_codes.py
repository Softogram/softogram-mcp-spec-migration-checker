"""Exit code contract: 0 clean, 1 will-break, 2 usage error. See
docs/low-level-design/002-finding-model-report-and-exit-codes.md section 3
and issue #12 acceptance criteria.
"""

import subprocess
import sys

from tests.helpers import FIXTURES_DIR


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "mcp_migration_check.cli", *args],
        capture_output=True,
        text=True,
    )


def test_exit_zero_on_clean_scan():
    result = _run_cli(str(FIXTURES_DIR / "r2" / "no_match_handle_keyed.py"))
    assert result.returncode == 0
    assert "No migration findings found." in result.stdout


def test_exit_one_when_a_will_break_finding_exists():
    result = _run_cli(str(FIXTURES_DIR / "r1" / "match_session_header.py"))
    assert result.returncode == 1
    assert "THIS WILL BREAK" in result.stdout


def test_exit_two_on_missing_path():
    result = _run_cli("/definitely/does/not/exist")
    assert result.returncode == 2
    assert result.stderr.strip() != ""


def test_empty_folder_with_no_python_files_exits_zero(tmp_path):
    result = _run_cli(str(tmp_path))
    assert result.returncode == 0
    assert "scanned 0 Python files" in result.stdout
