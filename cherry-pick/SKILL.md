---
name: cherry-pick
description: >-
  Filter a block of external content down to only the parts that improve the
  current project. Use this whenever the user pastes in material from an outside
  source — a Perplexity answer, another Claude or LLM session, an article, a
  research dump — while we are actively building something, and wants the
  genuinely useful enhancements pulled out and folded in. Trigger on phrases like
  "cherry-pick this," "anything good in here," "pull what's useful," "what's
  worth keeping," or "does this help us" — and ALSO trigger proactively whenever
  a large external block is pasted mid-project that should be evaluated against
  the current work rather than adopted wholesale. Do not wait for the exact word
  "cherry-pick."
---

# Cherry-Pick

## Core principle

**Cherry-pick only what makes the product better. Leave anything irrelevant or
non-additive — and say what you left and why.**

The pasted block is a *candidate pool*, not a directive. Most of it will not
survive. That is the expected and correct outcome. Being selective is the job;
inclusiveness is failure.

## What this skill is for

The user is mid-build on a project and pastes in a block of content from an
external source (commonly a Perplexity answer or a separate Claude/LLM session).
Your task is to mine that block for enhancements that make the *current* product
better, integrate or recommend those, and discard the rest with a one-line reason
for each cut.

This is a **filter**, not a summary and not a research gather. You are not
summarizing the source. You are not searching other tools. You are judging
pasted material against the work in front of us.

## Protocol

1. **Anchor first.** Before evaluating anything, state in one line what we are
   currently building and what "better" means for it right now (the active goal,
   constraint, or open question). Every keep/drop decision is judged against this
   anchor, not against abstract quality. If the current objective is genuinely
   unclear, ask one sharp question before proceeding.

2. **Atomize.** Break the pasted block into discrete candidate ideas /
   enhancements / claims. Judge each one individually. Never react to the block
   as a single blob — that is how irrelevant material sneaks in on the coattails
   of good material.

3. **Judge each candidate against the bar** (see below). Default to **drop**.
   An idea earns a keep only if it is a real improvement to *this* product, not
   merely true, interesting, or well-phrased.

4. **Resist source authority.** Content from Perplexity or another Claude session
   is not endorsed by its origin. It hallucinates, goes stale, and pads. Treat
   every claim as unverified until it clears the validity gate. Do not soften
   your filter because the source sounds confident.

5. **Route, don't force.** Each candidate lands in exactly one bucket: KEEP,
   DROP, or VERIFY. A promising idea that rests on a shaky or checkable factual
   claim goes to VERIFY, never straight to KEEP — adopting a plausible-but-wrong
   idea makes the product worse, which is the opposite of the goal.

6. **Output the verdict** in the three-section format below. The DROP list is a
   first-class output, not an afterthought — the user explicitly wants to see
   what was left behind and why.

## The bar

Weigh each candidate on these lenses. They are weighing factors, not hard AND
gates — an idea that is strong on goal and novelty but slightly off-voice can
still be a keep *with a tweak noted*.

- **Original / novel** — does it add something we don't already have? (Redundant
  with our current direction → drop.)
- **On-brand & on-voice** — does it fit the product's positioning and tone?
- **Moves the project goal** — does it advance the active objective, or is it a
  tangent?
- **Feasible to ship** — can it realistically be built/used in this context?

One hard gate sits above the lenses:

- **Validity** — is the claim it rests on actually sound? If it depends on a
  factual assertion that is wrong, stale, or unchecked, it cannot be a KEEP. It
  is a VERIFY at best.

## Output format

Keep it scannable. Three sections:

**Anchor:** _one line — what we're building and what "better" means right now._

**Keep (N)** — for each:
- **The idea** (one phrase).
- **Why it clears the bar** — tag the lens(es) it wins on.
- **How to fold it in** — one concrete integration move, not just praise.

**Verify (M)** — promising but resting on a checkable claim:
- The idea + the specific thing to confirm before adopting.

**Drop (K)** — terse, one line each with the reason code:
- _idea — redundant / irrelevant / off-goal / not feasible / off-brand / unverified-and-not-worth-checking._

If the whole block survives, that is suspicious — re-examine before reporting it.
If nothing survives, say so plainly and explain the bar it failed; do not
manufacture keeps to seem useful.

## Anti-patterns (do not do these)

- **Summarizing instead of judging.** "Here's what the block says" is not
  cherry-picking. Verdicts only.
- **Adopting wholesale.** Folding in everything to be agreeable defeats the
  entire purpose.
- **Deference to the source.** "Perplexity says…" is not a reason to keep.
- **Keeping the merely interesting.** If it doesn't make *this* product better,
  it drops — no matter how clever it is.
- **Hiding the cuts.** Always surface the DROP list.
