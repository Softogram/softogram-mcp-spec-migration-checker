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

## 2026-07-28 - Ship day: R3's final answer, the R1/R2 boundary in practice, and a packaging trap

- **Concept: "confirmed by the spec" and "detectable in app code" can resolve to two different scopes for the same rule.**
  LLD 003 closed issues #20/#21 by narrowing R3 from "any Streamable HTTP server missing the headers" to "hand-rolled MCP-over-HTTP transport code missing them" - the SDK's own built-in transport handles the headers internally, so a server using it has nothing in its own source for a static reader to flag.
  The rule stays Confirmed (the spec change is real) but its match target shrank to exactly the code a static tool can honestly see.
  How to explain it to someone else: "a spec change being real doesn't mean every server that's affected by it has a visible fingerprint in its own source - find the actual fingerprint before writing the matcher."
- **Concept: an ambiguous line needs one rule to actively yield, not two rules to coincidentally agree.**
  `BASKETS[ctx.session_id] = ...` is simultaneously "reading a session id" (R1) and "memory keyed by a session" (R2).
  Implemented as two independent matchers, both would fire on the same line, which reads to a user as double-counting one problem, not two.
  The fix: R1's matcher explicitly marks the descendants of a subscript's key and of `get`/`setdefault`/`pop` call arguments as "not mine" before checking for its own pattern, so the boundary is enforced by one rule declining, not by two rules cooperating.
  How to explain it to someone else: "when two rules can both see the same evidence, decide in code which one recuses - don't rely on them never overlapping in practice."
- **Process: a packaging config that "should" work can still break editable installs in ways worth just avoiding.**
  Adding `force-include` to place `rules.toml` into the wheel produced a real (non-editable) directory inside the venv's `site-packages/mcp_migration_check/`, which then shadowed the editable-install redirect for the *entire* package - `import mcp_migration_check.models` failed with the package resolving to that mostly-empty directory instead of `src/`.
  The fix wasn't debugging the interaction further; it was recognizing hatchling's default wheel packaging already includes non-`.py` files under a declared package directory, so the special-case force-include was solving a problem that didn't exist and only added risk.
  How to explain it to someone else: "before reaching for a packaging escape hatch, check whether the default behavior already does what you were about to force."

## 2026-07-28 (later same day) - Checking fixtures against the real SDK found a false positive

- **Concept: a plausible-looking API is not the same as a real one.**
  Every fixture and example server up to this point was hand-authored from general knowledge of what the MCP Python SDK "probably" looks like, never verified against an actual installed package.
  Asked directly whether that verification had happened, the honest answer was no - so `pip install mcp` was run for real, against both `mcp==1.29.0` (the last pre-update release) and `mcp==2.0.0` (published the same day as the spec update, confirming the update actually shipped on schedule).
  Reading the real source turned up two fabricated things that never worked on any real version: `from mcp.server import Server` combined with a `.tool()` decorator (that decorator only exists on `FastMCP`), and Starlette's `.route()` decorator (removed from the installed Starlette release; real code needs `Route`-list wiring or a raw ASGI callable).
  How to explain it to someone else: "if a checker's own test fixtures were never run against the real thing, you don't actually know the checker works - you know it agrees with itself."
- **Concept: a rule can be correct about the spec and still wrong about the code.**
  `Context.session_id` turned out to be a real, still-supported property in the *new* SDK (`mcp/server/context.py`: "the transport's session id for this connection... `None` on stdio and stateless HTTP") - it's a connection-scoped correlation id, not the removed protocol-level session handshake.
  R1 was matching any `ctx.session_id`-style attribute read as "This will break," which meant it would have cried wolf on correct, migrated code the moment a real user ran it.
  The fix: narrow R1 to only the pattern that's genuinely never seen outside hand-rolled, non-SDK transport code - reading the raw `Mcp-Session-Id` header by its literal string name, which no documented API in either SDK version exposes to application code at all.
  How to explain it to someone else: "the spec being right about what changed doesn't make your matcher right about how to detect it - go read the object your matcher claims to be watching."
- **Process: importing example code, not just parsing it, finds a different class of bug.**
  `ast.parse()` had validated every fixture's syntax from the start, but the first time a rewritten "after" example was actually *imported* against the real SDK, `mcp.run(transport="streamable-http")` at module level blocked the whole process - the SDK really does start a server synchronously on that call.
  Guarding it behind `if __name__ == "__main__":` fixed it, and is also just correct practice for any importable module.
  How to explain it to someone else: "parsing proves the grammar is right; importing proves the module doesn't have side effects it shouldn't; only running it proves the logic is right - each layer catches a different kind of wrong, so skipping straight to the cheapest one leaves the other two unchecked."

