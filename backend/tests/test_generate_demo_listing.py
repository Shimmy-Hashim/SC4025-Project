import random
from datetime import date

import pytest

import generate_demo_listing as gen
from trust_score.text import specific_tag

EXPECTED_TAG = {"authenticity": "Authenticity", "wrong_item": "Wrong item",
                "mismatch": "Description mismatch"}


@pytest.mark.parametrize("text_class", ["positive", "neutral", "generic_negative"])
def test_non_allegation_templates_never_match_specific_rules(text_class):
    assert [specific_tag(t) for t in gen.TEMPLATES[text_class]] == [None] * len(gen.TEMPLATES[text_class])


@pytest.mark.parametrize("text_class, tag", EXPECTED_TAG.items())
def test_allegation_templates_match_their_tag(text_class, tag):
    assert {specific_tag(t) for t in gen.TEMPLATES[text_class]} == {tag}


def test_seller_reviews_adds_copies_of_first_allegation():
    seller_b = next(s for s in gen.SELLERS if s["id"] == "B")
    rows = gen.seller_reviews(seller_b, random.Random(gen.SEED))
    expected = sum(count for _, _, count in seller_b["mix"]) + seller_b["copies"]
    assert len(rows) == expected
    first_mismatch = gen.TEMPLATES["mismatch"][0]
    assert sum(r["text"] == first_mismatch for r in rows) == 1 + seller_b["copies"]


def test_seller_reviews_are_deterministic_and_within_span():
    seller_c = next(s for s in gen.SELLERS if s["id"] == "C")
    first = gen.seller_reviews(seller_c, random.Random(gen.SEED))
    assert first == gen.seller_reviews(seller_c, random.Random(gen.SEED))
    oldest = date.fromisoformat(min(r["date"] for r in first))
    assert (gen.DATA_CUTOFF - oldest).days < seller_c["span"]


def test_listing_document_complaints_dated_from_cutoff():
    doc = gen.listing_document()
    seller_c = next(s for s in doc["sellers"] if s["id"] == "C")
    assert [(c["date"], c["order_id"]) for c in seller_c["complaints"]] == [
        ("2026-10-25", "C-O-0031"), ("2026-09-30", "C-O-0022"), ("2026-09-27", "C-O-0022"),
        ("2026-08-27", "C-O-0009")]
    assert {s["id"]: s["brand_status"] for s in doc["sellers"]} == {
        "A": "verified", "B": "not_authorised", "C": "not_authorised", "D": "unverified", "E": "unverified"}
    assert doc["data_cutoff"] == "2026-11-06"
