"""Serviceable-zip filter from the Comcast rep's list."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from leadpipe.normalize import normalize_address


@dataclass(frozen=True)
class FootprintRow:
    zip: str
    state: str
    city_label: str
    region: str


class Footprint:
    def __init__(self, rows: list[FootprintRow]):
        self.by_zip: dict[str, FootprintRow] = {r.zip: r for r in rows}
        # City tokens used to match news headlines. "St. Paul (Highland Park)" -> "st paul".
        self._city_tokens: dict[str, str] = {}
        for r in rows:
            base = r.city_label.split("(")[0]
            for part in base.split("/"):
                token = normalize_address(part).replace("saint ", "st ")
                if len(token) >= 4:
                    self._city_tokens.setdefault(token, r.city_label.split("(")[0].strip())

    @classmethod
    def load(cls, path: str | Path) -> Footprint:
        with open(path, newline="", encoding="utf-8") as fh:
            rows = [
                FootprintRow(
                    zip=row["zip"].strip(),
                    state=row["state"].strip(),
                    city_label=row["city_label"].strip(),
                    region=row["region"].strip(),
                )
                for row in csv.DictReader(fh)
            ]
        return cls(rows)

    def contains_zip(self, zip_code: str) -> bool:
        return zip_code.strip()[:5] in self.by_zip

    def match_city(self, text: str) -> str:
        """Return the footprint city mentioned last in text, or empty string.

        Last wins because relocation headlines name the destination last
        ("Eagan clinic moving to Woodbury"). Longer tokens are checked first so
        "st paul park" is not shadowed by "st paul".
        """
        hay = " " + normalize_address(text).replace("saint ", "st ") + " "
        best_label, best_pos = "", -1
        for token, label in sorted(self._city_tokens.items(), key=lambda kv: -len(kv[0])):
            pos = hay.rfind(f" {token} ")
            if pos > best_pos:
                best_label, best_pos = label, pos
        return best_label

    def city_labels(self) -> list[str]:
        seen: dict[str, None] = {}
        for label in self._city_tokens.values():
            seen.setdefault(label, None)
        return list(seen)

    def zips(self) -> list[str]:
        return sorted(self.by_zip)
