"""File discovery skip behavior. See issue #4 acceptance criteria and
docs/high-level-design/001-scan-pipeline.md stage 2.
"""

from mcp_migration_check.discovery import discover_python_files
from tests.helpers import FIXTURES_DIR

DISCOVERY_ROOT = FIXTURES_DIR / "discovery"


def test_finds_real_files_and_skips_venvs_hidden_and_cache_dirs():
    found = {p.name for p in discover_python_files(DISCOVERY_ROOT)}
    assert found == {"found_me.py"}


def test_single_python_file_argument_is_returned_directly():
    single_file = DISCOVERY_ROOT / "keep" / "found_me.py"
    found = discover_python_files(single_file)
    assert found == [single_file]
