# LLD 002 - Finding Model, Report Layout, and Exit Codes

**Status:** Settled - drafted by Claude at the user's request (per this project's `CLAUDE.md` Section 2 exception); all three open questions were accepted as proposed by the user on 2026-07-23.
The answers are recorded in the "Open questions" section at the bottom, which is kept for the record.
**Links:** [HLD 001](../high-level-design/001-scan-pipeline.md) stages 5-6 - [LLD 001](001-rule-definition-format.md) (the matcher contract this consumes) - `docs/PRD.md` sections 4.1, 8 - [GitHub issue #3](https://github.com/Softogram/softogram-mcp-spec-migration-checker/issues/3).
**Last updated:** 2026-07-23

This document uses the same terms as HLD 001's glossary (Rule, Matcher, Finding, Severity, Confidence tier).

## Why this LLD exists

HLD 001 settled the pipeline's behavior in prose: findings carry rule id, file, line, and one stripped line of text; the report groups by file and ends with a summary; exit codes are 0, 1, 2; parse warnings and `NEEDS-MANUAL-CHECK` never touch the exit code.
What it did not pin down is the exact shape: the full field list of an assembled finding, the report's section order and per-finding layout, the ordering rules that make output stable enough to snapshot, and a written mock for issues #12 (reporter) and #14 (E2E snapshot) to build against.
That gap is this document.

## What's already decided (not open for re-discussion here)

- A finding carries rule ID, file, line number, and the matched source line's own text, stripped, one line only (HLD 001 stage 5).
- Everything printed comes from rule metadata; the reporter never looks anything up rule by rule (HLD 001, LLD 001).
- Report grouped by file, plain language, each finding shows severity, confidence label, and source link; ends with a one-line summary counting each outcome separately (HLD 001 stage 6).
- `NEEDS-MANUAL-CHECK` is its own visible outcome, never rendered next to "Worth checking", never affects the exit code (HLD 001 stage 6, PRD 4.1).
- Parse failures are warnings in the report, skipped files, no exit-code effect (HLD 001 stage 3).
- Exit codes 0 (clean), 1 (at least one will-break), 2 (usage error) (HLD 001 stage 6).

## Proposed design

### 1. The assembled finding

The engine combines a raw match (from LLD 001: a bare line number) with the rule's metadata into the finding the reporter consumes.
One assembled finding holds:

| Part | Field | Where it comes from |
|---|---|---|
| Position | `file` | scan - path of the matched file, **relative to the scanned root**, always with forward slashes |
| Position | `line` | the raw match |
| Position | `matched_text` | the engine, looking up that line in the source and stripping surrounding whitespace |
| Rule facts | `rule_id`, `title`, `severity`, `confidence`, `explanation`, `source_url`, `source_checked` | the rule's metadata, copied as-is |

Two calls inside this table:

- **Paths are relative to the scanned root, with forward slashes on every platform.**
  This is what makes the E2E snapshot (#14) portable: the same scan on two machines, or on Windows vs. macOS, must produce byte-identical output.
  An absolute path would embed one developer's home directory into the snapshot.
- **A `NEEDS-MANUAL-CHECK` result is a separate, smaller record: rule id plus file, no line and no matched text.**
  The cannot-tell marker (LLD 001 section 4) says "a human must look at this file for this rule"; it does not point at a line, so pretending it has one would be false precision.
  The reporter prints it using the rule's `manual_check_text`.

### 2. Report layout

Plain text only, no colors, no timing information, no version string.
Every one of those exclusions exists for the same reason: the report must be stable enough that the E2E snapshot only changes when a finding actually changes.
Color also costs a dependency or terminal-detection logic; it can arrive later behind the future `--json`/formatting work without touching this contract.

Section order, top to bottom:

1. **Header:** one line naming the tool, the scanned path as given by the user, and how many Python files were scanned.
2. **File groups:** one block per file that has at least one finding, sorted alphabetically by relative path.
   Inside a block, findings are sorted by line number, ties broken by rule id.
   Files with no findings do not appear.
3. **NEEDS MANUAL CHECK section:** appears only when at least one cannot-tell result exists.
   Grouped by rule (sorted by rule id), each entry printing the rule's title, its `manual_check_text`, the affected files (sorted), and the source link.
   Its heading spells out what it means ("the tool could not tell whether this rule applies to you") so it cannot be misread as a severity.
4. **Skipped files section:** appears only when at least one file failed to parse; lists each file and a one-line reason, sorted by path.
5. **Summary:** exactly one line with four counts, always all four, even when zero: will break, worth checking, needs manual check, files skipped.

Each finding inside a file group prints five lines' worth of information, in this order: the line number with severity and confidence labels and the rule title; the matched source line itself, quoted; the plain-language explanation; the source link with its last-checked date.
The severity labels render as `[THIS WILL BREAK]` and `[Worth checking]`, deliberately different in weight - uppercase is reserved for the tier that fails the build.

A clean scan prints the header, a single line saying no migration findings were found, and the summary with zero counts.

### 3. The exit-code contract

| Code | Meaning | Notes |
|---|---|---|
| 0 | Scan completed, no will-break findings | Worth-checking findings, needs-manual-check results, and parse warnings may all exist and still exit 0 |
| 1 | Scan completed, at least one will-break finding | The only code driven by findings |
| 2 | Usage error | Path does not exist or is unreadable, unknown flag - the scan never ran |
| 3 | Unexpected internal error | The tool itself crashed - the scan's answer is unknown |

Code 3 is the one addition beyond HLD 001's settled 0/1/2, and it exists to protect code 1's meaning.
A Python program that dies on an unhandled error exits with code 1 by default - the same number this tool uses to mean "your server will break."
Without a crash guard, a bug in our tool would be indistinguishable from a finding to any script checking the exit code.
So the entry point catches unexpected failures, prints a plain message asking the user to file an issue, and exits 3.
This extends the HLD's contract rather than contradicting it: 0, 1, and 2 keep exactly their settled meanings.

A scanned folder that exists but contains zero Python files is not an error: the header says 0 files scanned, the summary is all zeros, and the exit code is 0.
An empty folder honestly contains nothing that will break; a loud header line is the right way to signal a probably-wrong path, not a failing code.

### 4. Determinism rules (what makes #14's snapshot possible)

Stated once, as a contract the reporter must obey:

- All ordering is fully specified above (files alphabetical, findings by line then rule id, manual-check entries by rule id, skipped files by path). No ordering may depend on filesystem walk order or dictionary insertion order.
- No absolute paths, no timestamps, no durations, no version numbers anywhere in the output.
- All printed prose comes from `rules.toml`, so a wording improvement is a data diff plus a snapshot refresh, never a code change.

### 5. The report mock (the target for #12 and #14)

This mock is the **layout** target: structure, ordering, labels, and summary shape are the contract.
The explanation sentences are indicative stand-ins - the real text lives in `rules.toml` (written in issues #7-#11), and the E2E snapshot gets generated from a real run in #14.
The mock assumes the "before" example server (issue #13) exercises every report feature: R1 and R2 firing as will-break, R4 and R5 as worth-checking, and R3 landing in needs-manual-check because the example picks its transport from an environment variable at runtime.

```
mcp-migration-check: scanned 2 Python files under examples/before

server.py
  line 14  [THIS WILL BREAK]  (Confirmed)  R1 - Old-style session usage
      > session_id = request.headers.get("Mcp-Session-Id")
      Sessions are removed in the 2026-07-28 spec update. Every request must
      carry what it needs on its own; code that reads or stores a session ID
      will stop working.
      Source: https://modelcontextprotocol.io/specification/draft/changelog (checked 2026-07-14)

  line 31  [THIS WILL BREAK]  (Confirmed)  R2 - Session-keyed server memory
      > BASKETS[session_id] = new_basket()
      Server-side memory keyed to a session must become an explicit handle
      that the client passes back on later requests.
      Source: https://modelcontextprotocol.io/specification/draft/changelog (checked 2026-07-14)

  line 58  [Worth checking]  (Reported)  R5 - Hand-written MCP error number
      > if err.code == -32601:
      Trusted sources report MCP error numbers may change in this update, but
      the official changelog does not confirm which ones. Verify this number
      against the final spec.
      Source: https://chatforest.com/builders-log/... (checked 2026-07-14)

tools/logging_setup.py
  line 9   [Worth checking]  (Reported)  R4 - Phased-out capability: Logging
      > server.set_logging_level("debug")
      Logging is reported as being phased out with a grace period. It will not
      break on July 28, but plan to move off it.
      Source: https://aaif.io/blog/mcp-is-growing-up/ (checked 2026-07-14)

NEEDS MANUAL CHECK - the tool could not tell whether these rules apply to you
  R3 - Missing required headers Mcp-Method / Mcp-Name
      Your server's transport (web vs. local-only) is decided at runtime, so
      the tool cannot tell whether this rule applies. If your server is
      reachable over the web, these two headers are required on every request.
      Files: server.py
      Source: https://modelcontextprotocol.io/specification/draft/changelog (checked 2026-07-14)

Summary: 2 will break, 2 worth checking, 1 needs manual check, 0 files skipped
```

Exit code for this run: 1.

## Open questions - now settled (answers recorded 2026-07-23)

1. **Exit code 3 for internal crashes: accepted.**
   The 0/1/2 meanings stay exactly as HLD 001 settled them; 3 is the crash guard that keeps code 1 trustworthy.
2. **No color in v0.1.0: accepted.**
   Plain text, byte-stable output; color is a later cosmetic layer.
3. **Summary line: kept as proposed.**
   Exactly the four outcome counts; the scanned-file count lives in the header only.

## Who's waiting on this

Directly: issue #12 (reporter and exit codes) and #14 (E2E snapshot target).
Indirectly: #13 (the before/after example needs to know the report it is supposed to produce).

## Next step

Settled.
Issues #12, #13, and #14 have their target; all general design gates are now closed.
The only remaining design work is R3-specific: issues #20 (detectability) and #21 (signal order).
