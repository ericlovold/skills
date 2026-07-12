---
name: truthsync
description: Use when ships have outrun the public story — merged PRs with no changelog entry, roadmap "Next" items that already shipped, README claims that drifted — or on request ("truthsync", "drain the drift") and as a pre-release sweep. Diffs merged work since the last drain against the project's truth surfaces (changelog, roadmap, README, glossary, traceability) and proposes the catch-up as one docs-only PR. A zoom-out detects this drift; truthsync fixes it.
---

# truthsync: the story catches up to the ships

Some repos ship faster than they narrate. If the roadmap's own principle is
"Now leads the product by ~one release and never lags it," then a shipped
"Next" item is a broken invariant — and the fix is a hand-built catch-up PR.
This skill is that PR as a ritual.

## Step 1 — establish the gap (live reads only)

- Last drain point: the newest changelog entry with a `version` stamp, or the
  last truthsync PR — whichever is later.
- `git log --oneline <that-point>..origin/main` — every merge since. Include
  work from other sessions; they ship too.

## Step 2 — sweep each ship across the truth surfaces

For every substantive merge, ask the surface questions (map these to wherever
your project keeps each one):

| Surface | The question |
|---|---|
| Changelog | Does it have an entry? Features, hardening, and honest boundaries all count |
| Roadmap | Did it complete a Now/Next/Later item? Rotate: shipped phrasing or removal, successors promoted, arc note updated |
| README | Does a claim, endpoint/API table row, or guide link now under- or over-state the product? |
| Glossary / concepts | Did it add or change a concept the canonical vocabulary should carry? |
| Traceability / test map | Enforcing surfaces touched → mapping still true? New invariant → new entry? |

Also close the loop the other way: backlog entries the ships resolved get
checked off with a "shipped" note.

## Step 3 — verify before writing (the count rule)

Every count, endpoint, tool name, and behavior claim in a new entry is
verified against the code as it is — grep the source, hit the route table,
count the registrations. A truth surface that's confidently wrong is worse
than a stale one.

## Step 4 — one PR, docs-only

All drains ride together: changelog entries, roadmap rotation, README and
glossary touches, traceability rows, backlog checkoffs. Docs-only diff, house
voice. List the ship→surface mapping in the PR body so review is a table scan.

## Rules

- Drift found ≠ license to editorialize: sync the story to the code, don't
  restrategize the roadmap inside a drain (that's a zoom-out decision).
- If the repo is public, the public-repo phrasing rule applies to every added
  sentence.
- Cadence: run before every release cut (notes get written from clean
  surfaces), and whenever a zoom-out flags drift.
