"""Priority score. Higher means call first. Not a probability."""

from __future__ import annotations

SOURCE_WEIGHTS = {
    "places_future": 40,  # pre-opening business with a real listing
    "mpls_permits": 30,  # commercial permit issued
    "stpaul_permits": 30,
    "google_news": 20,  # headline says opening/relocating; needs verification
}

MULTI_SITE_BONUS = 30  # multi-site pays up to $5,000 vs $1,500
PHONE_BONUS = 10
CONTACT_BONUS = 10
NEWS_ONLY_PENALTY = -5  # a headline with nothing corroborating it
UNPARSED_PENALTY = -10  # headline kept for a human, no company name extracted


def score_lead(
    sources: str, distinct_addresses: int, phone: str, contact_email: str, signals: str = ""
) -> int:
    source_list = [s for s in sources.split(",") if s]
    signal_list = [s for s in signals.split(",") if s]
    score = max((SOURCE_WEIGHTS.get(s, 10) for s in source_list), default=0)
    if len(source_list) > 1:
        score += 10
    if distinct_addresses >= 2:
        score += MULTI_SITE_BONUS
    if phone:
        score += PHONE_BONUS
    if contact_email:
        score += CONTACT_BONUS
    if source_list == ["google_news"]:
        score += NEWS_ONLY_PENALTY
    if signal_list and all(s == "news:unparsed" for s in signal_list):
        score += UNPARSED_PENALTY
    return score
