# PRD — MCP Spec Migration Checker

**Project:** `softogram-mcp-spec-migration-checker`
**Track:** A — Deep Build (Week 1, Jul 13–19, 2026)
**Status:** Draft — scoping complete, build not yet started
**Owner:** Softogram (solo)
**Build budget:** ~10 hours, this week only (see `CLAUDE.md`)
**Last updated:** 2026-07-14

This document explains what we're building, why, and how — written so someone new to AI or software engineering can follow along and contribute. Technical words are explained the first time they show up. There's also a glossary below you can jump back to.

---

## Glossary (look here if a word is unfamiliar)

- **MCP (Model Context Protocol):** an open standard (a shared rulebook) that lets AI apps and AI agents connect to outside tools, files, and data in a consistent way. Think of it like a USB port for AI — any tool that follows the MCP rulebook can plug into any AI app that also follows it.
- **Spec (specification):** the actual written rulebook for MCP — what a program must do to correctly "speak MCP."
- **RC (Release Candidate):** a near-final draft of the next version of the rulebook. It's expected to become official soon, but small details could still change.
- **Server (MCP server):** a program that offers tools/data to an AI app, following the MCP rulebook.
- **Client:** the AI app (or the part of it) that talks to an MCP server.
- **Breaking change:** a change to the rulebook that makes old code stop working correctly unless it's updated.
- **Session:** in the old rulebook, a way for the server to "remember" who it's talking to across multiple messages, using an ID.
- **Handle:** a plain, visible reference to something (like an ID for a shopping basket) that gets passed back and forth on purpose, instead of being hidden inside a session.
- **Capability:** something a server says it can do (e.g. "I can search files"). Servers announce their capabilities when a client connects.
- **Extension:** an optional add-on feature that isn't part of the core rulebook, but that a server and client can agree to use together.
- **Stateless:** doesn't rely on "remembering" anything between separate messages — each message stands on its own.
- **AST (Abstract Syntax Tree):** a structured, tree-shaped map of a program's code that a computer can read and understand, instead of just reading it as plain text. Our tool uses this to reliably find patterns in code.
- **Static analysis:** checking code by reading it, without actually running the program. Opposite of testing a program while it's live.
- **CLI (Command Line Interface):** a tool you use by typing a command into a terminal, instead of clicking buttons in an app.
- **SDK (Software Development Kit):** a ready-made code library that helps developers build something (here, an MCP server) without writing everything from scratch.
- **SEP (Spec Enhancement Proposal):** MCP's own process for proposing and discussing a rulebook change before it's accepted — similar to how many open-source projects use an "RFC" (Request for Comments) to debate a change first. Each SEP has a number and a GitHub pull request where the discussion happens. A SEP being **merged** means the proposal was actually accepted into the spec; "open" or "in review" means it's still being debated and could still change shape before it's final.

---

## 1. What problem are we solving?

MCP (explained above) is getting a big rulebook update. The update is dated **2026-07-28**, and a near-final draft (the "RC") was locked on **May 21, 2026**. That gives everyone about ten weeks to check their code before the update becomes official.

