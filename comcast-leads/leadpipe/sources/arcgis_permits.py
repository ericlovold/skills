"""Commercial building permits from an ArcGIS FeatureServer layer.

Used for Minneapolis CCS Permits and Saint Paul building permits. The field
names differ per city and are configured in `PermitSource.fields`.

A permit applicant is often the contractor, not the tenant. The lead still
carries the address and the work description, which is enough to look the
tenant up during enrichment.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from leadpipe.config import PermitSource
from leadpipe.http import Http
from leadpipe.models import Lead
from leadpipe.normalize import extract_zip

PAGE_SIZE = 1000

# A permit is interesting if any of these appear in the permit type, work type,
# or description. Residential-only permits are dropped.
COMMERCIAL_TERMS = (
    "commercial",
    "tenant",
    "build-out",
    "buildout",
    "build out",
    "remodel",
    "office",
    "retail",
    "restaurant",
    "clinic",
    "warehouse",
    "new building",
    "new construction",
    "alteration",
    "interior",
)
RESIDENTIAL_TERMS = ("single family", "single-family", "residential", "duplex", "sfd", "adu")


def layer_fields(http: Http, source: PermitSource) -> list[dict]:
    """Field list from the layer's metadata, for the `probe` command."""
    meta = http.get_json(f"{source.url}", params={"f": "pjson"})
    return meta.get("fields", [])


def _epoch_ms_to_iso(value) -> str:
    if value in (None, ""):
        return ""
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC).date().isoformat()
    except (TypeError, ValueError, OSError):
        return str(value)


def is_commercial(*texts: str) -> bool:
    hay = " ".join(t.lower() for t in texts if t)
    if not any(term in hay for term in COMMERCIAL_TERMS):
        return False
    return not any(term in hay for term in RESIDENTIAL_TERMS)


def parse_features(features: list[dict], source: PermitSource) -> list[Lead]:
    f = source.fields
    leads: list[Lead] = []
    for feat in features:
        a = feat.get("attributes", {})
        permit_type = str(a.get(f.permit_type) or "")
        work_type = str(a.get(f.work_type) or "")
        description = str(a.get(f.description) or "")
        if not is_commercial(permit_type, work_type, description):
            continue
        applicant = str(a.get(f.applicant) or "").strip()
        address = str(a.get(f.address) or "").strip()
        if not applicant and not address:
            continue
        leads.append(
            Lead(
                source=source.name,
                signal=f"permit:{(work_type or permit_type).strip().lower()}"[:60],
                company_name=applicant,
                address=address,
                city=source.city,
                state=source.state,
                zip=extract_zip(address),
                signal_date=_epoch_ms_to_iso(a.get(f.date)),
                evidence_url=source.url,
                description=" | ".join(x for x in (permit_type, work_type, description) if x)[:500],
                raw={"attributes": a, "value": a.get(f.value)},
            )
        )
    return leads


def fetch_permits(http: Http, source: PermitSource, since_days: int) -> list[Lead]:
    """Pull permits issued in the last `since_days`, paging through the layer."""
    if not source.url:
        return []
    since = datetime.now(UTC) - timedelta(days=since_days)
    where = f"{source.fields.date} >= TIMESTAMP '{since.strftime('%Y-%m-%d %H:%M:%S')}'"
    features: list[dict] = []
    offset = 0
    while True:
        page = http.get_json(
            f"{source.url}/query",
            params={
                "where": where,
                "outFields": "*",
                "orderByFields": f"{source.fields.date} DESC",
                "resultOffset": offset,
                "resultRecordCount": PAGE_SIZE,
                "f": "json",
            },
        )
        if "error" in page:
            raise RuntimeError(f"{source.name}: {page['error']}")
        batch = page.get("features", [])
        features.extend(batch)
        if not page.get("exceededTransferLimit") or not batch:
            break
        offset += len(batch)
    return parse_features(features, source)
