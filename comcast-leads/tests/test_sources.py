from leadpipe.config import MPLS_DEFAULTS, PermitFieldMap, PermitSource
from leadpipe.sources import arcgis_permits, google_news, places_future
from tests.conftest import FakeHttp

MPLS = PermitSource(
    name="mpls_permits",
    url=MPLS_DEFAULTS["url"],
    city="Minneapolis",
    fields=PermitFieldMap(**{k: v for k, v in MPLS_DEFAULTS.items() if k != "url"}),
)


def test_permits_keep_commercial_only(fixture_json):
    leads = arcgis_permits.parse_features(fixture_json("arcgis_query.json")["features"], MPLS)
    names = [ld.company_name for ld in leads]
    assert names == ["Greiner Construction", "Ryan Companies"]
    first = leads[0]
    assert first.zip == "55401"
    assert first.city == "Minneapolis"
    assert first.signal == "permit:commercial remodel"
    assert first.signal_date == "2026-09-25"
    assert "Northstar Dental" in first.description
    assert first.raw["value"] == 425000


def test_permits_paging_and_where_clause(fixture_json):
    page = fixture_json("arcgis_query.json")
    http = FakeHttp({"/query": page})
    leads = arcgis_permits.fetch_permits(http, MPLS, since_days=7)
    assert len(leads) == 2
    method, url, params = http.calls[0]
    assert url.endswith("/query")
    assert params["where"].startswith("IssueDate >= TIMESTAMP '")
    assert params["resultOffset"] == 0


def test_permits_skip_when_url_blank():
    src = PermitSource(name="stpaul_permits", url="", city="Saint Paul", fields=MPLS.fields)
    assert arcgis_permits.fetch_permits(FakeHttp(), src, 7) == []


def test_is_commercial():
    assert arcgis_permits.is_commercial("Building", "Commercial Remodel", "")
    assert not arcgis_permits.is_commercial("Building", "Residential Remodel", "single family")
    assert not arcgis_permits.is_commercial("Plumbing", "", "")


def test_news_company_extraction():
    ex = google_news.extract_company
    assert (
        ex("Northstar Dental to open second clinic in Eagan - Star Tribune") == "Northstar Dental"
    )
    assert ex("Minneapolis-based Lakes Physical Therapy relocating to Woodbury - BMTN") == (
        "Lakes Physical Therapy"
    )
    assert ex("Crumbl's new location in Blaine set for October - Patch") == "Crumbl"
    assert ex("Fall festival draws crowds to Eagan park - Sun Thisweek") == ""


def test_news_feed_to_leads(fixture_text, footprint):
    items = google_news.parse_feed(fixture_text("google_news.xml"))
    assert len(items) == 4
    assert items[0]["published"] == "2026-09-28"
    assert items[0]["outlet"] == "Star Tribune"
    leads = google_news.items_to_leads(items, footprint, query_city="Eagan")
    by_name = {ld.company_name: ld for ld in leads}
    assert by_name["Northstar Dental"].city == "Eagan"
    assert by_name["Lakes Physical Therapy"].city == "Woodbury"  # headline city beats query city
    assert by_name["Crumbl"].city == "Blaine"
    unparsed = [ld for ld in leads if ld.signal == "news:unparsed"]
    assert len(unparsed) == 1 and unparsed[0].company_name.startswith("Fall festival")


def test_news_query_and_url(footprint):
    q = google_news.build_query(('"grand opening"', "relocating"), "Eagan", 7)
    assert q == '("grand opening" OR relocating) "Eagan" Minnesota when:7d'
    assert google_news.feed_url(q).startswith("https://news.google.com/rss/search?q=%28")


def test_news_fetch_dedupes_links_across_cities(fixture_text, footprint):
    http = FakeHttp({"news.google.com": fixture_text("google_news.xml")})
    leads = google_news.fetch_news(http, footprint, ('"new location"',), 7)
    assert len(http.calls) == len(footprint.city_labels())
    assert len(leads) == 4  # same 4 links returned for every city, counted once


def test_places_future_filters_status_and_footprint(fixture_json, footprint):
    leads = places_future.parse_places(fixture_json("places_search.json")["places"], footprint)
    assert [ld.company_name for ld in leads] == ["Northstar Dental Eagan"]
    ld = leads[0]
    assert ld.zip == "55121" and ld.city == "Eagan" and ld.state == "MN"
    assert ld.raw["place_id"] == "ChIJfuture001"
    assert "place_id:ChIJfuture001" in ld.evidence_url


def test_places_future_fetch_uses_pro_mask(fixture_json, footprint):
    http = FakeHttp({"places:searchText": fixture_json("places_search.json")})
    leads = places_future.fetch_future_openings(http, "KEY", footprint)
    assert len(leads) == 1  # dedupe by place id across every city query
    assert "nationalPhoneNumber" not in places_future.FIELD_MASK
