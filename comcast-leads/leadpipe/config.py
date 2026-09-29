"""Settings from environment variables.

Keys never live in code. Copy .env.example to .env and fill it in; the CLI
loads .env from the working directory if present.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def load_dotenv(path: str | os.PathLike = ".env") -> None:
    """Minimal .env loader: KEY=VALUE lines, # comments, no interpolation.

    Existing environment variables win, so CI and cron can override the file.
    """
    p = Path(path)
    if not p.is_file():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class PermitFieldMap:
    """Attribute names on an ArcGIS permit layer. Confirm with `probe`."""

    applicant: str
    address: str
    permit_type: str
    work_type: str
    description: str
    date: str
    value: str


@dataclass(frozen=True)
class PermitSource:
    name: str
    url: str
    fields: PermitFieldMap
    city: str
    state: str = "MN"


def _permit_source(prefix: str, name: str, city: str, defaults: dict[str, str]) -> PermitSource:
    env = os.environ

    def f(key: str) -> str:
        return env.get(f"{prefix}_FIELD_{key.upper()}", defaults[key])

    return PermitSource(
        name=name,
        url=env.get(f"{prefix}_PERMITS_URL", defaults.get("url", "")).rstrip("/"),
        fields=PermitFieldMap(
            applicant=f("applicant"),
            address=f("address"),
            permit_type=f("permit_type"),
            work_type=f("work_type"),
            description=f("description"),
            date=f("date"),
            value=f("value"),
        ),
        city=city,
    )


MPLS_DEFAULTS = {
    "url": "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/CCS_Permits/FeatureServer/0",
    "applicant": "ApplicantName",
    "address": "Display",
    "permit_type": "PermitType",
    "work_type": "WorkType",
    "description": "Comments",
    "date": "IssueDate",
    "value": "Value",
}

STPAUL_DEFAULTS = {
    "url": "",
    "applicant": "APPLICANT",
    "address": "ADDRESS",
    "permit_type": "PERMIT_TYPE",
    "work_type": "WORK_TYPE",
    "description": "DESCRIPTION",
    "date": "ISSUE_DATE",
    "value": "VALUATION",
}


@dataclass(frozen=True)
class Settings:
    google_places_api_key: str
    apollo_api_key: str
    apollo_enable_enrich: bool
    db_path: Path
    footprint_csv: Path
    ingest_days: int
    mpls: PermitSource
    stpaul: PermitSource
    news_terms: tuple[str, ...] = field(
        default_factory=lambda: (
            '"grand opening"',
            '"new location"',
            '"is opening"',
            '"to open"',
            "relocating",
            '"new headquarters"',
            '"signed a lease"',
            "expanding",
        )
    )

    @property
    def places_enabled(self) -> bool:
        return bool(self.google_places_api_key)

    @property
    def apollo_enabled(self) -> bool:
        return self.apollo_enable_enrich and bool(self.apollo_api_key)


def load_settings() -> Settings:
    load_dotenv()
    env = os.environ
    return Settings(
        google_places_api_key=env.get("GOOGLE_PLACES_API_KEY", "").strip(),
        apollo_api_key=env.get("APOLLO_API_KEY", "").strip(),
        apollo_enable_enrich=_bool(env.get("APOLLO_ENABLE_ENRICH"), False),
        db_path=Path(env.get("LEADPIPE_DB", "data/leads.sqlite")),
        footprint_csv=Path(env.get("FOOTPRINT_CSV", "data/comcast_footprint_zips.csv")),
        ingest_days=int(env.get("INGEST_DAYS", "7")),
        mpls=_permit_source("MPLS", "mpls_permits", "Minneapolis", MPLS_DEFAULTS),
        stpaul=_permit_source("STPAUL", "stpaul_permits", "Saint Paul", STPAUL_DEFAULTS),
    )
