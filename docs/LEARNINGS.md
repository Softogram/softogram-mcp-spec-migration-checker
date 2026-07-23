# Learnings Log

Running, dated log of what got learned building this project.
A few lines per session, appended, never rewritten.
See this folder's `CLAUDE.md` section 5 for why this exists.

---

## 2026-07-14 - Kickoff: architecture and planning

- **Concept: rules-as-data vs rules-as-code.**
  The tool splits every check into metadata (what it means, how sure we are, where it came from - kept in a data file) and a matcher (the AST-walking logic, kept as small code).
  Fully-declarative rules were rejected because they require inventing a pattern mini-language; fully-hardcoded rules were rejected because the July 28 spec update would then mean rewriting the tool.
  How to explain it to someone else: "the engine is a record player, the rules file is the record - when the spec changes, you swap the record, not the player."
- **Concept: why false positives are the top product risk for a checker tool.**
  A migration checker that cries wolf gets uninstalled after one wrong "this will break".
  That's why every rule needs a must-NOT-match test fixture, not just a must-match one, and why findings carry confidence labels (Confirmed vs Reported) instead of pretending equal certainty.
- **Process: E2E testing a CLI means running the CLI.**
  The end-to-end check tool runs the installed command against real example folders and compares report + exit code to an expected snapshot - it does not import internals.
  That mirrors how an end user actually experiences the tool, which is the repo's own bug-reproduction rule applied to testing.

## 2026-07-14 - R3 design: transport detection and applicability vs. confidence

- **Concept: transport is knowable in only two of three real cases.**
  Statically, a server's transport (stdio vs. Streamable HTTP) is decided one of three ways: a literal value at the call site (readable from the AST), transport-specific imports or SDK wiring (a weaker but often-present signal), or a runtime decision - a CLI flag, an environment variable, a config file read at startup.
  Only the first two are things static analysis can ever know.
  The third is a hard limit, not a gap in effort - no amount of reading the source resolves what a flag decides at runtime.
  How to explain it to someone else: "reading the code can tell you what the code can do, not what someone will type when they run it."
- **Concept: a rule's target can vanish at a different layer than the one it names.**
  The two new required headers, `Mcp-Method` and `Mcp-Name`, are transport-layer HTTP headers, not application-level constructs.
  If the official SDK's Streamable HTTP transport already emits and validates them, a server just gets compliance for free after an SDK upgrade - leaving no pattern in the *application* code to match at all.
  This means "the rule is Confirmed by the spec" and "the rule has a matchable app-code pattern" are two separate questions, and the second one has to be checked before the rule ships, or the tool would be confidently labeling something it can't actually detect - a review caught this before any code was written.
  How to explain it to someone else: "confirming the spec changed doesn't confirm your checker can see the change."
- **Concept: applicability is not confidence, and mixing them is a correctness bug for this tool.**
  Confidence (Confirmed vs. Reported, PRD 4.1) is about how sure we are the *rule* correctly describes a real spec change.
  Applicability - "does this rule even apply to your server" - is a different axis entirely.
  When the tool can't tell if a server is web-exposed, showing that as "Reported / worth checking" would tell the reader our *source* is shaky, when the truth is the source is rock-solid and the ambiguity is about *them*.
  The fix: a distinct, visible outcome (`NEEDS-MANUAL-CHECK`) that never contributes to the exit code and is never rendered next to the Reported tier - not a new global severity, since generalizing the whole taxonomy for one rule's edge case would be over-engineering for a 10-hour build.

## 2026-07-14 - Closing HLD 001: fixture stability and "boring" vs. "enterprise" tooling

- **Concept: what a finding snapshot captures affects how often it breaks for no reason.**
  A finding's fixture snapshot could capture just a line number, a single matched line's text, or a multi-line context block.
  Settled on a single line's text: enough for a human to recognize the match without opening the file, but a multi-line block would make snapshots drift whenever anything nearby in a fixture file was reformatted - unrelated churn that has nothing to do with whether the rule still matches correctly.
  How to explain it to someone else: "a snapshot should only change when the thing it's testing changes, not when its neighbors do."
