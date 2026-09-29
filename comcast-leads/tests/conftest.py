from __future__ import annotations

import json
from pathlib import Path

import pytest

from leadpipe.footprint import Footprint

FIXTURES = Path(__file__).parent / "fixtures"
FOOTPRINT_CSV = Path(__file__).parent.parent / "data" / "comcast_footprint_zips.csv"


class FakeHttp:
    """Records requests and replays canned responses keyed by URL substring."""

    def __init__(self, responses: dict[str, object] | None = None):
        self.responses = responses or {}
        self.calls: list[tuple[str, str, dict | None]] = []

    def _lookup(self, url: str):
        for needle, resp in self.responses.items():
            if needle in url:
                return resp
        raise AssertionError(f"no fake response for {url}")

    def get_json(self, url, params=None, headers=None):
        self.calls.append(("GET", url, params))
        return self._lookup(url)

    def get_text(self, url, params=None, headers=None):
        self.calls.append(("GET", url, params))
        return self._lookup(url)

    def post_json(self, url, body, headers=None):
        self.calls.append(("POST", url, body))
        resp = self._lookup(url)
        return resp(body) if callable(resp) else resp


@pytest.fixture
def footprint() -> Footprint:
    return Footprint.load(FOOTPRINT_CSV)


@pytest.fixture
def fixture_json():
    def load(name: str):
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    return load


@pytest.fixture
def fixture_text():
    def load(name: str) -> str:
        return (FIXTURES / name).read_text(encoding="utf-8")

    return load
