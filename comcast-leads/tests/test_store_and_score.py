from leadpipe.models import Lead
from leadpipe.score import score_lead
from leadpipe.store import Store


def _lead(**kw) -> Lead:
    base = dict(
        source="mpls_permits",
        signal="permit:x",
        company_name="Northstar Dental",
        address="1200 Yankee Doodle Rd",
        zip="55121",
        city="Eagan",
    )
    base.update(kw)
    return Lead(**base)


def test_upsert_creates_then_merges(tmp_path):
    store = Store(tmp_path / "t.sqlite")
    key, created = store.upsert(_lead())
    assert created
    key2, created2 = store.upsert(
        _lead(
            source="google_news",
            signal="news:headline",
            phone="651-555-0100",
            evidence_url="https://x",
        )
    )
    assert key2 == key and not created2
    row = store.get(key)
    assert row["sources"] == "mpls_permits,google_news"
    assert row["signals"] == "permit:x,news:headline"
    assert row["phone"] == "651-555-0100"  # filled because it was empty
    assert row["evidence_url"] == "https://x"


def test_merge_does_not_overwrite_existing_values(tmp_path):
    store = Store(tmp_path / "t.sqlite")
    key, _ = store.upsert(_lead(phone="651-555-0100"))
    store.upsert(_lead(phone="000"))
    assert store.get(key)["phone"] == "651-555-0100"


def test_multi_site_counts_distinct_addresses(tmp_path):
    store = Store(tmp_path / "t.sqlite")
    store.upsert(_lead(address="1200 Yankee Doodle Rd", zip="55121"))
    store.upsert(_lead(address="1200 Yankee Doodle Road", zip="55121"))  # same address, abbreviated
    assert store.distinct_addresses("northstar dental") == 1
    store.upsert(_lead(address="800 Grand Ave", zip="55105", city="St. Paul"))
    assert store.distinct_addresses("northstar dental") == 2


def test_mark_submitted_is_idempotent(tmp_path):
    store = Store(tmp_path / "t.sqlite")
    key, _ = store.upsert(_lead())
    assert store.mark_submitted(key)
    assert not store.mark_submitted(key)
    assert not store.mark_submitted("nope|00000")
    assert store.unsubmitted() == []


def test_needs_enrichment_skips_complete_and_enriched(tmp_path):
    store = Store(tmp_path / "t.sqlite")
    k1, _ = store.upsert(_lead(company_name="A"))
    k2, _ = store.upsert(_lead(company_name="B", phone="1", contact_email="b@x"))
    k3, _ = store.upsert(_lead(company_name="C"))
    store.mark_enriched(k3)
    assert [r["dedupe_key"] for r in store.needs_enrichment(10)] == [k1]


def test_score_ordering():
    news_only = score_lead("google_news", 1, "", "")
    permit = score_lead("mpls_permits", 1, "", "")
    places = score_lead("places_future", 1, "", "")
    multi = score_lead("mpls_permits", 2, "", "")
    corroborated = score_lead("mpls_permits,google_news", 1, "", "")
    full = score_lead("places_future", 2, "651", "a@b")
    assert news_only < permit < places
    assert multi > permit
    assert corroborated > permit
    assert full == 40 + 30 + 10 + 10
    assert score_lead("", 0, "", "") == 0
    unparsed = score_lead("google_news", 1, "", "", signals="news:unparsed")
    assert unparsed < news_only
    # An unparsed headline later corroborated by a permit loses the penalty.
    assert (
        score_lead("google_news,mpls_permits", 1, "", "", signals="news:unparsed,permit:x") > permit
    )
