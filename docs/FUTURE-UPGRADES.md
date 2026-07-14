# Future Upgrades — the expanded list

This is the detailed version of `docs/PRD.md` Section 11 ("What might we add later?").
The PRD keeps the short version; this document is where the detail lives, so PRD Section 11 doesn't get overloaded.
Nothing here is being built now.
Per this repo's rule, we only invest more time once the shipped v1 tool shows real interest — stars, installs, people asking about it.

Written in the same style as the rest of this project's docs: short sentences, one idea at a time, and any technical term explained the first time it shows up.

---

## Terms used in this doc

- **Version hop:** the gap between one dated spec version and the very next one (for example, 2025-11-25 to 2026-07-28). MCP's rulebook is versioned by date, and each hop has its own list of changes.
- **Cumulative diff:** adding up the changes across *more than one* version hop, instead of just one. If a server is two hops behind, a cumulative diff tells it about both hops' worth of changes, not just the most recent one.
- **SEP (Spec Enhancement Proposal):** explained in the PRD glossary — MCP's own process for proposing and reviewing a rulebook change before it's accepted, similar to an "RFC" in other open-source projects.
- **CI/CD (Continuous Integration / Continuous Deployment):** automated pipelines that run checks (like tests, or this tool) every time code is pushed, before it's allowed to merge or ship.
- **Extension:** an optional add-on feature to MCP that isn't part of the core rulebook, but that a server and client can agree to use together (already defined in the PRD glossary — repeated here since it comes up below).

---

## 1. Multi-version cumulative diff detection

**What it is:** right now (v1), this tool assumes the server it's scanning is already built against the current stable spec version, 2025-11-25, and only checks the single hop from there to the 2026-07-28 draft (see PRD Section 3).
A more complete version would first figure out which spec version a server is *actually* on, then apply every version hop's rules between that version and the target version — not just the last one.

**Why this matters:** a server that's still on an older version (say, 2025-06-18) would get a report today that's misleading — it would look "clean" for changes it hasn't even caught up to yet, because those changes were introduced in an earlier hop this tool doesn't know about.

**Why this wasn't v1 scope:** this is a meaningfully bigger project than a single-hop checker, for two separate reasons:

1. **It needs a rule set per version-pair, not one rule set.** Today's rule set only describes one hop's worth of changes. A cumulative-diff tool needs a separate, maintained rule set for *every* hop in MCP's version history, and needs to keep adding a new one every time MCP ships a new version. That's an ongoing maintenance commitment, not a one-time build.
2. **It needs version-detection logic that doesn't exist yet.** The tool would have to figure out, just by reading someone's code, which spec version they're actually targeting — which is its own hard problem (a server might not declare its target version anywhere obvious in code), separate from the rule-matching problem this tool already solves.

Both of those are realistically bigger than the ~10-hour budget for this project's first version. A cumulative-diff mode is the single biggest "if this tool takes off, do this next" item.

---

## 2. Promoting today's watch-list items into real rules

PRD Section 4.2 lists SEPs (SEP-2575, the SEP-2663/SEP-2557 tasks discrepancy, SEP-2322) that describe likely-real changes, but that weren't safe to build rules against right away — either because the underlying proposal hadn't merged yet, or because which exact SEP number is the right citation is still unclear.

