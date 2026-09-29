from __future__ import annotations

import argparse
import logging
import sys

from leadpipe import pipeline
from leadpipe.config import load_settings
from leadpipe.export import write_csv
from leadpipe.footprint import Footprint
from leadpipe.http import RequestsHttp
from leadpipe.sources import arcgis_permits
from leadpipe.store import Store


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="leadpipe", description="Comcast referral lead pipeline")
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("ingest", help="pull sources, filter to footprint, store and score")
    s.add_argument(
        "--sources",
        default=",".join(pipeline.ALL_SOURCES),
        help=f"comma list from {','.join(pipeline.ALL_SOURCES)}",
    )

    e = sub.add_parser("enrich", help="attach phone/website (Places) and contact (Apollo)")
    e.add_argument("--limit", type=int, default=25, help="max leads to enrich this run")

    x = sub.add_parser("export", help="write unsubmitted leads to CSV, best first")
    x.add_argument("--out", default="out/leads.csv")
    x.add_argument("--limit", type=int, default=None)

    m = sub.add_parser("mark-submitted", help="record that leads were entered in the portal")
    m.add_argument("keys", nargs="+")

    pr = sub.add_parser("probe", help="print a permit layer's field names")
    pr.add_argument("source", choices=["mpls", "stpaul"])

    sub.add_parser("stats", help="counts by source and submission state")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    settings = load_settings()
    http = RequestsHttp()

    if args.cmd == "probe":
        source = settings.mpls if args.source == "mpls" else settings.stpaul
        if not source.url:
            print(f"{args.source}: no URL configured", file=sys.stderr)
            return 2
        for f in arcgis_permits.layer_fields(http, source):
            print(f"{f.get('name'):40} {f.get('type', '')}")
        return 0

    footprint = Footprint.load(settings.footprint_csv)
    store = Store(settings.db_path)
    try:
        if args.cmd == "ingest":
            sources = tuple(s.strip() for s in args.sources.split(",") if s.strip())
            r = pipeline.ingest(settings, http, store, footprint, sources)
            print(
                f"fetched={r.fetched} kept={r.kept} created={r.created} merged={r.merged} "
                f"dropped_out_of_footprint={r.dropped_out_of_footprint}"
            )
            if r.errors:
                print(f"errors={r.errors}", file=sys.stderr)
                return 1
            return 0
        if args.cmd == "enrich":
            r = pipeline.enrich(settings, http, store, args.limit)
            print(
                f"attempted={r.attempted} phones_found={r.phones_found} "
                f"contacts_found={r.contacts_found} apollo_skipped={r.apollo_skipped}"
            )
            if r.errors:
                print(f"errors={r.errors}", file=sys.stderr)
                return 1
            return 0
        if args.cmd == "export":
            n = write_csv(store.unsubmitted(args.limit), args.out)
            print(f"wrote {n} leads to {args.out}")
            return 0
        if args.cmd == "mark-submitted":
            missed = [k for k in args.keys if not store.mark_submitted(k)]
            if missed:
                print(f"not found or already submitted: {missed}", file=sys.stderr)
                return 1
            print(f"marked {len(args.keys)} submitted")
            return 0
        if args.cmd == "stats":
            rows = store.all_leads()
            submitted = sum(1 for r in rows if r["submitted_at"])
            by_source: dict[str, int] = {}
            for r in rows:
                for s in r["sources"].split(","):
                    if s:
                        by_source[s] = by_source.get(s, 0) + 1
            print(f"leads={len(rows)} submitted={submitted} by_source={by_source}")
            return 0
    finally:
        store.close()
    return 0
