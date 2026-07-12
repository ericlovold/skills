---
name: tailwind
description: Use when the user drops market news and says "pick this up" / "what does this mean for us" — a platform launch, a protocol shift, a competitor move, a policy change. Runs the market-event playbook — verify the event at primary sources, map it onto your product and roadmap, ship a fenced same-day slice if one exists, and flag the GTM moment. Named for what a well-aimed event is to a small fast product: a tailwind.
---

# tailwind: news speed, product response

A small team's edge over incumbents is cycle time: when the market moves, the
product can answer the same day. A worked example that set the pattern: a
platform launched per-request charging for AI crawlers at breakfast; a
governed-buyer adapter + guide + changelog entry shipped by lunch. This skill
is that pattern, repeatable.

## Step 1 — verify the event before building on it

- Primary sources outrank coverage: vendor docs and changelogs over press,
  press over social. Get the actual mechanics — header names, dates,
  defaults, protocol — not the vibe. (Vendor marketing blogs sometimes block
  automated fetches; their developer-docs subdomains usually don't.)
- Pin the load-bearing facts: what changed, when it takes effect, who's
  affected, what the wire looks like. If a fact can't be verified, it can't
  be in the changelog entry or the guide.

## Step 2 — map it onto your product

Three questions, in order:

1. **Which of your primitives apply unchanged?** The best answers need zero
   core surgery — in the worked example, a crawl-payment quote was "just a
   spend decision with a hostname for a merchant." If the event requires new
   core semantics, it's a full arc, not a same-day slice.
2. **Which roadmap item does it accelerate?** An event that makes a "Later"
   item suddenly urgent is the strongest signal — the arc was already believed
   in; the market just voted for it.
3. **Which side of the transaction is yours?** Usually the buyer/governor
   side — "hold the mandate, not the rail." Rails belong to platforms;
   deciding, evidencing, and budgeting are yours. Say explicitly which side
   the event's vendor owns and why you're not competing there.

## Step 3 — ship the fenced slice (same day or not at all)

The slice is an adapter, a guide, a policy pack, or a small surface touch —
never hot-path core surgery on news cadence. It ships with:

- the honest boundary stated (what you govern vs what the vendor's rail owns),
- a docs guide with a recipe (buyers arrive from the news search),
- a changelog entry that rides the news language while it's hot,
- the follow-on arc captured in the backlog (the slice is the wedge, the arc
  is the product),
- a roadmap note if the event just started a roadmap item's first slice.

If no fenced slice exists, say so — the deliverable degrades gracefully to the
mapping (step 2) + a backlog arc + the GTM flag. A forced slice on the wrong
event is worse than none.

## Step 4 — flag the GTM moment

News windows close in days. Tell the user what the moment is — the one-line
question the event just invented (in the worked example, "what did we pay the
web last month, by department?") — and offer to coach a post. Coach structure
and strategy; never draft their words for them.

## Rules

- No slice before verification; no changelog claim without a checked fact.
- The event does not reorder the roadmap by itself — a zoom-out weighs it
  against everything else; tailwind ships the wedge and captures the arc.
- Speed is the point, but the gate is not waived: tests, docs, truth surfaces
  — same bar as any change.
