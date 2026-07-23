# LLD 001 - Rule Definition Format and Matcher Contract

**Status:** Settled - drafted by Claude at the user's request (per this project's `CLAUDE.md` Section 2 exception), then all four open questions were answered by the user on 2026-07-23.
The answers are recorded in the "Open questions" section at the bottom, which is kept for the record.
**Links:** [HLD 001](../high-level-design/001-scan-pipeline.md) ("Rules are data, matchers are small code" section, and the R3 section) - `docs/PRD.md` sections 4.1, 8 - [GitHub issue #2](https://github.com/Softogram/softogram-mcp-spec-migration-checker/issues/2).
**Last updated:** 2026-07-23

This document uses the same terms as HLD 001's glossary (Rule, Matcher, Finding, Severity, Confidence tier).

Three file-format names show up below, so here is what each one is:

- **JSON** - a plain-text data format using braces and quotes. Python can read it with no extra installs. It does not allow comments.
- **YAML** - a plain-text data format using indentation. Friendly to read, but Python needs a third-party library installed to read it.
- **TOML** - a plain-text data format using named sections and `key = value` lines, like a classic config file. Python 3.11 and newer can read it with no extra installs, and it allows comments.

## Why this LLD exists

HLD 001 already made the one architectural call this project needed: a rule's **metadata** (what it means, how sure we are, where it came from) is kept as data, separate from its **matcher** (the AST-walking logic that finds it).
That split is settled and is not up for debate here.

What HLD 001 did *not* do is nail down the exact shape of either side, or the contract between them.
This document proposes those shapes.
Issue #5 (the scan engine) depends directly on this, and every rule issue (#7-#11) depends on it through #5.

## What's already decided (not open for re-discussion here)

Carried over from HLD 001, treated as fixed constraints:

- Metadata is data; matchers are small code. A fully declarative rule format was already rejected.
- No plugin system for third-party rules.
- The engine must have zero rule-specific knowledge. Adding or removing a rule must only ever touch the rule set, never engine code.
- Everything the reporter prints (severity, confidence, explanation, source link) must come from metadata.
- A finding carries: rule ID, file, line number, and the matched source line's own text (one line, not a multi-line block).
- R3's three-outcome behavior: confidently web-exposed and non-compliant means "This will break"; confidently local-only means silence; can't tell means a distinct `NEEDS-MANUAL-CHECK` outcome that is not a severity and not a confidence tier, never affects the exit code, and is never rendered next to "Worth checking."

## Proposed design

### 1. The metadata field set

Every rule is described by exactly these fields.

| Field | What it holds | Example (described, not literal) |
|---|---|---|
| `id` | Short stable code for the rule. This is the key that links the metadata to its matcher, appears in the report, and would be the argument to a future `--explain` flag. | R1 through R5 |
| `title` | One-line human name for the rule, used as the heading of a finding. | "Old-style session usage" |
| `severity` | What happens if the reader ignores this finding. Exactly one of two allowed values: the will-break value or the worth-checking value. This is what drives the exit code. | will-break |
| `confidence` | How sure we are that the rule describes a real spec change (PRD 4.1). Exactly one of two allowed values: confirmed or reported. This drives the confidence label in the report. | confirmed |
| `explanation` | A plain-language paragraph: what pattern was found, why it breaks or might break, and what to do about it. | a few sentences of prose |
| `source_url` | The link that proves the rule: the spec section, changelog entry, or SEP it came from. | a URL into the MCP spec |
| `source_checked` | The date (YYYY-MM-DD) someone last verified the source still says what the rule claims. | 2026-07-14 |
| `manual_check_text` | Optional. Only present on rules whose matcher can return the "cannot tell" outcome (R3 is the only such rule in the MVP). This is the exact text printed for a `NEEDS-MANUAL-CHECK` result. | a short paragraph telling the reader what to check by hand |

Two deliberate calls inside this table:

- **Severity and confidence stay two separate fields, even though the MVP pairs them one-to-one** (both Confirmed rules are will-break, both Reported rules are worth-checking).
  They answer different questions: severity is about impact on the reader's server, confidence is about the quality of our source.
  Collapsing them into one field would bake today's coincidence into the format, and the July 28 final spec could easily produce a rule that is confirmed by the spec but only worth checking in practice.
  A side benefit for honesty: any promotion of a rule (say, worth-checking to will-break) is a visible one-line change to the rules file in version control, never a hidden code change.
- **R3's skip condition does not live in metadata.**
  Deciding whether a server is web-exposed is matching logic, so it lives in R3's matcher code.
  Only the *text* shown for the cannot-tell outcome lives in metadata (`manual_check_text`), which keeps the "everything printed comes from metadata" guarantee intact.

### 2. Storage format and location

**Proposal: one TOML file named `rules.toml`, shipped inside the installed package, with one named section per rule.**

Why TOML:

- Python 3.11+ reads it with the standard library, so it adds no dependency.
- It allows comments, so the rules file can carry notes like "re-verify this section after July 28" right next to the rule they belong to.
- Multi-line text (the `explanation` paragraphs) is natural to write in it.
- A reviewer who knows no Python can still open the file and audit every rule's claim and source link, which is the whole point of rules-as-data.

Why not the alternatives:

- **YAML** - needs a third-party library. One extra dependency buys nothing TOML doesn't already give us.
- **JSON** - no comments, and paragraph-length explanations inside quoted strings are painful to write and review.
- **A Python file holding plain data structures** - zero parsing work, but it blurs the exact line this architecture exists to draw. A rules file that is code invites logic to creep into it, and a non-Python reader can no longer audit it.

The file is read once at startup.
Loading validates every rule and stops the program immediately with a clear message naming the offending rule if anything is wrong: a missing required field, a value outside the allowed severity or confidence lists, a duplicate id, or an unparseable date.
Failing fast here is what makes the rules file trustworthy: a typo in the data can never silently become a wrong label in a report.

Cost of this choice: the tool requires Python 3.11 or newer.
That is open question 1 below.

### 3. Matcher registration contract

**Proposal: one small matcher function per rule, one module per rule, connected by one explicit registry table.**

The shape, in words:

1. Each rule's matcher is a single function living in its own small module inside a rules package (one file per rule, named after the rule).
2. The rules package also holds one plain lookup table mapping each rule id to its matcher function. This table is the registry. It lives with the rules, not with the engine.
3. At startup, the engine loads `rules.toml`, then cross-checks it against the registry in both directions: a rule with no matcher, or a matcher with no rule, stops the program immediately with a message naming the id.
4. During a scan, for each Python file, the engine hands every matcher the same bundle: the file's path, the file's parsed AST, and the file's source text split into numbered lines.
5. The matcher hands back its answer for that one file (shape defined in section 4).
6. The engine assembles findings by combining the matcher's answer with the rule's metadata. Matchers never produce any text that gets printed.

Adding a hypothetical rule R6 therefore touches exactly three places, all in rule territory: a new section in `rules.toml`, a new matcher module, and one new line in the registry table.
The engine and the reporter are untouched, which is the auditability guarantee made mechanical.

Why an explicit table instead of the two common alternatives:

- **Decorator self-registration** (each matcher tags itself and a registry fills up as modules get imported) was rejected.
  It depends on import order and import side effects, which are exactly the kind of invisible machinery that confuses a new contributor, and there is no single place to see the whole rule list at a glance.
- **Filename-convention discovery** (engine scans a folder and wires files to rules by name) was rejected for the same reason: magic that saves five lines and costs every future reader a debugging session when a rename silently unwires a rule.

For a five-rule tool, one visible table read in one glance is the boring, robust choice.

### 4. The matcher's answer, including "cannot tell"

**Proposal: a matcher's answer for one file is one of two things.**

- **The normal answer: a list of raw matches, possibly empty.**
  A raw match is just a line number.
  The engine looks up that line's own text from the source lines itself, so the settled one-line snapshot shape is enforced in exactly one place, and no matcher can accidentally attach a multi-line block.
  An empty list simply means "this rule found nothing in this file", which is also how a rule stays silent when it does not apply (R3 on a confidently local-only server returns an empty list).
- **The exceptional answer: a single cannot-tell marker.**
  Returning this means "for this rule, in this file, a human has to look" and produces a `NEEDS-MANUAL-CHECK` outcome.
  The engine handles it generically for any rule: it renders it in its own report section using the rule's `manual_check_text`, it never contributes to the exit code, and it never appears next to the Worth-checking tier.
  If a matcher returns this marker but its rule has no `manual_check_text` in the metadata, that is a fail-fast error, because otherwise the engine would have to invent text, breaking the metadata-only-printing guarantee.

This shape answers the sharpest question from the problem statement: the third outcome is part of the *general* contract, so the engine needs zero rule-specific knowledge, but it is *optional to use*, so R1, R2, R4, and R5 stay dead simple - they return hit lists and never think about it.

### 5. The auditability guarantee, made concrete

Restating the mechanics that deliver the two promised guarantees:

- **"Adding or removing a rule never touches engine code"** holds because the only three touch points (metadata section, matcher module, registry line) all live in the rules package, and the startup cross-check proves the three stayed in sync.
- **"Everything printed comes from metadata"** holds because a matcher's entire vocabulary is line numbers plus one flag.
  A matcher physically has no channel through which to supply a severity, a confidence label, an explanation, or a link.
  A rule can only be promoted by editing the rules file, which is a visible data diff in version control.

The test harness (issue #6) should include one test that asserts the startup cross-check itself: every rule in `rules.toml` has a registered matcher and vice versa.
That turns the guarantee from a convention into something CI can refuse to break.

## Open questions - now settled (answers recorded 2026-07-23)

1. **Python floor: settled at Python 3.11 minimum, developed and tested on the latest release.**
   The user deferred on this one ("latest is fine, no hard feelings"), so the floor was set by engineering reasoning: 3.11 is the lowest version whose standard library reads TOML, and nothing else in the design needs anything newer.
   A migration checker wants the widest audience that costs nothing to support; requiring the newest Python as a *minimum* would only shrink who can install it.
2. **Severity/confidence pairing: left free.**
   User confirmed the proposal.
   No validation ties confirmed to will-break; a promotion remains a visible one-line data diff in version control.
3. **Per-file sight for R3: accepted for v0.1.0.**
   User confirmed the per-file contract is acceptable; the cannot-tell outcome is the pressure valve when transport evidence lives in a different file.
   R3's final shape is still gated on issues #20 (detectability) and #21 (signal order) - this answer settles the *contract*, not R3 itself.
4. **Raw match as a bare line number: confirmed.**
   Keep the sanity check when writing R2's matcher; if a rule ever needs to point at a specific name within a line, that is a contract change to raise before, not after, #5 freezes it.

## Who's waiting on this

Directly blocked and now unblocked: issue #5 (scan engine).
Transitively: issues #7-#11 (the five rules), with #9 (R3) as the hardest test of the contract, plus #6 (test harness conventions).

## Next step

Settled.
Issue #5 (scan engine) and issue #4 (scaffold) can start.
The remaining design work before rules R1-R5 is issue #3 (finding model, report layout, exit codes) and, for R3 only, issues #20/#21.
