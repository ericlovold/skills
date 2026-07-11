---
name: preship
description: >-
  Use when something is about to leave the building — a production deploy, a
  public release, a pricing or copy change on a live page, an email to a
  customer or investor, a post going live — and the user says "ship it",
  "ready to send?", "preship", or is clearly one step from an irreversible or
  public action. Acts as the second pair of eyes a solo founder doesn't have:
  an adversarial pass on the exact artifact going out, not the intention
  behind it. Not a test run (that's verify) and not strategy (that's
  zoomout) — this is the reviewer of last resort.
---

# preship: the reviewer a solo founder doesn't have

Solo means no code reviewer, no editor, no QA, no ops on-call, no legal read.
Every class of mistake those roles exist to catch still exists — there's just
nobody assigned to catch it. This skill is the assignment: one adversarial
pass on the actual thing about to go out, run by someone who didn't write it.

## Protocol

1. **Review the artifact, not the description of it.** Read the real diff,
   the rendered page, the email as the recipient opens it — fresh, this
   pass, end to end. If the final artifact isn't visible to you, say so and
   get it; a preship run on a paraphrase is theater.

2. **Ask who receives it, and what the worst honest reading is.** The
   customer, the competitor, the future auditor, the tired user at 11pm.
   Read it as them, not as the author.

3. **Run the missing-role checks that apply:**
   - **Reviewer** — does the change do more than intended? Secrets or debug
     output in the diff, migration order, whether rollback actually exists.
   - **Editor** — names, numbers, dates, prices agree with each other and
     with reality; every link resolves; the typo is always in the headline.
   - **QA** — the path a first-time user takes, which is never the path the
     author tested. Empty states, the second click, the back button.
   - **Ops** — what breaks at 2am, and who gets paged. (You do. It's always
     you.)

4. **Verdict.** Exactly one of:
   - **SHIP** — clean, go.
   - **SHIP-AFTER** — the ranked list of fixes, then go. No re-review of the
     whole artifact afterward; re-check the fixes only.
   - **HOLD** — something is wrong enough that shipping today is the
     mistake. Say what, and what would clear it.

## Rules

- **Findings point at the artifact.** "Line 3 says $29, the pricing page
  says $39" is a finding. "Consider tightening the intro" is a vibe — cut it.
- **Five findings, ranked, maximum.** A forty-item list is a way of
  reviewing nothing; if there are forty problems, the verdict is HOLD and
  the finding is "this isn't ready for review."
- **Calibrate to blast radius.** A prod migration and a tweet do not get the
  same depth. Irreversible + public gets everything; reversible + quiet gets
  the sixty-second version.
- **voice-fence still applies.** On outbound writing, name the problem in
  their draft — never supply the replacement sentence.
- **One pass.** Preship is a gate, not a loop. If it keeps finding new
  things on round three, the problem is upstream of shipping.

## Failure mode this kills

The solo blind spot: the class of error a second person catches in thirty
seconds — the wrong price on the launch page, the migration with no
rollback, the customer email with the internal codename — that shipping
alone never catches, so a customer catches it instead.