## 2026-07-28 (still later) - Distributing a Python CLI as a real standalone binary

- **Concept: "downloadable and runs directly" is a distribution decision, not a packaging afterthought.**
  A `pip install`-based CLI still asks the user to have Python, a package manager, and (for this project) a git clone.
  PyInstaller collapses all of that into one native file per OS - the whole Python interpreter and every dependency get bundled into a single executable, so a user with zero Python on their machine can still run it.
  Verified for real, not assumed: built the executable locally, then ran it with `env -i PATH=/usr/bin:/bin` (a stripped environment with no Python, no venv, nothing this project installed) against both examples and confirmed identical output and exit codes to the `pip install` path.
- **Concept: a bundled data file needs its destination path to match where the code already looks for it.**
  PyInstaller's dependency analysis only follows Python imports automatically; `rules.toml` isn't imported, so it has to be listed explicitly in the spec's `datas`.
  The one thing that mattered: the destination path inside the bundle (`mcp_migration_check/rules/rules.toml`) had to match the *relative* structure the engine's existing `Path(__file__).parent`-based lookup expects - get that path wrong and the rule set silently fails to load only in the packaged build, never in a normal dev environment, which is exactly the kind of gap that "works on my machine" doesn't catch.
  How to explain it to someone else: "when you bundle a non-code file, ask where your own code goes looking for it - not just whether the bundler can find it to include."

## 2026-07-28 (final entry) - The real changelog published, and the backlog got its correction pass same-day

- **Concept: "draft" and "final" aren't the same document, even at the same URL pattern.**
  Every rule's `source_url` had pointed at `/specification/draft/changelog` since Week 1. Once the spec actually shipped, that page returned an empty stub - the real content moved to a dated URL (`/specification/2026-07-28/changelog.md`). Fetching the *final* text (not the blog summary, not memory of the draft) turned up things the draft-era research never had access to: the exact SEP number for session removal (2567, not 2575 - a sibling proposal), an official error-code allocation policy naming exactly four renumbered codes, and Roots/Sampling/Logging deprecation stated on the changelog itself rather than only a secondary blog.
  How to explain it to someone else: "a tool whose entire pitch is confidence-tier honesty has to re-fetch the actual source when the source's status changes from draft to final - the URL looking similar doesn't mean the content is."
- **Concept: "worth checking" can turn into "we know exactly what breaks" once the source gets specific enough.**
  R5 used to flag any hardcoded number in a wide range as a vague heads-up, because no source named a specific number (the project's own rule: guessing is worse than not checking). The final changelog's error-code allocation policy changed that: it names exactly four codes as renumbered and explicitly grandfathers the rest of the range as safe. That turned a broad, low-confidence rule into a narrow, high-confidence one - fewer lines flagged, but every one now backed by an exact before/after number instead of a shrug.
  How to explain it to someone else: "the fix for an overbroad rule is sometimes better information, not more code."
- **Concept: the same investigation method that caught R1's bug is what makes new rules safe to add.**
  Before writing R6/R7/R8, the same discipline from earlier today (install the real pre- and post-update SDK, check what's actually there) was applied to all five SEP-2575 backlog candidates first. It found three genuine, low-false-positive signals - `event_store` as a constructor kwarg (R6), and two decorator methods, `subscribe_resource`/`unsubscribe_resource` (R7) and `set_logging_level` (R8), all confirmed present in the old SDK and confirmed *absent* from the new one's low-level `Server` class entirely. It also found two candidates (the `initialize` handshake, `server/discover`) with no equivalent public hook in either SDK version at all - handled internally, nothing for a developer to have written custom code against. Both were left unimplemented rather than guessed at, matching R3's own precedent.
  How to explain it to someone else: "an app-code-visible signal isn't something you assume exists because the spec changed - you go find it, and sometimes the honest finding is that it doesn't exist."
- **Concept: two rules using the same method name can each be right about a different fact.**
  R4's original match list included `set_logging_level`, assumed (never checked) to be something a tool calls to consume the Logging capability. Checking the real SDK showed `set_logging_level` is never a method on `ServerSession` (the object app code actually holds) - it only exists as the low-level `Server`'s decorator for *registering the removed request handler*. That's R8's fact, not R4's. Removing it from R4's match set and giving it to R8 alone means the two rules can never conflate a 12-month-grace-period deprecation with a request that's already gone - exactly the confidence-tier-honesty bug this project's own review standard exists to catch.
  How to explain it to someone else: "if a rule's match list has a name in it 'because it sounds related,' that's the same unverified-assumption smell that caused R1's bug - go check which real object actually has that method before trusting the list."
