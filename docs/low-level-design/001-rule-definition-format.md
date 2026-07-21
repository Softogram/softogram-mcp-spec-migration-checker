# LLD 001 - Rule Definition Format and Matcher Contract

**Status:** Problem statement only - no solution yet. The user proposes the design next (per this project's `CLAUDE.md` Section 2); Claude's job here was to lay out the requirement clearly, not answer it.
**Links:** [HLD 001](../high-level-design/001-scan-pipeline.md) ("Rules are data, matchers are small code" section, and the R3 section) - `docs/PRD.md` sections 4.1, 8 - [GitHub issue #2](https://github.com/Softogram/softogram-mcp-spec-migration-checker/issues/2).
**Last updated:** 2026-07-14

This document uses the same terms as HLD 001's glossary (Rule, Matcher, Finding, Severity, Confidence tier). No new terms are needed yet.

## Why this LLD exists

HLD 001 already made the one architectural call this project needed: a rule's **metadata** (what it means, how sure we are, where it came from) is kept as data, separate from its **matcher** (the AST-walking logic that finds it). That split is settled and is not up for debate here - re-opening it is explicitly out of scope (see "What's already decided" below).

What HLD 001 did *not* do is nail down the exact shape of either side, or the contract between them. It described the idea in prose ("the engine hands a matcher one file's AST, the matcher hands back zero or more raw matches: line + context") without specifying concrete fields, a file format, or a registration mechanism. That gap is this issue.

This matters beyond tidiness: issue #5 (the scan engine) depends directly on #2, and every one of the five rule issues (#7-#11) depends on #2 through #5. Nothing rule-related can start until this is settled - it's the first real bottleneck in the build order.

## What's already decided (not open for re-discussion here)

Carried over from HLD 001, and treated as fixed constraints on whatever gets designed in this doc:

- Metadata is data; matchers are small code. A fully declarative rule format (patterns described in a config language, no matcher code) was already rejected - it would mean inventing and maintaining a pattern mini-language, a bigger project than this whole tool.
- A plugin system for third-party rules was already rejected - out of scope for a 10-hour build.
- The engine must have zero rule-specific knowledge. Adding or removing a rule must only ever touch the rule set, never engine code.
- Everything the reporter prints (severity, confidence, explanation, source link) must come from metadata. The reporter never looks anything up itself, rule by rule.
- A finding carries: rule ID, file, line number, and the matched source line's own text (one line, not a multi-line block) - settled in the prior LLD session.
- R3 already has a settled three-outcome shape at the *behavior* level (HLD 001's "R3: transport detection" section): confidently web-exposed and non-compliant -> "This will break"; confidently local-only -> silently correct (no finding); can't tell -> a distinct `NEEDS-MANUAL-CHECK` outcome that is not a severity and not a confidence tier, and must never affect the exit code or get rendered next to "Worth checking."

Whatever this LLD settles has to make all of the above true in practice, not just in prose.

## The five things this LLD must actually answer

1. **Exact metadata field set.**
   HLD 001 lists, in prose: ID, short title, severity, confidence tier, plain-language explanation, source URL, and the date the source was last checked. This LLD needs to turn that into a concrete, exhaustive field list - names and what each one holds - and confirm it's genuinely enough for all five MVP rules, not just the easy ones. R3 is the test case: does its skip condition and its `NEEDS-MANUAL-CHECK` outcome live in this same metadata, or somewhere else entirely? That's not yet decided.

2. **Storage format and location.**
   HLD 001 settled *that* metadata lives in "one dedicated rules file, separate from the engine." It did not settle *what format* that file is written in (a plain Python data structure, YAML, JSON, TOML, something else) or its exact path in the package. This is a narrower question than the already-rejected "declarative pattern language" debate - it's about how to serialize plain facts (a string, a URL, a date), not about expressing matching logic - and shouldn't be allowed to reopen that rejected alternative.

3. **Matcher registration contract.**
   How does a piece of matcher code declare "I am the matcher for rule R3"? And what exactly does the engine hand it, and what exactly does it hand back? HLD 001's "line + context" description is prose, not a contract - this LLD needs to pin down the actual shape of a raw match, and how a matcher is discovered and wired to its rule ID without the engine needing to know rule names in advance.

4. **How a rule expresses "not applicable here."**
   This is the sharpest open question, and it's R3-specific in origin but general in consequence. A matcher can't just return "matches" or "nothing" - R3 needs a third possible outcome (can't tell -> `NEEDS-MANUAL-CHECK`), already fixed at the behavior level in HLD 001. The open question is where that third outcome is expressed in the *contract*: as a special value a matcher can return, as a property of the match itself, or some other shape - and whether that capability is something every rule's matcher has to know about (even the four rules that will never use it), or something that only applies where a rule actually needs it. Getting this wrong either forces unnecessary complexity onto R1/R2/R4/R5, or hides a special case inside the engine - both of which would break the "engine has zero rule-specific knowledge" guarantee above.

5. **The auditability guarantee, made concrete.**
   "Adding or removing a rule never touches engine code" and "everything printed comes from metadata" are guarantees HLD 001 already promises. This LLD's chosen format and contract have to actually deliver them - if confidence, severity, or source link end up split between the metadata file and matcher code in a way the reporter has to reassemble, the guarantee is broken even if nobody intended it to be.

## Who's waiting on this

Directly blocked: issue #5 (scan engine). Transitively blocked through #5: issues #7-#11 (the five rule implementations), with #9 (R3) as the hardest test of whatever gets decided here, since it's the only rule that needs point 4 above. Also relevant to #6 (test harness/fixture conventions), since how a fixture asserts "this matcher returned exactly these matches" depends on the shape settled here.

## Next step

The user proposes the design - field list, file format, registration mechanism, and the applicability answer - and Claude's role from here is to ask questions and push back, not to draft the answer (per `CLAUDE.md` Section 2, unless asked otherwise).
