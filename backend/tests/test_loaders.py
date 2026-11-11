import json
from datetime import date

import pytest

from trust_score.models import Complaint
from trust_score.loaders import load_indian_products, load_listing, load_seller_reviews, load_synthetic

REVIEWS_CSV = (
    "seller_id,review_id,reviewer_id,date,stars,text\n"
    "A,A-R0,A-U0,2026-11-01,5,Great phone.\n"
    "B,B-R0,,2026-10-01,1,This phone is fake.\n"
)


def test_load_seller_reviews_groups_by_seller(tmp_path):
    path = tmp_path / "reviews.csv"
    path.write_text(REVIEWS_CSV, encoding="utf-8")
    grouped = load_seller_reviews(path)
    assert sorted(grouped) == ["A", "B"]
    review = grouped["B"][0]
    assert (review.stars, review.review_date, review.reviewer_id) == (1, date(2026, 10, 1), None)


def test_load_listing_builds_context(tmp_path):
    listing = {"data_cutoff": "2026-11-06", "brand": "Apple", "product": {"title": "T"},
               "sellers": [{"id": "A", "name": "Nova", "price": 100, "delivery": "d",
                            "days_selling": 400, "positive_feedback_pct": 98.0,
                            "feedback_count": 10, "brand_status": "verified", "odr_pct": 0.5,
                            "orders_in_window": 40,
                            "complaints": [{"id": "A-C0", "date": "2026-10-30", "order_id": "o1",
                                            "confirmed_counterfeit": True}]},
                           {"id": "B", "name": "New", "price": 90, "delivery": "d",
                            "days_selling": 10, "complaints": None}]}
    (tmp_path / "listing.json").write_text(json.dumps(listing), encoding="utf-8")
    (tmp_path / "reviews.csv").write_text(REVIEWS_CSV, encoding="utf-8")
    product, context = load_listing(tmp_path / "listing.json", tmp_path / "reviews.csv")
    assert product == {"title": "T"}
    assert (context.brand, context.data_cutoff) == ("Apple", date(2026, 11, 6))
    a, b = context.sellers
    assert (len(a.reviews), a.brand_status, a.odr_pct, a.orders_in_window) == (1, "verified", 0.5, 40)
    assert a.complaints[0] == Complaint("A-C0", date(2026, 10, 30), "o1", True)
    assert (b.positive_feedback_pct, b.brand_status, b.feedback_count, b.complaints) == (None, "unverified", 0, None)


def test_load_listing_rejects_unknown_brand_status(tmp_path):
    listing = {"data_cutoff": "2026-11-06", "brand": "Apple", "product": {},
               "sellers": [{"id": "A", "name": "n", "price": 1, "delivery": "d", "days_selling": 1,
                            "brand_status": "yes"}]}
    (tmp_path / "listing.json").write_text(json.dumps(listing), encoding="utf-8")
    (tmp_path / "reviews.csv").write_text(REVIEWS_CSV, encoding="utf-8")
    with pytest.raises(ValueError, match=r"Unknown brand_status for sellers \['A'\]"):
        load_listing(tmp_path / "listing.json", tmp_path / "reviews.csv")


def test_load_indian_products_drops_duplicates_and_missing_text(tmp_path):
    path = tmp_path / "vfl.csv"
    path.write_text(
        "asin,name,date,rating,review\n"
        "X1,p,2020-01-01,1,Fake product\n"
        "X1,p,2020-01-01,1,Fake product\n"
        "X1,p,2020-01-02,5,NA\n"
        "X2,q,2020-01-03,4.0,None\n"
        "X2,q,2020-01-04,4.0,Ok\n", encoding="utf-8")
    grouped = load_indian_products(path)
    assert {k: [r.text for r in v] for k, v in grouped.items()} == {"X1": ["Fake product"], "X2": ["Ok"]}
    assert grouped["X2"][0].stars == 4


def test_load_synthetic_returns_reviews_scenarios_and_research_screen(tmp_path):
    path = tmp_path / "synthetic.csv"
    path.write_text(
        "﻿asin,date,rating,review,review_record_id,synthetic_reviewer_id,"
        "synthetic_scenario,screen_specific_wording\n"
        "S1,2020-01-01,1,This is fake.,S1_a,U1,authenticity_surge,1\n"
        "S1,2020-01-02,5,Good.,S1_b,U2,authenticity_surge,0\n", encoding="utf-8")
    grouped, scenarios, research_specific = load_synthetic(path)
    assert len(grouped["S1"]) == 2
    assert scenarios == {"S1": "authenticity_surge"}
    assert research_specific == {"S1": 1}
