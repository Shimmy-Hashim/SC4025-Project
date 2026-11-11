from datetime import date, timedelta
from pathlib import Path

import pytest

from trust_score import constants as c
from trust_score.config import FACTOR_WEIGHTS
from trust_score.factors import ListingContext
from trust_score.loaders import load_listing
from trust_score.models import FactorResult, Review, SellerRecord
from trust_score.scoring import (
    alert_factors,
    apply_cap,
    base_band,
    eligibility_reason,
    pick_inline,
    score_offer,
    weighted_score,
)

BACKEND = Path(__file__).resolve().parent.parent
CUTOFF = date(2026, 11, 6)
GOOD = "Great phone."
KEYS = ["history", "brand", "price", "reviews", "complaints"]


def _factors(**statuses):
    """statuses: key -> "pass" | "na" | "concern" | "alert"."""
    out = {}
    for k in KEYS:
        s = statuses.get(k, "pass")
        if s in ("concern", "alert"):
            out[k] = FactorResult("warn", f"{k} {s}", "t", "src", severity=s)
        else:
            out[k] = FactorResult(s, "s", "t", "src")
    return out


def _seller(seller_id="S", days=400, n_reviews=20, price=100, brand="verified"):
    reviews = [Review(f"r{i}", 5, CUTOFF - timedelta(days=i), GOOD, f"u{i}") for i in range(n_reviews)]
    return SellerRecord(seller_id=seller_id, name=seller_id, price=price, delivery="", days_selling=days,
                        positive_feedback_pct=95.0, feedback_count=100, brand_status=brand, reviews=reviews)


def test_weights_total_100():
    assert sum(FACTOR_WEIGHTS.values()) == 100


def test_eligibility_passes_at_exactly_90_days_and_20_reviews():
    assert eligibility_reason(_seller(days=90, n_reviews=20)) is None


def test_eligibility_reasons():
    assert eligibility_reason(_seller(days=21, n_reviews=2)) == c.REASON_NEW_AND_FEW_REVIEWS.format(duration="3 weeks", n=2)
    assert eligibility_reason(_seller(days=89)) == c.REASON_NEW.format(duration="2 months")


def test_eligibility_reason_few_reviews_counts_after_dedupe():
    seller = _seller(n_reviews=20)
    seller.reviews.append(seller.reviews[0])
    seller.reviews.pop(1)
    assert eligibility_reason(seller) == c.REASON_FEW_REVIEWS.format(n=19)


def test_weighted_score_all_pass_is_100():
    assert weighted_score(_factors()) == 100


def test_weighted_score_excludes_na_instead_of_counting_zero():
    # brand (16) na: 84 available; complaints (26) warn: 58 earned -> 69.05 -> 69 (as 0 it would be 58)
    assert weighted_score(_factors(brand="na", complaints="concern")) == 69


def test_weighted_score_rounds_half_up():
    # history (12) na: 88 available; brand 16 + price 17 earned = 33 -> 37.5 -> 38
    assert weighted_score(_factors(history="na", reviews="concern", complaints="concern")) == 38


def test_weighted_score_raises_when_every_factor_na():
    with pytest.raises(ValueError, match="Score is undefined when every factor is na"):
        weighted_score(_factors(**{k: "na" for k in KEYS}))


@pytest.mark.parametrize("score, band", [(100, "High"), (75, "High"), (74, "Medium"),
                                         (50, "Medium"), (49, "Low"), (0, "Low")])
def test_base_band_cut_offs(score, band):
    assert base_band(score) == band


@pytest.mark.parametrize("key, score, band", [
    ("history", 88, "High"),     # history does not cap
    ("brand", 84, "Medium"),     # capped
    ("price", 83, "Medium"),     # capped
    ("complaints", 74, "Medium"),
    ("reviews", 71, "Medium"),
])
def test_single_concern_outcomes(key, score, band):
    factors = _factors(**{key: "concern"})
    assert weighted_score(factors) == score
    assert apply_cap(base_band(score), factors) == band


def test_cap_never_raises_a_low_band():
    assert apply_cap("Low", _factors(reviews="concern")) == "Low"


def test_alert_factors_in_factor_order():
    assert alert_factors(_factors(price="alert", brand="alert", reviews="concern")) == ["brand", "price"]


def test_pick_inline_puts_alerts_then_warnings_first():
    assert pick_inline(_factors(reviews="concern", brand="alert")) == ["brand", "reviews", "price"]
    assert pick_inline(_factors()) == ["price", "history", "brand"]


def test_score_offer_alert_forces_low_even_when_score_is_high():
    me = _seller("me", price=10)
    context = ListingContext("Apple", CUTOFF, [me, _seller("a", price=1000), _seller("b", price=1000)])
    offer = score_offer(me, context)
    assert (offer.score, offer.band) == (83, "Low")
    assert offer.alert == offer.factors["price"].short


def test_score_offer_not_enough_data_keeps_alert_visible():
    me = _seller("me", days=30, n_reviews=3, price=10, brand="unverified")
    context = ListingContext("Apple", CUTOFF, [me, _seller("a", price=1000), _seller("b", price=1000)])
    offer = score_offer(me, context)
    assert (offer.band, offer.score) == ("Not enough data", None)
    assert offer.reason == c.REASON_NEW_AND_FEW_REVIEWS.format(duration="1 month", n=3) + c.REASON_SEE_ALERT
    assert offer.alert == offer.factors["price"].short


def test_score_offer_two_na_factors_after_gate_is_not_enough_data():
    me = _seller("me", brand="unverified")
    offer = score_offer(me, ListingContext("Apple", CUTOFF, [me]))  # no other sellers -> price na
    assert (offer.band, offer.score, offer.alert) == ("Not enough data", None, None)
    assert offer.reason == c.REASON_MISSING_FACTORS + c.REASON_NOT_A_WARNING


def test_demo_personas():
    _, context = load_listing(BACKEND / "inputs/demo_listing.json", BACKEND / "inputs/demo_reviews.csv")
    offers = {s.seller_id: score_offer(s, context) for s in context.sellers}
    statuses = {k: [f"{f.status}:{f.severity}" if f.severity else f.status for f in o.factors.values()]
                for k, o in offers.items()}
    assert statuses == {
        "A": ["pass", "pass", "pass", "pass", "pass"],
        "B": ["pass", "warn:concern", "pass", "warn:concern", "pass"],
        "C": ["warn:concern"] * 5,
        "D": ["na", "na", "pass", "na", "na"],
        "E": ["na", "na", "warn:alert", "na", "na"],
    }
    assert {k: (o.score, o.band, o.alert is not None) for k, o in offers.items()} == {
        "A": (100, "High", False), "B": (55, "Medium", False), "C": (0, "Low", False),
        "D": (None, "Not enough data", False), "E": (None, "Not enough data", True)}
