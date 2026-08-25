---
name: fresh-eyes
description: Use when the user says "fresh eyes", "/fresh-eyes", or is about to hand a project to someone with no context — another agent, a new session, a contractor, a reviewer, a sprint someone else will run. The inverse of an ingestion pass — instead of routing outside material INTO the project, it exports verified project state OUT to a cold reader, and names what that reader will trip on that the team has gone blind to. Also use before pausing work you will not personally resume.
---

# FRESH EYES: the export, and the newcomer's stare

An ingestion skill takes material the user vouches for and routes it into the
project. This is the other direction. Someone is about to open this project
with **zero context** — another agent, a contractor, the user in three weeks —
and everything currently living in a session transcript is about to stop
existing.

Two jobs, and the second is the one people skip:

1. **Export** what a cold reader needs, verified live.
2. **Stare** at the project the way that reader will, and name what is
   confusing, assumed, or quietly load-bearing.

A handoff that only does (1) is a status report. The value is in (2).

## The hard rule: nothing from memory

Every claim in the export is verified against the live system **in this run**.
A handoff is read by someone who **cannot check your work**, so a stale claim
does not get caught — it gets acted on. Your own summary of what you did
earlier in the session counts as memory. Re-verify it.

Verify at minimum, and record the command used:

- Branch, tip commit, and whether the branch content differs from the default
  branch. **Squash merges break ancestry** — compare content, not merge-base.
- Open pull requests and their real state. A merged PR is not an open loop.
- The gate — typecheck, lint, tests. Run it; quote the actual numbers.
- Anything the export calls "live" — hit it. Do not trust the README.
- Published artifact versions (registries, tags) against what the repo claims.

The most common failure is exporting *the deploy is green* from memory while
the live URL says otherwise. Curl it.

## Step 1 — fence the sprint

Before describing anything, state what the incoming reader is being handed and
what they are **not**. An unfenced handoff invites a newcomer to redesign
something the user already decided. Write both lists; **out of scope is the
more valuable one**, and each entry needs its reason — "deliberate, the
owner's call" reads very differently from "nobody has gotten to it."

## Step 2 — the export

One self-contained artifact, written for someone who has never seen the
project, committed to the repo — not left in chat, since chat is exactly the
thing about to disappear.

| Section | What it must answer |
|---|---|
| **Ground state** | Branch, commit, gate numbers, what is deployed, verified how |
| **What just landed** | The last arc, in the reader's terms, not the team's |
| **In flight / open loops** | Ranked, each with its next concrete action |
| **Landmines** | What will burn a newcomer, each with its tell |
| **Decisions that are the owner's** | Do not let a cold agent make these |
| **How to get running** | The exact commands that worked, today |

**Landmines repay the whole exercise.** A landmine is a behavior that (a) has
already cost someone hours, and (b) presents as a different problem than it
is. Give each one its **tell** — the symptom the reader will actually see —
not just the cause. "Row-level security returns nothing outside a tenant
context" is a cause; "queries come back empty and it looks like missing data,
never like an error" is the tell that saves the afternoon.

## Step 3 — the newcomer's stare

Now read the project as the outsider. You are looking for what your own
fluency hides. Prompts that work:

- What does the entry point assume you already know?
- What has a name here that means something else everywhere else?
- Which "obvious" step is only obvious because someone did it once, months ago?
- What is load-bearing, owned by nobody, and documented nowhere?
- Where do two sources of truth disagree?
- What would a competent stranger reasonably do here that would be wrong?

Fix the cheap ones inside the fence. Report the rest.

## Step 4 — the blind-spot ledger (the contract)

An ingestion pass promises that nothing fed in vanishes. This one promises
that **nothing the outsider needs is left assumed**. End with one line per
finding:

```text
FRESH EYES ledger:
1. gate green, 1,189 tests passing   → VERIFIED  (ran it this run)
2. tenant-scoped reads fail silently → LANDMINE  (exported, with the tell)
3. codegen step before first build   → ASSUMED   (was tribal; now in the export)
4. registry token expires in Nov     → UNOWNED   (flagged, needs a human)
5. does the About page get rewritten → DECIDE    (owner's call, not the sprint's)
6. two docs disagree on pricing      → DRIFT     (reported, not fixed here)
```

Statuses: **VERIFIED · LANDMINE · ASSUMED · UNOWNED · DECIDE · DRIFT**.

A ledger with no LANDMINE or ASSUMED lines usually means the stare did not
happen. Handing over a codebase you know well and finding nothing a stranger
would trip on is the least likely outcome, not the best one.

## Boundaries

- **Export, don't refactor.** Fresh eyes see a great deal; a handoff is the
  worst possible moment to act on all of it. Cheap and inside the fence: fix.
  Everything else: ledger it.
- **Don't resolve DRIFT here.** Conflicting truth surfaces get reported; a
  docs-reconciliation pass drains them as its own piece of work.
- **Don't decide the owner's decisions.** Anything shaped like product,
  pricing, naming, or identity goes in the export as DECIDE, phrased so a cold
  agent knows to stop rather than guess.
- **Assume the export is public.** It is a committed file: no keys, no live
  account identifiers, no customer names, no private terms. When a fact is
  needed to work but unsafe to commit, name its *shape* and where it lives —
  an env var, a secrets store — never the value.
- Cut the export before committing it. A handoff nobody finishes reading is a
  handoff that did not happen.
