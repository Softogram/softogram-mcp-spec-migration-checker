# Test conventions

Run the whole suite with one command from a clean checkout:

```
pytest
```

## Per-rule fixtures

Every rule has its own folder under `tests/fixtures/<rule>/`.
Each folder holds at least:

- One `match_*.py` file that MUST produce a finding.
- One `no_match_*.py` file that MUST NOT produce a finding.

The must-not fixtures are the important half.
A checker that cries wolf gets uninstalled after one wrong "this will break" - see `docs/PRD.md` section 12.

R3 has four fixtures instead of two, since it is the one conditional rule (see `docs/low-level-design/003-r3-transport-detection.md`):
a hand-rolled endpoint missing the headers, a hand-rolled endpoint handling them, a stdio-only server, and a server whose transport is decided at runtime.

## The shared assertion helper

`tests/helpers.py` exposes `run_matcher(rule_id, fixture_path)`.
It parses the fixture into an AST and calls that rule's registered matcher directly - no CLI, no engine - so a rule test asserts exactly one thing: "this matcher returns exactly these line numbers for this file."

To add a test for a new rule fixture:

1. Add the fixture file under `tests/fixtures/<rule>/`.
2. In `tests/test_<rule>.py`, call `run_matcher("<RULE_ID>", path)` and assert the exact list of line numbers (or `NEEDS_MANUAL_CHECK` for R3's cannot-tell case).

## Other test layers

- `test_ruleset_validation.py` - `rules.toml` fails fast on bad data (missing field, bad severity/confidence, bad date, duplicate id).
- `test_ruleset_registry_guarantee.py` - `rules.toml` and the matcher registry agree in both directions (LLD 001's auditability guarantee, made mechanical).
- `test_discovery.py` - virtualenvs, hidden folders, and caches are skipped; real files are found.
- `test_engine.py` - a malformed file becomes a skipped-file warning and the scan continues.
- `test_cli_exit_codes.py` - the 0/1/2 exit code contract, run through the actual CLI entry point as a subprocess.
- `test_cli_json_and_explain.py` - `--json` round-trips through a parser and matches the human report's content; `--explain` prints rule metadata and exits 2 on an unknown rule id.

`scripts/e2e_check.py` is a separate, higher layer: it runs the *installed* CLI against `examples/before` and `examples/after` (both the plain report and `--json`) and diffs the output against a checked-in snapshot. It is the release gate, not a unit test - see `docs/high-level-design/001-scan-pipeline.md`, testing layer 3.
