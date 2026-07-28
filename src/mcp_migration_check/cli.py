"""Entry point: argument parsing, path validation, exit codes, crash guard.

See docs/high-level-design/001-scan-pipeline.md stage 1 and
docs/low-level-design/002-finding-model-report-and-exit-codes.md section 3
for the exit-code contract this implements.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mcp_migration_check.engine import load_ruleset_and_registry, run_scan
from mcp_migration_check.report import render_explain, render_json, render_report

EXIT_CLEAN = 0
EXIT_WILL_BREAK = 1
EXIT_USAGE_ERROR = 2
EXIT_INTERNAL_ERROR = 3


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mcp-migration-check",
        description=(
            "Reports what will break in a Python MCP server under the "
            "2026-07-28 MCP spec update."
        ),
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="folder or file to scan (default: current folder)"
    )
    parser.add_argument(
        "--json", action="store_true", help="print findings as machine-readable JSON"
    )
    parser.add_argument(
        "--explain", metavar="RULE_ID", help="print one rule's full explanation and exit"
    )
    return parser


def _run_explain(rule_id: str) -> int:
    rules, _registry = load_ruleset_and_registry()
    rule = rules.get(rule_id)
    if rule is None:
        known = ", ".join(sorted(rules))
        print(
            f"mcp-migration-check: unknown rule id '{rule_id}' - known rules: {known}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    print(render_explain(rule), end="")
    return EXIT_CLEAN


def _run(argv: list[str]) -> int:
    args = _build_parser().parse_args(argv)  # argparse itself exits 2 on a bad flag

    if args.explain:
        return _run_explain(args.explain)

    path_arg = args.path
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
    report = render_json(result, path_arg) if args.json else render_report(result, path_arg)
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