This update changes some fundamental things, and code written for the old rulebook can break. Based on the official changelog (the page that lists exactly what changed — see [source](https://modelcontextprotocol.io/specification/draft/changelog)):

- **Sessions go away.** Servers used to "remember" a client using a session ID. That's removed. Every message now has to carry everything it needs on its own.
- **Server memory has to become a visible handle.** If a server needs to remember something (like "which shopping basket is this?"), it now has to hand back a plain, visible ID (a handle) that gets passed along in later messages — instead of hiding that memory inside a session.
- **Two new HTTP headers are required on every web-based request.**
  A header is a small labeled piece of information a computer sends alongside a request, before the main content of the message.
  The two new required headers are `Mcp-Method` (which method is being called) and `Mcp-Name` (which specific operation within it).
  This helps tools like load balancers (traffic-routing software) make smarter decisions.
  The official changelog scopes this specifically to **Streamable HTTP POST requests** — the transport used by web-reachable servers. It does not apply to servers that only run locally over stdio (explained in Section 4).
- **A new "extensions" option was added**, so servers can offer optional features beyond the core rulebook.

Other sources close to MCP's governing body (the Agentic AI Foundation, part of the Linux Foundation) and independent trackers also describe more changes as part of the same update: three older features (Roots, Sampling, Logging — explained: ways for servers to declare folders, ask the AI to run a quick calculation, and send log messages) are being marked as "on their way out" (with a year's grace period before anything actually stops working), a new way to handle long-running tasks, a new way for servers to show interactive visual interfaces, and stricter login/security rules. These aren't yet shown on the single official "what changed" page we checked, so we treat them as less certain (more on that in Section 4.1).

**Who is this for:** developers (or small teams) who run or build an MCP server written in Python, using the official MCP Python SDK. For this first version, we're only supporting that group (see Section 3).

**Why build this now:** the deadline is real and close, and the draft is locked (unlikely to change much before it becomes official). That's the kind of honest urgency worth building something for.

## 2. What are we trying to achieve? (Goals)

- Let a developer run one simple command and get a plain-language list of what in their code will likely break, and what to do about it.
- Make it fast to try — from installing it to seeing a first report in under 5 minutes, no setup required for the common case.
- Be honest about how sure we are. Some findings come straight from the official rulebook change list (very sure). Others come from articles describing the update more broadly (less sure, still useful, but labeled differently). The tool should never present a "maybe" as a "definitely."

## 3. What this tool will NOT do (yet)

Being clear about what we're skipping is just as important as what we're building — it keeps the first version realistic for a 10-hour project.

- It won't rewrite anyone's code automatically. It only reports problems; a person still decides what to change.
- It won't check anything beyond this one rulebook update. It's not a general code-quality tool.
- It won't run the server and test it live. It only reads the code (static analysis, explained above).
- It only understands Python code using the official MCP Python SDK. Not TypeScript, not other MCP toolkits — yet.
- It's not a website or hosted service. It's a command-line tool you run yourself. No accounts, no sign-up, nothing sent anywhere by default.
- It can't promise it's 100% correct against the final rulebook, since the official update isn't published yet at the time we're building this (see Section 12, Risks).
- It only checks **one hop** of the rulebook's version history: from the current stable version (**2025-11-25**) to the draft version (**2026-07-28**). It assumes the server being scanned is already built against 2025-11-25. It does not detect which spec version a server is actually on, and it does not add up the changes across multiple version hops. A server still on an older version (for example, 2025-06-18) would need to upgrade to 2025-11-25 first — using MCP's own version history — before this tool's findings reliably apply to it. This is a deliberate scope cut, not a bug (see Section 12 and `docs/FUTURE-UPGRADES.md`).

## 4. How will it work? (Solution Overview)

It's a small command-line tool, written in Python, that you install and then point at a folder of code:

```
mcp-migration-check ./my-server
```

Here's what happens, step by step:

1. **It reads your Python code as a tree, not as plain text.** This is the AST (explained in the glossary) — a much more reliable way to find patterns in code than just searching for text, because it understands the actual structure of the program.
2. **It looks for specific patterns**, such as:
   - Code that reads or stores a session ID, or keeps a "memory" tied to a session instead of passing an explicit handle.
   - Server code that stores information in a way that assumes the old "remembered session" model, instead of the new "explicit handle" model.
   - Web-server code that doesn't yet expect the two new required headers, `Mcp-Method` and `Mcp-Name`, mentioned in Section 1 (this check only applies to servers reachable over the web using the Streamable HTTP transport — not to servers that only run locally over stdio). When the tool genuinely cannot tell which kind of server it's looking at, it says so plainly instead of guessing (see Section 4.1).
   - Use of the three features that are reportedly being phased out (Roots, Sampling, Logging).
   - Code that checks for specific error numbers from MCP by hand (which might change).
3. **Each pattern found gets a label**, explained next in Section 4.1: definitely breaking, worth a second look, or looks fine already.
4. **It prints a simple report in the terminal** — organized by file, with a plain-English explanation for each finding, how sure we are about it, and a link to where that information came from.
5. **It comes with one real example** in the project: a small sample MCP server written the old way, this tool's report on it, and the same server rewritten the new way with a clean report. That's a real, working example — not just a made-up demo.

### 4.1 How sure are we about each rule?

Because the official rulebook isn't fully finalized yet, we're careful not to overstate our confidence. Every check we run is labeled with how sure we are:

| Confidence label | What it means | What we call it in the report | Where it came from |
|---|---|---|---|
| **Confirmed** | It's listed on the official "what changed" page | "This will break" | [Official MCP changelog](https://modelcontextprotocol.io/specification/draft/changelog) |
| **Reported** | Described by trusted sources close to MCP, but not yet on that one official page | "Worth checking, not 100% certain" | [Agentic AI Foundation blog post](https://aaif.io/blog/mcp-is-growing-up/), [independent builder's guide](https://chatforest.com/builders-log/mcp-spec-2026-07-28-release-candidate-stateless-breaking-changes-builder-guide/) |
| **Known unknown** | Mentioned as changing, but the exact detail isn't confirmed anywhere yet (example: "an error number changes" without saying which one) | Not checked for in version 1 — mentioned in the README instead | Independent trackers |

We'd rather tell a developer "we're not 100% sure, please double-check" than confidently say something is broken when we only read about it secondhand. Keeping this list of rules separate from the rest of the program (in its own file) also means that once the official rulebook is fully published on July 28, we can update just that list — not rewrite the whole tool.

**A separate, fourth thing a finding can say: "we couldn't tell if this applies to you."**
This is different from the confidence labels above.
Confidence (Confirmed vs. Reported) is about how sure we are that a *rule itself* is real and correctly describes the spec change.
This new case is about something else: whether a *specific rule* even applies to *your* server at all.

The only rule where this comes up in version 1 is the web-vs-local check (Section 4, item 3).
The tool can usually tell whether a server is reachable over the web or only runs locally — but not always.
When it genuinely can't tell, it says so directly — "we couldn't determine this — please check by hand" — rather than either staying silent (which could let a real problem through unnoticed) or guessing (which could wrongly tell someone their code is broken when it isn't).
This "can't tell" case is shown clearly in the report, kept visually separate from "worth checking," and never treated as "this will break" — it does not cause the tool's error exit code (Section 8) to trigger.

### 4.2 Changes we're tracking but not building into v1 yet (the watch list)

None of the rows below are active rules in version 1.
This is a checklist to revisit specifically before the July 28 correction pass (Section 11, item 1) — a reminder of what to re-check once the real rulebook ships, not something the tool checks for today.

One nuance worth stating plainly first: the SEPs below are all *mentioned* on the official changelog page — our bar for "Confirmed" in Section 4.1.
The draft spec's prose already describes their effects.
But being described in the draft's prose is not automatically the same as the underlying SEP being fully merged and closed out in MCP's own review process on GitHub.
A draft page can be edited while a SEP is still under active discussion.
That's why a SEP stays in this "watch, don't build yet" bucket until its merge status is actually confirmed — we don't want to hard-code a rule against a specific mechanism name that could still change shape.

**Update, still 2026-07-14:** SEP-2575 is now confirmed merged. It's promoted out of the "not yet safe to build" bucket below — see the note directly under the table for what that means for the rule backlog.

| SEP | What it's about | Current GitHub status | Note |
|---|---|---|---|
| **SEP-2575** — "Make MCP Stateless" | The `initialize`/`notifications/initialized` handshake goes away; replaced by `server/discover`, per-request protocol-version/capability info, `subscriptions/listen`, and removal of `ping`, `logging/setLevel`, `notifications/roots/list_changed` | **Merged.** No longer an unmerged watch item — its mechanisms are now legitimate Confirmed rule candidates, same bar as R1-R3. | Kept in this table as a record of the correction (see below), not because it's still uncertain. Decided 2026-07-14: stays out of v0.1.0 — R1-R5 already sum to ~11h against the ~10h budget. Filed as five backlog issues instead (`docs/FUTURE-UPGRADES.md` Section 2 has the links). |
| **SEP-2663 vs. SEP-2557** — the "tasks" change (`tasks/get`, `tasks/update`) | Moving long-running-task handling out of the core protocol and into an official extension | Unresolved — our own research found conflicting SEP numbers cited for this same change in different review comments | Flagged as an open citation discrepancy, not resolved. Needs re-verification directly against GitHub before either number is treated as authoritative. Not urgent for v1 either way — this area is already out of scope per Section 9. |
| **SEP-2322** — Multi Round-Trip Requests (MRTR) / `resultType` | A new pattern for a server to ask a client for more input mid-request, using a `resultType` field | Not yet independently confirmed merged — still treat as unmerged until checked directly | Genuinely its own proposal, not a mislabeled duplicate of the stateless work. Same caution as above still applies: appearing on the changelog page isn't the same as knowing the underlying SEP has fully merged. |

**A correction to what this document said earlier:** an earlier version of this table recorded SEP-2575 as "open / in review, not merged," based on our own research at the time, and separately noted that an automated lookup claiming it was merged shouldn't be trusted, since this project works against a hypothetical future timeline. That automated lookup's conclusion has now been confirmed correct through a different, trusted channel — so the status above is corrected accordingly. The general caution stands for SEP-2322 and the SEP-2663/2557 discrepancy, which remain unconfirmed.

**Update, 2026-07-28 — the final spec published, and the SEP-2575 backlog got its correction pass early.** With the actual final (non-draft) changelog live at `https://modelcontextprotocol.io/specification/2026-07-28/changelog.md`, three of the five SEP-2575 backlog issues turned out to have a real, low-false-positive app-code signal once checked against the real installed `mcp` package (both the pre-update `1.29.0` and the post-update `2.0.0` release) and were implemented as R6 (SSE resumability opt-in via `event_store`), R7 (old `resources/subscribe`/`resources/unsubscribe` handlers), and R8 (old `logging/setLevel` handler). The other two — the removed `initialize`/`notifications/initialized` handshake and the new required `server/discover` RPC — were investigated the same way and found to have **no clean app-code signal at all**: both are handled entirely inside the SDK's transport/dispatch layer for any server built on it, with no public hook a developer would write custom code against, so a rule would either never fire for real servers or would have to guess at hand-rolled dispatch code already covered by R3's theme. Per this project's own rule of not guessing at undetectable patterns (Section 12), no rule was built for either. See `docs/LEARNINGS.md`'s 2026-07-28 entries for the full investigation.

A related correction while doing this pass: the session/handle-removal citation for R1 and R2 is more precisely **SEP-2567**, not SEP-2575 — the changelog attributes the `Mcp-Session-Id` header and protocol-level session removal specifically to SEP-2567, a sibling proposal to the broader stateless-handshake work in SEP-2575. Both rules' metadata now cite the more precise number.

## 5. Why did we build it this way?

**Why read the code instead of running it:** running someone's server would mean handling their passwords, settings, and other dependencies — a much bigger and riskier job than we can do in 10 hours. Reading the code is simpler and safer.

**Why read code as a tree (AST) instead of just searching for text:** plain text search (like using "find" for a word) gets confused easily and gives wrong answers. Reading the code the way a computer actually understands it (as a tree) gives much more reliable results — worth the small extra effort.

**Why Python, not a different language:** the people we're building this for already write their MCP servers in Python. A Python tool installs easily into the same setup they already have. (Our general rule in this repo is to pick a single-file, install-anywhere language like Go or Rust when a tool is meant for a broad audience — but here, matching the audience's own language is more helpful.)

**Why label how sure we are about each rule:** while researching this project, we noticed that the one official "what changed" page doesn't mention everything that other trusted sources say is part of the same update. Rather than pretend we're equally sure about everything, we built in a simple confidence system from the start. It's a small amount of extra work now that avoids giving anyone false confidence later.

**Why a command-line tool instead of a website:** it matches what the people using it already do (they're developers working in a terminal), and avoids extra complexity like accounts or hosting, which this project's rules (see `CLAUDE.md`) say to avoid unless truly needed.

## 6. Who uses this, and how

- A developer running an MCP server that's already live runs the tool once, gets a clear list of what to fix before July 28, labeled by how sure we are.
- A developer starting a brand-new MCP server today runs the tool as they build, so they don't accidentally write code the old way.
- Someone deciding whether to trust this tool can see, right in the report, which findings are backed by the official source and which aren't — and check for themselves.

## 7. Where else can this tool help? (Beyond this one update)

A fair question is whether this tool is only useful for this one, one-time rulebook change. It isn't — here's where else the same idea applies:

- **Every future MCP update, not just this one.** MCP plans to keep updating its rulebook over time (it's versioned by date). The way we've built this tool — with the checking rules kept separate from the rest of the program — means that when the *next* update comes along later, we (or anyone) can add a new set of rules without rebuilding the tool from scratch. This becomes a reusable pattern, not a one-off.
- **Checking a project's health at any time, not just right before a deadline.** A team could run it any time — not just because a deadline is close — to see if their code already has outdated patterns worth cleaning up, the same way people run a spell-checker on a document even when there's no submission due.
- **Checking someone else's code before you depend on it.** If you're about to use an open-source MCP server that somebody else built, you can run this tool against it first to see how ready it is for the upcoming changes, before you build your own project on top of it.
- **A guardrail while a team keeps writing new code.** A team could wire this into their own pre-commit check (a script that runs automatically before code is saved) so they don't accidentally reintroduce old, outdated patterns while several people are working on the same project.
- **A way for Softogram (the agency side of this business) to start conversations with potential clients.** Since Softogram is also a software development agency, this tool doubles as a free, honest way to show a potential client something concrete and useful about their own code — "here's what we found, here's how we'd help fix it" — instead of a cold pitch.
- **A learning tool for people new to MCP.** Because every finding explains what's wrong, why, and links to where that information came from, someone new to MCP can use this tool to actually learn how the protocol works, not just to pass a check.

None of this needs to be built now — it's why Section 11 (Future Upgrade Path) lists "update the rules once the final spec ships" as the top priority whether or not this project gets more time invested in it.

## 8. What exactly are we building this week? (Functional Requirements)

Must have:
- [ ] A command you can run: `mcp-migration-check <path>` (checks the current folder if no path is given)
- [ ] A check for old-style session usage → labeled "This will break" (Confirmed)
- [ ] A check for server memory that isn't using the new visible-handle style → labeled "This will break" (Confirmed)
- [ ] A check for web-server code missing the two new required headers, `Mcp-Method` and `Mcp-Name` → labeled "This will break" (Confirmed) — skipped for servers that only run locally over stdio, since this rule doesn't apply to them; when the tool can't tell whether a server is web-reachable or local, it reports "we couldn't determine this — please check by hand" instead of guessing either way
- [ ] A check for use of the three features being phased out (Roots, Sampling, Logging) → labeled "Worth checking" (Reported)
- [ ] A check for hand-written MCP error numbers → labeled "Worth checking" (Reported)
- [ ] A plain-language report, organized by file, each finding labeled with how sure we are and a link to the source
- [ ] The tool exits with an error code if anything "will break" is found (so it can be used in automated checks later, even though that's not built yet)
- [ ] The checking rules are kept in their own file, separate from the rest of the program, each one labeled and linked to its source
- [ ] One real, working example: a small sample server, before and after
- [ ] A README that explains, in plain language, what sources the rules came from and when they were last checked
- [ ] Published as a public, free-to-use project on GitHub (`softogram-mcp-spec-migration-checker`)

Nice to have, only if time allows:
- [ ] A `--json` option, so the report can be read by other programs, not just humans
- [ ] A `--explain <rule-id>` option that prints the full explanation and source for one specific rule

## 9. What we're explicitly not doing yet (Out of Scope)

- **Automatically fixing code.** Too risky to build safely in 10 hours — could break working code by mistake. Reporting only, for now.
- **Supporting other programming languages** (like TypeScript). Keeping this to one language keeps the first version realistic.
- **Building this into automated pipelines** (like GitHub Actions). Possible for someone to set up themselves already; officially supporting it is separate future work.
- **A hosted website or dashboard.** Would need accounts and storage, which this project's rules (`CLAUDE.md`) say to avoid unless the problem is specifically about that.
- **Guessing the exact error number that's changing.** No source confirms the specific number yet — guessing would be worse than not checking at all.
- **Checking the new task-handling or visual-interface features.** Those are new, optional features — not things that break existing servers that aren't using them yet. Out of scope for a tool about fixing breakage.
- **Checking the new login/security rules in detail.** Reported as stricter, but not detailed enough yet in what we've read to build a reliable check.

## 10. How will we know we did a good job? (Success Criteria)

- Running the tool on our own sample project gives exactly the labels we expect (nothing missed, nothing mislabeled).
- Someone who's never seen this project before can install it and get their first report in under 5 minutes, using only the README.
- Every "worth checking" finding explains why it isn't a "will break" finding, and every "will break" finding links to the official source.

## 11. What might we add later? (Future Upgrade Path)

If this project gets more time later (following this repo's rule of only investing more once something shows real interest — stars, installs, people asking about it):

1. ~~**Update the rules once the official rulebook is fully published on July 28.**~~ **Done, 2026-07-28** — every rule re-verified against the final changelog the same day it published; R4 promoted to Confirmed, R5 narrowed to the four confirmed-renumbered codes, R1/R2's SEP citation corrected, and three backlog SEP-2575 candidates (R6, R7, R8) implemented. See Section 4.2's 2026-07-28 update note and `docs/LEARNINGS.md`.
2. **Add the `--json` option and a small helper for automated pipelines** (like GitHub Actions).
3. **Support TypeScript-based MCP servers**, using the same approach.
4. **Add a "here's exactly what to change" preview mode** that shows the fix without applying it — a safer middle step before ever trying to auto-fix code.
5. **Auto-fix mode**, but only once the preview mode above has been trusted for a while.
6. **An optional, privacy-respecting way to learn from real-world results** (only if people explicitly agree to share what their scans found), to improve the rules over time.

This is the short version. For the full, expanded list — including multi-version cumulative diffing (checking more than one spec-version hop at once) and new rule candidates already spotted in the current changelog — see `docs/FUTURE-UPGRADES.md`.

## 12. What could go wrong? (Risks & Assumptions)

- **We're assuming the near-final draft won't change much before it becomes official.** Multiple sources agree it was "locked" on May 21, 2026 specifically so people have a stable target to build against. Still, the page we're building against could be edited before July 28 — which is why updating the rules afterward (Section 11, item 1) is the top priority either way.
- **We noticed while researching that our sources don't fully agree.** The one official "what changed" page describes fewer changes than other trusted sources describe for the same update. That's exactly why we built the confidence-labeling system in Section 4.1, instead of treating every claim as equally certain.
- **A tool like this loses trust fast if it cries wolf.** If we're not sure something is actually breaking, we label it "worth checking" instead of "will break" — better to under-claim than over-claim.
- **Only supporting Python for now might limit how many people this helps**, if a lot of affected servers turn out to be written in other languages. That's a deliberate, temporary trade-off (see Section 11, item 3), not something we forgot.
- **We assume the server being scanned is already on the 2025-11-25 spec version.** This tool only checks the single hop from 2025-11-25 to the 2026-07-28 draft (see Section 3). It doesn't detect which version a server is actually running, and it doesn't add up changes across multiple version hops. A server still on an older version would see findings that don't fully apply until it first upgrades to 2025-11-25 the normal way. This is a known, deliberate scope cut, not something we overlooked — see `docs/FUTURE-UPGRADES.md` for the multi-version approach we'd build later.

## 13. Where this information came from (References)

Most certain (official source):
- [MCP's official "what changed" page](https://modelcontextprotocol.io/specification/draft/changelog)
- [MCP's own blog post about this update](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/)

Reported by trusted sources, slightly less certain:
- [Agentic AI Foundation: "MCP Is Growing Up"](https://aaif.io/blog/mcp-is-growing-up/)
- [Independent builder's guide from ChatForest](https://chatforest.com/builders-log/mcp-spec-2026-07-28-release-candidate-stateless-breaking-changes-builder-guide/)

This project's own context:
- `docs/softogram-growth.md` (in the main `softogram-projects` folder) — explains the bigger picture: why Softogram builds one small tool every week.
- `CLAUDE.md` — the rules this whole project follows (what to build, what language to use, how to write docs, and what "finished" means).
- `LOG.md` — the day-by-day log of what's done and what's left for this specific project.
- `docs/FUTURE-UPGRADES.md` — the expanded version of Section 11: everything that could make this tool more complete or robust later, organized by category.
