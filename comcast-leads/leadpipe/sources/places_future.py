"""Google Places API (New): businesses with businessStatus = FUTURE_OPENING.

This is the only source that fires before a business opens and already has a
listing. Text search bills at the Pro SKU per call; the field mask here stays
inside Pro. Phone and website (Enterprise SKU) are fetched later in enrich,
only for leads that survived the footprint filter.

Unverified against a live key: whether an "opening soon" text query surfaces
enough FUTURE_OPENING places. The status value itself is documented.
"""

from __future__ import annotations

from leadpipe.footprint import Footprint
from leadpipe.http import Http
from leadpipe.models import Lead

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.addressComponents",
        "places.businessStatus",
        "places.primaryType",
        "nextPageToken",
    ]
)
FUTURE_OPENING = "FUTURE_OPENING"
MAX_PAGES = 3


def _component(place: dict, kind: str) -> str:
    for c in place.get("addressComponents", []) or []:
        if kind in c.get("types", []):
            return c.get("shortText") or c.get("longText") or ""
    return ""


def parse_places(places: list[dict], footprint: Footprint) -> list[Lead]:
    leads: list[Lead] = []
    for p in places:
        if p.get("businessStatus") != FUTURE_OPENING:
            continue
        zip_code = _component(p, "postal_code")[:5]
        if not footprint.contains_zip(zip_code):
            continue
        leads.append(
            Lead(
                source="places_future",
                signal="places:future_opening",
                company_name=(p.get("displayName") or {}).get("text", ""),
                address=p.get("formattedAddress", ""),
                city=_component(p, "locality"),
                state=_component(p, "administrative_area_level_1") or "MN",
                zip=zip_code,
                evidence_url=f"https://www.google.com/maps/place/?q=place_id:{p.get('id', '')}",
                description=p.get("primaryType", ""),
                raw={"place_id": p.get("id"), "primaryType": p.get("primaryType")},
            )
        )
    return leads


def fetch_future_openings(http: Http, api_key: str, footprint: Footprint) -> list[Lead]:
    headers = {"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": FIELD_MASK}
    leads: list[Lead] = []
    seen: set[str] = set()
    for city in footprint.city_labels():
        body: dict = {"textQuery": f"opening soon {city} MN", "pageSize": 20}
        for _ in range(MAX_PAGES):
            page = http.post_json(SEARCH_URL, body, headers=headers)
            places = [p for p in page.get("places", []) if p.get("id") not in seen]
            seen.update(p.get("id") for p in places)
            leads.extend(parse_places(places, footprint))
            token = page.get("nextPageToken")
            if not token:
                break
            body = {**body, "pageToken": token}
    return leads
