"""CSV export in the column order the referral portal asks for."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

COLUMNS = [
    "contact_name",
    "company_name",
    "contact_email",
    "phone",
    "address",
    "city",
    "state",
    "zip",
    "contact_title",
    "website",
    "signals",
    "sources",
    "signal_date",
    "evidence_url",
    "description",
    "score",
    "first_seen",
    "dedupe_key",
]


def write_csv(rows: list[sqlite3.Row], out_path: str | Path) -> int:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row[c] for c in COLUMNS})
    return len(rows)
