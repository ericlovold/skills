---
name: decided
description: >-
  Use when a real decision gets made — in chat, after a zoomout, mid-arc — or
  when the user says "log this decision", "we decided", "let's go with", or
  "why did we choose X again?". Appends the decision WITH its reasoning to
  docs/DECISIONS.md, and when a settled topic reopens, quotes the log back and
  asks what changed. Not for tasks (that's a todo) and not for ideas (that's
  queue) — only for choices that closed a door.
---

# decided: log the decision, keep the reasoning

Decisions don't stay decided on their own. The choice survives in the code;
the *reasoning* evaporates — and a few weeks later the same question comes
back, gets decided slightly differently, and the product wobbles. A team has
institutional memory in other people's heads. A solo founder has a file, or
nothing. This is the file.

## Capturing (at decision time, not later)

When a decision closes in conversation, append to `docs/DECISIONS.md`
(create it if missing), newest on top:

```text
- 2026-07-11 — **Stay source-available, not OSS.**
  Why: licensing is the only moat while the team is one person.
  Rejected: full OSS (community value < fork risk right now).
  Revisit when: first design partner asks for it in writing.
```

Four fields, all required:

- **The decision** — one line, stated as the thing chosen, not the question.
- **Why** — the reasoning that actually carried it, 1–3 lines, in the user's
  own framing where possible. This field is the entire point of the file.
- **Rejected** — the alternative that lost, with the one-line reason it lost.
  A decision with no named loser was probably not a decision.
- **Revisit when** — a condition (preferred) or a date. "Never" is a valid
  answer and worth writing down.

## The re-litigation protocol

When the user starts reopening a settled topic, check the log **before**
engaging with the question:

1. Quote the entry back — date, decision, why.
2. Ask one question: **"what changed?"**
3. If nothing changed → the decision stands; return to work. The log just
   saved an afternoon.
4. If something did change → decide fresh, then log the new decision as a
   new entry marked *supersedes YYYY-MM-DD*. Never edit or delete the old
   entry — the history of how thinking evolved is data, not clutter.

## Rules

- **Capture at the moment of decision.** A rationale reconstructed a week
  later is a guess wearing the old decision's clothes.
- **The public-repo rule** (same as queue): if the repo is public, phrase
  entries for a competitor, a customer, and a design partner reading at once.
  Sensitive reasoning gets a generalized entry; the substance stays in chat.
- **Small decisions don't go in.** "Named the variable `retries`" is not a
  door closing. If nobody would re-litigate it, don't log it.
- **Zoomout reads this file.** Open "revisit when" conditions that have come
  true are open loops and should surface there.

## Failure mode this kills

The Tuesday re-litigation loop: the same strategic question — pricing, repo
visibility, build-vs-buy — decided every few weeks, each time from scratch,
each time slightly differently, burning the scarcest resource a solo founder
has on questions that were already answered.
