"""Orchestration: ingest -> footprint filter -> store -> score; enrich; export."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from leadpipe.config import Settings
from leadpipe.enrich import apollo, places_details
from leadpipe.footprint import Footprint
from leadpipe.http import Http
from leadpipe.models import Lead
from leadpipe.score import score_lead
from leadpipe.sources import arcgis_permits, google_news, places_future
from leadpipe.store import Store

log = logging.getLogger("leadpipe")

ALL_SOURCES = ("mpls", "stpaul", "news", "places")


@dataclass
class IngestReport:
    fetched: dict[str, int] = field(default_factory=dict)
    kept: int = 0
    created: int = 0
    merged: int = 0
    dropped_out_of_footprint: int = 0
    errors: dict[str, str] = field(default_factory=dict)


def in_footprint(lead: Lead, footprint: Footprint) -> bool:
    """Zip wins when present. News has no zip, so a footprint city is enough."""
    if lead.zip:
        return footprint.contains_zip(lead.zip)
    return bool(lead.city) and footprint.match_city(lead.city) != ""


def _rescore(store: Store, key: str) -> int:
    row = store.get(key)
    assert row is not None
    score = score_lead(
        sources=row["sources"],
        distinct_addresses=store.distinct_addresses(row["norm_name"]),
        phone=row["phone"],
        contact_email=row["contact_email"],
        signals=row["signals"],
    )
    store.set_score(key, score)
    return score


def _absorb(store: Store, footprint: Footprint, leads: list[Lead], report: IngestReport) -> None:
    for lead in leads:
        if not in_footprint(lead, footprint):
            report.dropped_out_of_footprint += 1
            continue
        key, created = store.upsert(lead)
        _rescore(store, key)
        report.kept += 1
        if created:
            report.created += 1
        else:
            report.merged += 1


def ingest(
    settings: Settings, http: Http, store: Store, footprint: Footprint, sources: tuple[str, ...]
) -> IngestReport:
    report = IngestReport()
    for name in sources:
        try:
            if name == "mpls":
                leads = arcgis_permits.fetch_permits(http, settings.mpls, settings.ingest_days)
            elif name == "stpaul":
                if not settings.stpaul.url:
                    log.info("stpaul: STPAUL_PERMITS_URL not set, skipping")
                    continue
                leads = arcgis_permits.fetch_permits(http, settings.stpaul, settings.ingest_days)
            elif name == "news":
                leads = google_news.fetch_news(
                    http, footprint, settings.news_terms, settings.ingest_days
                )
            elif name == "places":
                if not settings.places_enabled:
                    log.info("places: GOOGLE_PLACES_API_KEY not set, skipping")
                    continue
                leads = places_future.fetch_future_openings(
                    http, settings.google_places_api_key, footprint
                )
            else:
                raise ValueError(f"unknown source {name!r}")
        except Exception as exc:  # one bad source must not sink the run
            log.exception("%s failed", name)
            report.errors[name] = f"{type(exc).__name__}: {exc}"
            continue
        report.fetched[name] = len(leads)
        _absorb(store, footprint, leads, report)
    return report


@dataclass
class EnrichReport:
    attempted: int = 0
    phones_found: int = 0
    contacts_found: int = 0
    apollo_skipped: bool = False
    errors: dict[str, str] = field(default_factory=dict)


def enrich(settings: Settings, http: Http, store: Store, limit: int) -> EnrichReport:
    report = EnrichReport()
    report.apollo_skipped = not settings.apollo_enabled
    for row in store.needs_enrichment(limit):
        key = row["dedupe_key"]
        report.attempted += 1
        updates: dict[str, str] = {}
        try:
            if settings.places_enabled and not row["phone"]:
                place_id = _place_id_from_raw(store, key)
                if not place_id:
                    place_id = places_details.find_place_id(
                        http, settings.google_places_api_key, row["company_name"], row["address"]
                    )
                contact = places_details.fetch_contact(
                    http, settings.google_places_api_key, place_id
                )
                if contact.phone:
                    updates["phone"] = contact.phone
                    report.phones_found += 1
                if contact.website:
                    updates["website"] = contact.website
            website = updates.get("website") or row["website"]
            if settings.apollo_enabled and not row["contact_email"]:
                person = apollo.best_contact(
                    http, settings.apollo_api_key, row["company_name"], website
                )
                if person and (person.email or person.name):
                    updates["contact_name"] = person.name
                    updates["contact_title"] = person.title
                    updates["contact_email"] = person.email
                    if person.email:
                        report.contacts_found += 1
        except Exception as exc:
            log.exception("enrich %s failed", key)
            report.errors[key] = f"{type(exc).__name__}: {exc}"
            continue
        if updates:
            store.update_fields(key, **updates)
        store.mark_enriched(key)
        _rescore(store, key)
    return report


def _place_id_from_raw(store: Store, key: str) -> str:
    """A places_future lead already knows its place_id; reuse it and skip a search."""
    row = store.conn.execute(
        "SELECT raw FROM sightings WHERE dedupe_key = ? AND source = 'places_future' LIMIT 1",
        (key,),
    ).fetchone()
    if not row:
        return ""
    try:
        return json.loads(row[0]).get("place_id") or ""
    except (ValueError, AttributeError):
        return ""
