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
