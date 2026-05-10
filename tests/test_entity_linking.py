from counterparty_sentiment.entity_linking import enrich_with_entity, link_company


def test_link_company_maps_major_name_to_ticker():
    link = link_company("Lockheed Martin won a new defense contract")

    assert link.ticker == "LMT"
    assert link.canonical_name == "Lockheed Martin"
    assert link.confidence >= 0.9


def test_enrich_with_entity_adds_ticker_and_canonical_counterparty():
    row = enrich_with_entity({"headline": "JPMorgan reports stable credit trends", "text": "JPMorgan remains well capitalized."})

    assert row["ticker"] == "JPM"
    assert row["counterparty"] == "JPMorgan Chase"
    assert row["entity_link"]["confidence"] >= 0.9
