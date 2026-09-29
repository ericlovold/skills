"""Decision-maker name, title and email from Apollo.io.

Spends credits. Nothing here runs unless settings.apollo_enabled is true,
which requires both an API key and APOLLO_ENABLE_ENRICH=true.

Flow: people search by company domain (or name) and title list, which costs
no credits, then one people/match with reveal to unlock the email of the
best-ranked person, which costs about one credit. Mobile reveal is off.

Endpoint paths are from Apollo's public docs. Parameter names were not
exercised against a live key; see README.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from leadpipe.http import Http

SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/api_search"
MATCH_URL = "https://api.apollo.io/api/v1/people/match"

# Ordered: earlier titles win when several people match.
TITLE_PRIORITY = (
    "owner",
    "founder",
    "ceo",
    "president",
    "managing partner",
    "principal",
    "general manager",
    "office manager",
    "operations manager",
    "it manager",
    "practice manager",
    "director of operations",
    "controller",
)


@dataclass
class Person:
    name: str = ""
    title: str = ""
    email: str = ""
    apollo_id: str = ""


def domain_from_website(website: str) -> str:
    if not website:
        return ""
    host = urlparse(website if "://" in website else f"https://{website}").netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _rank(title: str) -> int:
    t = (title or "").lower()
    for i, key in enumerate(TITLE_PRIORITY):
        if key in t:
            return i
    return len(TITLE_PRIORITY)


def _headers(api_key: str) -> dict:
    return {"x-api-key": api_key, "Content-Type": "application/json", "Cache-Control": "no-cache"}


def search_people(http: Http, api_key: str, company_name: str, domain: str) -> list[Person]:
    body: dict = {"person_titles": list(TITLE_PRIORITY), "page": 1, "per_page": 10}
    if domain:
        body["q_organization_domains_list"] = [domain]
    elif company_name:
        body["q_organization_name"] = company_name
    else:
        return []
    page = http.post_json(SEARCH_URL, body, headers=_headers(api_key))
    people = [
        Person(
            name=p.get("name", "") or "",
            title=p.get("title", "") or "",
            email="",  # search never returns real emails; match does
            apollo_id=p.get("id", "") or "",
        )
        for p in page.get("people", [])
    ]
    return sorted(people, key=lambda p: _rank(p.title))


def reveal_email(http: Http, api_key: str, person: Person) -> Person:
    if not person.apollo_id:
        return person
    d = http.post_json(
        MATCH_URL,
        {"id": person.apollo_id, "reveal_personal_emails": False, "reveal_phone_number": False},
        headers=_headers(api_key),
    )
    p = d.get("person", {}) or {}
    email = p.get("email", "") or ""
    if email.startswith("email_not_unlocked"):
        email = ""
    return Person(
        name=p.get("name", "") or person.name,
        title=p.get("title", "") or person.title,
        email=email,
        apollo_id=person.apollo_id,
    )


def best_contact(http: Http, api_key: str, company_name: str, website: str) -> Person | None:
    people = search_people(http, api_key, company_name, domain_from_website(website))
    if not people:
        return None
    return reveal_email(http, api_key, people[0])