- **Concept: "boring, well-known" and "enterprise-grade" aren't actually in tension for tooling choices.**
  Asked to pick tools for "enterprise development," the honest answer wasn't to add process (pre-commit matrices, tox, semantic-release, security scanners) - it was to pick the same defaults real production codebases already converged on (`pytest`, `ruff`, `pyproject.toml` + `hatchling`, optional `mypy`), because those defaults earned their status precisely by being simple *and* robust at once.
  The actual enterprise practices left out (multi-version test matrices, release automation) are about coordinating a team over time, not about whether a solo 10-hour tool's rules are correct - so they went into `docs/FUTURE-UPGRADES.md` instead of the v1 scaffold.
  How to explain it to someone else: "the boring choice and the enterprise choice are usually the same tool, once you separate 'correctness tooling' from 'team-coordination process.'"

## 2026-07-21 - LLD 001 proposal: rule format, registry, and the shape of a matcher's answer

- **Concept: a registry is a choice between visible and invisible wiring.**
  Three ways exist to connect a rule id to its matcher code: an explicit lookup table (one visible mapping, read in a glance), decorator self-registration (each matcher tags itself, a registry fills up as a side effect of imports), and filename conventions (the engine guesses wiring from file names).
  The explicit table won because the other two trade five lines of typing for invisible machinery: decorator registries depend on import order and side effects, and convention-based discovery silently unwires a rule when a file gets renamed.
  How to explain it to someone else: "for five rules, a table you can read beats a mechanism you have to trust."
- **Concept: constraining what a matcher can say is what enforces honesty mechanically.**
  A matcher's entire vocabulary in the proposed contract is line numbers plus one cannot-tell flag; every printed word (severity, confidence, explanation, source link) comes from the metadata file.
  This is not just tidiness: it means a rule physically cannot be promoted from "worth checking" to "will break" inside code, only by a visible one-line data diff in version control.
  How to explain it to someone else: "if the code can't speak, the code can't lie - the data file does all the talking, and data diffs are easy to review."
- **Concept: an optional contract feature keeps a special case from taxing everyone.**
  R3 needs a third outcome (cannot tell, human must check), but forcing all five matchers to know about a three-state result would push R3's complexity onto four rules that never use it.
  The proposed shape makes the cannot-tell marker part of the general contract (so the engine stays rule-agnostic) but optional to return (so simple rules stay a list of hits).
  How to explain it to someone else: "design the contract so the common case doesn't pay for the rare one."
- **Process: a deadline that slipped changes what the deadline is.**
  The weekend ship target (Jul 18-19) passed with all planning done and zero build hours spent.
  The date that actually matters was always the spec landing on Jul 28: shipping before it keeps the tool's "find out before it breaks" pitch honest; shipping after turns it into a cleanup tool and forces re-verifying every rule against final spec text.
  How to explain it to someone else: "when you miss an internal deadline, re-anchor to the external one, because that one doesn't move."

## 2026-07-23 - LLD 002: report determinism and the exit-code collision

- **Concept: snapshot-testable output must be deterministic by contract, not by luck.**
  The E2E check compares the CLI's report to a stored snapshot byte for byte, so every source of run-to-run variation had to be squeezed out explicitly: fully specified sort orders (never filesystem walk order or dict order), paths relative to the scan root with forward slashes on every platform, and no timestamps, durations, colors, or version strings anywhere in the output.
  How to explain it to someone else: "if you want to diff a program's output against a saved copy, the output has to be a pure function of the input - list everything else that could leak in, and ban each one."
- **Concept: a crashing Python program exits with code 1 - the same code this tool uses to mean "your server will break."**
  Without a crash guard, a bug in the checker is indistinguishable from a real finding to any script reading the exit code, which silently poisons the tool's most machine-readable signal.
  The fix is a top-level guard that catches unexpected failures and exits with a distinct code (3), leaving 0/1/2 with their settled meanings.
  How to explain it to someone else: "decide what every exit code means, including the one your language emits when you crash - because your users' scripts can't tell your bug from your verdict."