**Update:** SEP-2575 is now confirmed merged (see PRD Section 4.2's correction note). Its mechanisms — the removed `initialize`/`notifications/initialized` handshake, `server/discover`, `subscriptions/listen`, the removal of `ping`/`logging/setLevel`/`notifications/roots/list_changed`, and removal of SSE stream resumability — are now legitimate Confirmed rule candidates, the same confidence tier as R1-R3.

**Decided 2026-07-14:** these five stay out of v0.1.0. R1-R5's existing estimates already sum to ~11h against the ~10h budget (NOTES.md, LOG.md), so adding five more mechanisms wasn't realistic for this weekend's ship. Each is filed as its own backlog issue (`stretch` label, no milestone), not dropped: [#22](https://github.com/Softogram/softogram-mcp-spec-migration-checker/issues/22) (initialize handshake), [#23](https://github.com/Softogram/softogram-mcp-spec-migration-checker/issues/23) (`server/discover`), [#24](https://github.com/Softogram/softogram-mcp-spec-migration-checker/issues/24) (`subscriptions/listen`), [#25](https://github.com/Softogram/softogram-mcp-spec-migration-checker/issues/25) (`ping`/`logging.setLevel`/`roots.list_changed` removal), [#26](https://github.com/Softogram/softogram-mcp-spec-migration-checker/issues/26) (SSE resumability removal). The same "becomes a real candidate once merged" logic still applies to SEP-2322's `resultType` field, which remains unconfirmed as of this writing.

**A related note on R4's scope, spotted on a later changelog re-read:** the official changelog describes SEP-2322 (Multi Round-Trip Requests) as replacing the old way of sending server-initiated requests for `roots/list`, `sampling/createMessage`, **and `elicitation/create`**. R4 today only checks for three features — Roots, Sampling, Logging — and doesn't mention Elicitation at all. Once SEP-2322 is stable enough to build against, R4 (or a new sibling rule) should likely be widened to also flag old-style `elicitation/create` usage, not just Roots/Sampling/Logging. Not actionable yet, since it depends on the same SEP-2322 stability question above — recorded here so it isn't rediscovered from scratch later.

This should happen as part of the same July 28 correction pass that PRD Section 11 item 1 already calls for — it's not a separate initiative, just a specific checklist item within that pass.

---

## 3. New rule candidates already spotted in the current changelog

While reviewing the full official changelog (everything listed between the 2025-11-25 spec and the 2026-07-28 draft, not just the items already in PRD Section 1), a few more concrete, citable changes stood out as good future rule candidates. None of these are built in v1 — they're recorded here so they don't have to be rediscovered later.

- **Missing `ttlMs`/`cacheScope` on list results.** The changelog requires a new `CacheableResult` shape — a `ttlMs` (a freshness hint, in milliseconds, saying how long a response can be cached) and a `cacheScope` (`"public"` or `"private"`, saying whether shared caches are allowed to reuse the response) — on the results of `tools/list`, `prompts/list`, `resources/list`, `resources/read`, and `resources/templates/list`. A server that doesn't return these fields on those five methods is a strong future rule candidate. **Why not v1:** this needs its own matcher logic and its own fixtures, and wasn't part of the five rules already scoped and estimated for this week's 10-hour budget.
- **Removal of `notifications/elicitation/complete` and `elicitationId`.** Both are removed under the changelog's rules. A server using the "URL mode" elicitation pattern (asking a user to complete something via a link) that still sends or expects either of these would break. A future rule could specifically look for that pattern. **Why not v1:** elicitation is a narrower, less commonly used feature than sessions or handles, so it was left out of this week's five must-have rules by design (see NOTES.md's cut line).
- **HTTP+SSE transport, now fully Deprecated.** This transport was already soft-deprecated before; the changelog now formally reclassifies it as Deprecated under MCP's own feature lifecycle policy. A future rule could flag any server still using this older transport (instead of Streamable HTTP) as "worth checking," pointing at the migration path. **Why not v1:** the tool's current rules don't yet look at *which transport* a server uses at all, beyond the stdio-vs-web distinction R3 already needs (see HLD 001) — a transport-identity rule is a reasonable next rule to build once that detection logic already exists for R3.
- **`includeContext` values `"thisServer"`/`"allServers"`, now Deprecated.** These two specific string values (used when a server asks for extra context) are reclassified from soft-deprecated to Deprecated. A future rule could look for literal use of either string. **Why not v1:** a narrow, low-blast-radius pattern compared to the five rules already scoped.
- **A specific, numbered fix for R5's biggest gap.** PRD Section 9 currently says: "no source confirms the specific number yet" for hand-written MCP error numbers, and lists guessing the exact number as explicitly out of scope. The changelog we reviewed while writing this document actually does name specific numbers: the resource-not-found error code changes from `-32002` to `-32602`, and a new allocation policy renumbers `HeaderMismatch` from `-32001` to `-32020`, `MissingRequiredClientCapability` from `-32003` to `-32021`, and `UnsupportedProtocolVersion` from `-32004` to `-32022`. **This is worth the project owner's attention directly, not just a future-upgrade note** — it may mean R5 (currently "Reported," described only in general terms) can be tightened into a more specific, still-Confirmed rule sooner than expected, since these numbers are named on the same official changelog page the rest of the "Confirmed" rules cite. This document isn't the place to make that call unilaterally, since it wasn't one of the three changes requested for this pass — flagging it here, and in the session's summary, so the project owner can decide whether to fold it into R5 now or treat it as its own future item.
- **Deterministic ordering for `tools/list`.** The changelog adds a **SHOULD** (not a strict requirement) that servers return tools from `tools/list` in a consistent order, to help with caching and prompt-cache hit rates. This is a code-quality nice-to-have, not a breaking change — lowest priority of everything on this list, and arguably not even a "will break" or "worth checking" candidate, more a "worth mentioning" one.

---

## 4. TypeScript MCP server support

**What it is:** support scanning MCP servers written in TypeScript, using the official TypeScript MCP SDK, the same way v1 supports Python servers using the official Python SDK.

**Why this wasn't v1 scope:** this project's tool reads code using Python's own `ast` module, which only understands Python. Supporting TypeScript means a whole second parsing approach and a second set of matchers per rule — not a small addition, a second version of the core engine. Matching the audience's own language (Python developers today) was judged more valuable for a first version than partial support for two languages (see PRD Section 5).

---

## 5. `--json` output and CI/CD pipeline integration

**What it is:** a `--json` flag so the report can be read by other programs (not just a person reading a terminal), plus a small helper or example config for wiring this tool into a CI/CD pipeline like GitHub Actions, so a team can fail a pull request automatically when something "will break."

**Why this wasn't v1 scope:** `--json` is already a "nice to have, only if time allows" item in this week's plan (PRD Section 8) — genuinely useful, just not required for the tool to prove its core idea works. Official CI/CD integration is a further step past that: someone can already wire the existing command-line tool into their own pipeline today using its exit code (PRD Section 8), so building official support is separate, lower-urgency work (PRD Section 9).

---

## 6. Preview-then-auto-fix mode, in that order

**What it is:** two future modes, meant to be built one after the other, never the second one first:

1. **Preview mode** — shows exactly what change it would make to fix a finding, without actually changing the file. A safer middle step between "just tell me what's wrong" (what v1 does) and "just fix it for me."
2. **Auto-fix mode** — actually applies the fix, but only once preview mode has been available and trusted for a while.

**Why this wasn't v1 scope, and why the order matters:** automatically rewriting someone's code is risky — a wrong automatic fix could break code that was actually fine. PRD Section 9 already rules out auto-fixing entirely for v1. Preview mode is the safer stepping stone: it lets a developer see and judge a suggested fix before trusting the tool to touch their files directly. Building auto-fix before preview mode has earned trust would skip the exact safety step this idea depends on.

---

## 7. Opt-in, privacy-respecting scan-result sharing

**What it is:** an optional way for people running this tool to agree to share anonymized results of what their scans found — which rules matched, not their actual code — so the rule set itself can improve over time based on real-world usage, not just the handful of example servers this project ships with.

**Why this wasn't v1 scope:** this needs explicit, informed consent, a place to send the data, and a real privacy design — all of which are exactly the kind of accounts-and-hosting complexity this project's rules (`CLAUDE.md`) say to avoid unless a problem specifically calls for it. It's listed here as something to consider only if the tool has real, ongoing usage worth learning from — not before.

---

## Where this fits with the rest of the project's docs

- `docs/PRD.md` Section 11 — the short version of this same list; this document is the expanded version.
- `docs/PRD.md` Section 4.2 — the "watch list" of spec changes this document's item 2 is about promoting.
- `docs/high-level-design/001-scan-pipeline.md` — the current architecture; several items above (multi-version diffing, TypeScript support) would mean real changes to this pipeline, not just new rules.
- `NOTES.md` — this week's actual cut line; nothing in this document is in scope for that.
