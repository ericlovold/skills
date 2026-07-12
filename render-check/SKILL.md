---
name: render-check
description: Use BEFORE claiming any UI change works — pages, theme changes, new components — and whenever the user asks "did you actually look at it?". Seeds the data the page needs, boots the dev server, screenshots the named pages with a headless browser, and attaches the evidence. A visual claim without a screenshot is a cheap lie; this skill makes the proof one word.
---

# render-check: no pixels, no claim

"Types pass and the classes look right" is not the same as "the page renders
correctly." Design fixes get claimed and re-claimed until a human says *still
broken*. The rule: a visual change is verified by rendering it, or it is not
verified.

## The ritual

1. **Bring up the data store** the app needs (a local Postgres, SQLite,
   whatever). Sandboxed containers get reclaimed — re-check it's running
   every time, don't assume last turn's process survived.
2. **Seed what the pages need to show.** The empty state proves nothing; seed
   the exact rows that exercise the branch you changed (a nested org with a
   pending item, not a blank account). Insert at the DB level if the ORM's
   generated client won't run standalone. Write down the schema gotchas that
   bite (a NOT-NULL column with no default, a required timestamp) — they'll
   bite again next time.
3. **Boot the dev server** on a spare port, in whatever read-only/demo mode
   renders without a login. If it says another dev server owns the dir, kill
   the PID it names.
4. **Assert fast, then look.** `curl | grep` for the load-bearing strings
   first (cheap, catches 500s), THEN screenshot — grep proves presence, pixels
   prove layout.
5. **Attach the screenshots** to the user AND read them yourself — a
   screenshot you didn't look at proves nothing.
6. **Clean up, always.** Kill the dev server; delete the dev build cache
   (stale artifacts have broken later typecheck gates — leaving them is a
   booby trap for the next command).

### Concrete shape (a Next.js + Prisma + Postgres app — swap for your stack)

```bash
# 1. Postgres (paths are this environment's; find yours)
sudo -u postgres /usr/lib/postgresql/16/bin/pg_ctl start -D /var/lib/postgresql/16/main \
  -o "-c config_file=/etc/postgresql/16/main/postgresql.conf"
# 2. seed via psql inserts (the generated Prisma client is TS-only, won't run under plain node)
# 3. dev server, demo view
DATABASE_URL=... APP_DEMO_ID=<seeded id> npx next dev -p 3112
# 4. screenshot with the preinstalled headless browser
node --input-type=module -e '
import { chromium } from "playwright-core"
const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" })
const p = await b.newPage({ viewport: { width: 1280, height: 900 } })
await p.goto("http://localhost:3112/<page>", { waitUntil: "networkidle" })
await p.screenshot({ path: "<tmp>/<page>.png", fullPage: true }); await b.close()'
# (run from the repo root so playwright-core resolves; the browser path is versioned — ls to confirm)
```

## What to render

- The pages the diff touched, in the state the diff targets — seeded data that
  exercises the new branch, not an empty page.
- Theme changes: BOTH light and dark. A fix in one mode has broken the other
  before.
- Mobile-shaped bugs: a second pass at a phone viewport (e.g. `390×844`).

## Rules

- No screenshot, no "fixed." Say "changed, not yet rendered" if you must stop
  early — never the stronger claim.
- Grep-assertions alone don't close a *visual* issue; they only catch crashes.
  The screenshot is the deliverable.
- Seeded ids are throwaway; never real production ids. The seed lives and dies
  in the local container.
