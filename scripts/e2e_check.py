#!/usr/bin/env python3
"""End-to-end release gate: run the installed CLI against the before/after
examples and diff the report against checked-in snapshots.

Goes through the CLI as a real user would - a subprocess, not an import of
the package's internals (that's what the unit tests are for). See
docs/high-level-design/001-scan-pipeline.md, testing layer 3, and issue
#14's acceptance criteria.

Usage, from a clean checkout (after `pip install .` or equivalent):

    python scripts/e2e_check.py
"""

from __future__ import annotations

import difflib
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SNAPSHOTS_DIR = REPO_ROOT / "tests" / "e2e" / "snapshots"

CASES = [
    # (example folder, snapshot file, expected exit code)
    ("examples/before", "before.txt", 1),
    ("examples/after", "after.txt", 0),
]


def _run_cli(path_arg: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["mcp-migration-check", path_arg],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def _check_one(example_path: str, snapshot_name: str, expected_exit: int) -> list[str]:
    problems: list[str] = []
    expected_text = (SNAPSHOTS_DIR / snapshot_name).read_text()

    result = _run_cli(example_path)

    if result.returncode != expected_exit:
        problems.append(
            f"{example_path}: expected exit code {expected_exit}, got {result.returncode}\n"
            f"stderr: {result.stderr}"
        )

    if result.stdout != expected_text:
        diff = "\n".join(
            difflib.unified_diff(
                expected_text.splitlines(),
                result.stdout.splitlines(),
                fromfile=f"expected ({snapshot_name})",
                tofile="actual",
                lineterm="",
            )
        )
        problems.append(f"{example_path}: report output does not match snapshot\n{diff}")

    return problems


def main() -> int:
    if shutil.which("mcp-migration-check") is None:
        print(
            "e2e_check: mcp-migration-check is not on PATH - install the package first "
            "(e.g. `pip install .`) and activate that environment.",
            file=sys.stderr,
        )
        return 1

    all_problems: list[str] = []
    for example_path, snapshot_name, expected_exit in CASES:
        all_problems.extend(_check_one(example_path, snapshot_name, expected_exit))

    if all_problems:
        print("e2e_check: FAILED\n")
        print("\n\n".join(all_problems))
        return 1

    print("e2e_check: all example scans match their snapshots. PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
