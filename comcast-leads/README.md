# comcast-leads

Finds businesses in the Comcast Business footprint that are about to open,
move, or build out a space, and turns them into referral rows for the
Comcast Business Authorized Connector portal.

Temporary home: this folder lives in the `skills` repo only until it gets a
repo of its own. Nothing here depends on the rest of this repo. Move it with
`git mv comcast-leads ../comcast-leads` or a subtree split.

## What it does

```
sources  ->  footprint filter  ->  dedupe + score  ->  enrich  ->  export CSV
```

| Stage | Source | Signal | Needs a key |
|---|---|---|---|
| ingest | Minneapolis CCS Permits (ArcGIS REST) | commercial permit issued | no |
| ingest | Saint Paul building permits (ArcGIS REST) | commercial permit issued | no |
| ingest | Google News RSS, per footprint city | "opens", "relocates", "expands" headlines | no |
| ingest | Google Places text search | `businessStatus = FUTURE_OPENING` | Places |
| enrich | Google Places details | business phone and website | Places |
| enrich | Apollo people search + match | decision-maker name, title, email | Apollo, and opt-in |

Only businesses whose zip is in `data/comcast_footprint_zips.csv` are kept.
That list came from the Comcast rep. City labels in that file are for
readability and for matching news headlines, not a source of truth.

## Setup on the Mac Mini

```bash
cd comcast-leads
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in keys; never commit .env
```

Confirm the permit layers' real field names before the first run, because the
defaults in `leadpipe/config.py` were taken from documentation, not a live
call:

```bash
python -m leadpipe probe mpls
python -m leadpipe probe stpaul     # only after STPAUL_PERMITS_URL is set
```

Then set any `MPLS_FIELD_*` / `STPAUL_FIELD_*` overrides in `.env`.

## Daily run

```bash
python -m leadpipe ingest                 # all keyless sources, plus Places if key set
python -m leadpipe enrich --limit 25      # phone/website via Places; Apollo only if APOLLO_ENABLE_ENRICH=true
python -m leadpipe export --out out/leads.csv
python -m leadpipe mark-submitted <dedupe_key> ...   # after entering in the portal
```

The export contains only unsubmitted leads, highest score first, with the
four columns the portal wants (contact name, company, email, phone) plus the
evidence link so the rep can see why the lead exists.

Schedule with cron on the Mac Mini:

```
15 6 * * 1-5  cd /path/to/comcast-leads && .venv/bin/python -m leadpipe ingest && .venv/bin/python -m leadpipe export --out out/leads.csv
```

## Cost controls

- Places: text search bills at the Pro SKU. Phone and website are fetched
  only for leads that survive the footprint filter, and only in `enrich`.
- Apollo: search is free of credits; revealing an email costs about one
  credit and a mobile about eight. Enrichment does nothing unless
  `APOLLO_ENABLE_ENRICH=true`, and `--limit` caps how many leads are enriched
  per run.

## Scoring

Score is a rough priority, not a probability. Source weight, plus a bonus
when the same company shows up at two or more addresses (multi-site pays up
to $5,000 versus $1,500), plus a bonus when a phone is already attached.
See `leadpipe/score.py`.

## Tests

```bash
pytest
ruff check .
```

Every parser is tested against a recorded fixture in `tests/fixtures`. Live
endpoints were not reachable from the environment where this was written, so
the first live run on the Mac Mini is the real integration test. Expect to
adjust field names via `.env`.

## Things still unverified against live endpoints

- Minneapolis and Saint Paul permit field names and the date field.
- Whether Google Places text search reliably returns `FUTURE_OPENING` places
  for an "opening soon" query. The status value itself is documented.
- Apollo request parameter names for people search; the endpoint paths are
  documented but were not exercised.
