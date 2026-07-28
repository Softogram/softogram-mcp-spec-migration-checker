"""--json and --explain CLI options. See issues #18 and #19."""

import json
import subprocess
import sys

from tests.helpers import FIXTURES_DIR


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "mcp_migration_check.cli", *args],
        capture_output=True,
        text=True,
    )


def test_json_output_round_trips_and_matches_the_human_report():
    fixture = FIXTURES_DIR / "r1" / "match_session_header.py"
    result = _run_cli("--json", str(fixture))
    assert result.returncode == 1

    payload = json.loads(result.stdout)  # must be valid JSON
    assert payload["files_scanned"] == 1
    assert payload["summary"]["will_break"] == 1
    assert len(payload["findings"]) == 1

    finding = payload["findings"][0]
    assert finding["rule_id"] == "R1"
    assert finding["severity"] == "will-break"
    assert finding["confidence"] == "confirmed"
    assert finding["line"] == 2
    assert "source_url" in finding and "source_checked" in finding


def test_json_clean_scan_has_empty_findings_and_exit_zero():
    fixture = FIXTURES_DIR / "r2" / "no_match_handle_keyed.py"
    result = _run_cli("--json", str(fixture))
    assert result.returncode == 0

    payload = json.loads(result.stdout)
    assert payload["findings"] == []
    assert payload["summary"]["will_break"] == 0


def test_explain_prints_rule_metadata_and_exits_zero():
    result = _run_cli("--explain", "R1")
    assert result.returncode == 0
    assert "R1 - " in result.stdout
    assert "Severity:" in result.stdout
    assert "Confidence:" in result.stdout
    assert "Source:" in result.stdout


def test_explain_unknown_rule_id_exits_two():
    result = _run_cli("--explain", "NOT_A_RULE")
    assert result.returncode == 2
    assert "unknown rule id" in result.stderr
