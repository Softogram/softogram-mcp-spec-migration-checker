"""Entry point: argument parsing, path validation, exit codes, crash guard.

See docs/high-level-design/001-scan-pipeline.md stage 1 and
docs/low-level-design/002-finding-model-report-and-exit-codes.md section 3
for the exit-code contract this implements.
"""

from __future__ import annotations

import sys
from pathlib import Path

from mcp_migration_check.engine import run_scan
from mcp_migration_check.report import render_report

EXIT_CLEAN = 0
EXIT_WILL_BREAK = 1
EXIT_USAGE_ERROR = 2
EXIT_INTERNAL_ERROR = 3


def _parse_args(argv: list[str]) -> str:
    if len(argv) == 0:
        return "."
    if len(argv) == 1 and argv[0] not in ("-h", "--help"):
        return argv[0]
    print("usage: mcp-migration-check [path]", file=sys.stderr)
    raise SystemExit(EXIT_USAGE_ERROR)


def _run(argv: list[str]) -> int:
    path_arg = _parse_args(argv)
    root = Path(path_arg)

    if not root.exists():
        print(f"mcp-migration-check: path does not exist: {path_arg}", file=sys.stderr)
        return EXIT_USAGE_ERROR
    if root.is_file() and root.suffix != ".py":
        print(f"mcp-migration-check: not a Python file: {path_arg}", file=sys.stderr)
        return EXIT_USAGE_ERROR
    if not root.is_dir() and not root.is_file():
        print(f"mcp-migration-check: not a file or folder: {path_arg}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    result = run_scan(root)
    report = render_report(result, path_arg)
    print(report, end="")

    return EXIT_WILL_BREAK if result.will_break_count > 0 else EXIT_CLEAN


def main() -> None:
    try:
        exit_code = _run(sys.argv[1:])
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - the crash guard, deliberately broad
        print(
            "mcp-migration-check: unexpected internal error - please file an issue "
            f"at the project's GitHub repo with this message: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_INTERNAL_ERROR) from None
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
