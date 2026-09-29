from pathlib import Path

from leadpipe.config import Settings, load_settings
from leadpipe.enrich import apollo, places_details
from leadpipe.footprint import Footprint
from leadpipe.models import Lead
from leadpipe.pipeline import enrich, in_footprint, ingest
from leadpipe.store import Store
from tests.conftest import FOOTPRINT_CSV, FakeHttp


def _settings(tmp_path: Path, places_key="", apollo_key="", apollo_on=False) -> Settings:
    base = load_settings()
    return Settings(
        google_places_api_key=places_key,
        apollo_api_key=apollo_key,
        apollo_enable_enrich=apollo_on,
        db_path=tmp_path / "leads.sqlite",
        footprint_csv=FOOTPRINT_CSV,
        ingest_days=7,
        mpls=base.mpls,
        stpaul=base.stpaul,
    )


def test_apollo_domain_and_ranking(fixture_json):
    assert apollo.domain_from_website("https://www.northstardental.example/contact") == (
        "northstardental.example"
    )
    assert apollo.domain_from_website("northstardental.example") == "northstardental.example"
    assert apollo.domain_from_website("") == ""
    http = FakeHttp({"api_search": fixture_json("apollo_search.json")})
    people = apollo.search_people(http, "K", "Northstar Dental", "northstardental.example")
    assert [p.title for p in people][0] == "Owner & Lead Dentist"
    assert all(p.email == "" for p in people)
    body = http.calls[0][2]
    assert body["q_organization_domains_list"] == ["northstardental.example"]


def test_apollo_best_contact_reveals_top_person(fixture_json):
    http = FakeHttp(
        {
            "api_search": fixture_json("apollo_search.json"),
            "people/match": fixture_json("apollo_match.json"),
        }
    )
    person = apollo.best_contact(http, "K", "Northstar Dental", "https://northstardental.example")
    assert person.email == "sam@northstardental.example"
    match_body = http.calls[1][2]
    assert match_body["reveal_phone_number"] is False  # mobiles cost 8 credits; never on


def test_places_details_two_step(fixture_json):
    http = FakeHttp(
        {
            "places:searchText": {
                "places": [
                    {"id": "ChIJx", "displayName": {"text": "Northstar Dental Eagan"}},
                ]
            },
            "/v1/places/ChIJx": {
                "id": "ChIJx",
                "nationalPhoneNumber": "(651) 555-0100",
                "websiteUri": "https://northstardental.example",
            },
        }
    )
    pid = places_details.find_place_id(http, "K", "Northstar Dental", "1200 Yankee Doodle Rd")
    assert pid == "ChIJx"
    c = places_details.fetch_contact(http, "K", pid)
    assert c.phone == "(651) 555-0100"
    assert places_details.find_place_id(http, "K", "", "x") == ""
    assert places_details.fetch_contact(http, "K", "").phone == ""


def test_in_footprint_rules():
    fp = Footprint.load(FOOTPRINT_CSV)
    assert in_footprint(Lead(source="s", signal="x", company_name="A", zip="55401"), fp)
    assert not in_footprint(Lead(source="s", signal="x", company_name="A", zip="55044"), fp)
    assert in_footprint(Lead(source="s", signal="x", company_name="A", city="Eagan"), fp)
    assert not in_footprint(Lead(source="s", signal="x", company_name="A", city="Lakeville"), fp)
    assert not in_footprint(Lead(source="s", signal="x", company_name="A"), fp)


def test_ingest_end_to_end(tmp_path, fixture_json, fixture_text):
    settings = _settings(tmp_path, places_key="PK")
    http = FakeHttp(
        {
            "/query": fixture_json("arcgis_query.json"),
            "news.google.com": fixture_text("google_news.xml"),
            "places:searchText": fixture_json("places_search.json"),
        }
    )
    fp = Footprint.load(FOOTPRINT_CSV)
    store = Store(settings.db_path)
    report = ingest(settings, http, store, fp, ("mpls", "stpaul", "news", "places"))
    assert report.errors == {}
    assert report.fetched == {"mpls": 2, "news": 4, "places": 1}  # stpaul skipped: no URL
    assert report.dropped_out_of_footprint == 0
    rows = {r["company_name"]: r for r in store.all_leads()}
    assert "Greiner Construction" in rows and "Northstar Dental Eagan" in rows
    # The places lead outranks a news-only headline.
    assert rows["Northstar Dental Eagan"]["score"] > rows["Northstar Dental"]["score"]
    assert rows["Fall festival draws crowds to Eagan park"]["score"] < rows["Crumbl"]["score"]


def test_ingest_survives_one_bad_source(tmp_path, fixture_text):
    settings = _settings(tmp_path)
    http = FakeHttp({"news.google.com": fixture_text("google_news.xml")})  # no /query response
    store = Store(settings.db_path)
    report = ingest(settings, http, store, Footprint.load(FOOTPRINT_CSV), ("mpls", "news"))
    assert "mpls" in report.errors
    assert report.fetched == {"news": 4}


def test_enrich_never_calls_apollo_when_disabled(tmp_path, fixture_json):
    settings = _settings(tmp_path, places_key="PK", apollo_key="AK", apollo_on=False)
    store = Store(settings.db_path)
    store.upsert(
        Lead(
            source="mpls_permits",
            signal="p",
            company_name="Northstar Dental",
            address="1200 Yankee Doodle Rd",
            zip="55121",
            city="Eagan",
        )
    )
    http = FakeHttp(
        {
            "places:searchText": {
                "places": [{"id": "ChIJx", "displayName": {"text": "Northstar Dental"}}]
            },
            "/v1/places/ChIJx": {
                "nationalPhoneNumber": "651-555-0100",
                "websiteUri": "https://n.example",
            },
        }
    )
    report = enrich(settings, http, store, limit=10)
    assert report.apollo_skipped and report.phones_found == 1 and report.contacts_found == 0
    assert not any("apollo.io" in url for _, url, _ in http.calls)
    row = store.all_leads()[0]
    assert row["phone"] == "651-555-0100" and row["enriched_at"] != ""


def test_enrich_with_apollo_enabled(tmp_path, fixture_json):
    settings = _settings(tmp_path, places_key="PK", apollo_key="AK", apollo_on=True)
    store = Store(settings.db_path)
    store.upsert(
        Lead(
            source="places_future",
            signal="p",
            company_name="Northstar Dental Eagan",
            address="1200 Yankee Doodle Rd",
            zip="55121",
            city="Eagan",
            raw={"place_id": "ChIJfuture001"},
        )
    )
    http = FakeHttp(
        {
            "/v1/places/ChIJfuture001": {
                "nationalPhoneNumber": "651-555-0100",
                "websiteUri": "https://northstardental.example",
            },
            "api_search": fixture_json("apollo_search.json"),
            "people/match": fixture_json("apollo_match.json"),
        }
    )
    report = enrich(settings, http, store, limit=10)
    assert report.contacts_found == 1
    # Known place_id means no text search was spent.
    assert not any("searchText" in url for _, url, _ in http.calls)
    row = store.all_leads()[0]
    assert row["contact_name"] == "Sam Owner"
    assert row["contact_email"] == "sam@northstardental.example"
    assert row["score"] == 40 + 10 + 10
