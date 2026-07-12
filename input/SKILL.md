---
name: input
description: Use when the user says "INPUT", "/INPUT", or feeds in a block of raw material they vouch for — strategy notes, sprint output, a roadmap enhancement, a code snippet, or live coding suggestions for work in flight. Unlike a one-liner capture, INPUT is ingestion with judgment — read it all, split it into pieces, route each piece to where it lives, apply what's live, and report a disposition for every piece. Nothing fed in gets silently dropped.
---

# INPUT: more input, Johnny 5

The user has raw material they already know is good — the vouching is the
signal. Your job is not to re-litigate whether it's valuable; it's to read
fast, think anyway, and put every piece where it belongs. Disassemble the
payload, not the day.

## Step 1 — read the whole payload first

No partial application. Strategy context at the bottom can change what a
snippet at the top means. Read everything, THEN act.

## Step 2 — split and classify

Break the payload into distinct pieces. Each piece is one of:

| Class | Destination |
|---|---|
| **Live** — a suggestion/snippet for work currently in flight | The working tree, this change |
| **Later** — roadmap enhancement, strategy, feature idea, snippet with no live target | The backlog (a dated one-line entry) |
| **Durable** — a working-style rule, convention, or lesson that outlives any one task | Propose an edit to the project's agent-instructions file (e.g. `AGENTS.md` / `CLAUDE.md`) |
| **Sensitive** — names, deals, sources, private reasoning | The conversation only — never a committed file |

One payload usually contains several classes. Classify per piece, not per
payload.

## Step 3 — act by class

- **Live pieces**: verify against the live code before applying — the
  suggestion was written against someone's mental model, not necessarily the
  file as it is now. Apply what survives, fenced to the current change, and
  run the relevant gate. If a piece is wrong for this codebase, PUSH BACK with
  the reason — INPUT is ingestion with judgment, not dictation. Johnny 5 reads
  fast; he still thinks.
- **Later pieces**: distill each to a dated backlog entry, phrased safe for a
  public repo. Keep the user's words where they carry intent. Do NOT start the
  new work — INPUT never turns into a pivot unless the user says "now".
  Roadmap-shaped pieces become backlog entries flagged "(roadmap candidate)";
  the roadmap itself changes only on request.
- **Durable pieces**: draft the agent-instructions addition and show it — the
  user approves durable memory (date it, phrase it to survive time).
- **Sensitive pieces**: acknowledge what you're holding and where the safe
  generalized placeholder went, if any. The substance stays in chat.

## Step 4 — the disposition report (the contract)

End with one line per piece — nothing fed in vanishes:

```text
INPUT disposition:
1. retry-backoff snippet        → APPLIED   (gateway module, tests green)
2. Q3 channel-pack idea         → QUEUED    (backlog, roadmap candidate)
3. "always gate deploys" rule   → PROPOSED  (instructions draft above, awaiting ok)
4. prospect pricing detail      → HELD      (sensitive — conversation only)
5. switch-to-polling suggestion → PUSHED BACK (webhooks already cover this; see note)
```

Statuses: APPLIED · QUEUED · PROPOSED · HELD · PUSHED BACK. A payload where
everything lands as QUEUED is fine; a payload with no disposition report is
a failed INPUT.

## The INPUT! call (flavor — never at the expense of the work)

This skill is named for Number 5 shouting "INPUT!" in *Short Circuit*. Lean
into it, lightly:

- **On invoke** (interactive sessions only — never in cron/headless, where a
  banner is just log noise), open with the Number 5 banner from
  `assets/johnny5.txt` and exactly ONE catchphrase: *"Input!"* · *"More
  input!"* · *"Number 5 is alive!"* · *"Need more input."*
- **Garnish the disposition report**, one aside max per line, mapping the
  robot's lines to what actually happened:
  | Status | Aside |
  |---|---|
  | APPLIED | *input assimilated* |
  | QUEUED | *stored in memory banks* |
  | PROPOSED | *awaiting your command* |
  | HELD | *no disassemble* (kept whole, kept safe) |
  | PUSHED BACK | *malfunction — does not compute here* |
- **Close a clean run** with *"Number 5 is alive."*
- Humans who want the full effect — voice + a boot animation — run
  `bash assets/input-alert.sh` in their own terminal (best-effort `say`,
  degrades to a terminal bell, silent where no audio exists).

**The one hard rule:** the flourish is a garnish on a working report, never a
substitute for one. If the payload is heavy, or the moment is serious, or the
flavor would delay routing a live piece — drop the flavor, keep the rigor. A
witty banner over a missing disposition report is a failed INPUT with a hat on.

## Boundaries

- INPUT feeds the current work or the backlog — it does not open new work
  streams, end turns as the main event when work was interrupted, or edit
  roadmap/README claims on its own authority.
- If the repo is public, phrase every committed byte so a competitor, a
  customer, and a design partner could all read it.
- If a piece is copy a human will read as their own words, coach it, don't
  write it.
