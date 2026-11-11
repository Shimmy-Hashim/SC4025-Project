from datetime import date, timedelta

import pytest

from trust_score import constants as c
from trust_score.factors import (
    BrandFactor,
    ComplaintsFactor,
    Factor,
    HistoryFactor,
    ListingContext,
    PriceFactor,
    ReviewsFactor,
    affected_orders,
    reference_prices,
    concern_phrase,
    evaluate_all,
    flagged_reviews,
    format_pct,
    trend_sentence,
)
from trust_score.models import Complaint, FlaggedReview, Review, SellerRecord
from trust_score.review_screen import assess_reviews

CUTOFF = date(2026, 11, 6)
FAKE = "This phone is fake."
WRONG = "Received a different model."
MISMATCH = "Not as described."
GENERIC = "Battery drains fast."
GOOD = "Great phone."


def _seller(seller_id="S", price=100, days=400, pct=95.0, count=1000, odr=None, brand="verified",
            orders=None, reviews=None, complaints=()):
    return SellerRecord(seller_id=seller_id, name=seller_id, price=price, delivery="",
                        days_selling=days, positive_feedback_pct=pct, feedback_count=count,
                        odr_pct=odr, brand_status=brand, orders_in_window=orders,
                        reviews=reviews or [],
                        complaints=None if complaints is None else list(complaints))


def _context(*sellers):
    return ListingContext(brand="Apple", data_cutoff=CUTOFF, sellers=list(sellers))


def _reviews(spec):
    """spec: list of (count, stars, text); dated one day apart before the cutoff."""
    out = []
    for count, stars, text in spec:
        for _ in range(count):
            i = len(out)
            out.append(Review(f"r{i}", stars, CUTOFF - timedelta(days=i), text, f"u{i}"))
    return out


def test_factor_base_is_abstract():
    with pytest.raises(TypeError, match="abstract"):
        Factor()  # type: ignore[abstract]


def test_factor_helpers_set_source_and_severity():
    factor = BrandFactor()
    assert factor.result("pass", "s", "t").severity is None
    assert (factor.concern("s", "t").status, factor.concern("s", "t").severity) == ("warn", "concern")
    assert (factor.alert("s", "t").status, factor.alert("s", "t").severity) == ("warn", "alert")
    assert factor.alert("s", "t").source == c.SOURCE_BRAND


# History: age gives evidence, not trust
def test_history_na_below_90_days():
    result = HistoryFactor().evaluate(_seller(days=89), _context())
    assert (result.status, result.short) == ("na", c.HISTORY_NA_SHORT)
    assert result.text == c.HISTORY_NA_TEXT.format(duration="2 months")


@pytest.mark.parametrize("pct, count, shown", [(None, 1000, "1,000"), (99.0, 19, "19")])
def test_history_limited_without_feedback_or_under_20_ratings(pct, count, shown):
    result = HistoryFactor().evaluate(_seller(pct=pct, count=count), _context())
    assert (result.status, result.short) == ("na", c.HISTORY_LIMITED_SHORT.format(count=shown))


def test_history_young_seller_with_good_record_passes():
    result = HistoryFactor().evaluate(_seller(days=125, pct=96.0, count=60), _context())
    assert result.status == "pass"
    assert result.short == c.HISTORY_PASS_SHORT.format(duration="4 months", pct=96)


def test_history_pass_at_exactly_90_percent_and_20_ratings():
    result = HistoryFactor().evaluate(_seller(days=90, pct=90.0, count=20), _context())
    assert result.status == "pass"
    assert result.text == c.HISTORY_TEXT.format(duration="3 months", pct=90, count="20")


def test_history_concern_below_90_percent_shows_floored_pct():
    result = HistoryFactor().evaluate(_seller(pct=89.9), _context())
    assert (result.status, result.severity) == ("warn", "concern")
    assert result.short == c.HISTORY_WARN_FEEDBACK_SHORT.format(pct=89)


def test_history_concern_at_odr_target_and_odr_in_text():
    result = HistoryFactor().evaluate(_seller(odr=1.0), _context())
    assert (result.status, result.short) == ("warn", c.HISTORY_WARN_ODR_SHORT.format(odr="1"))
    assert result.text.endswith(c.HISTORY_ODR_TEXT.format(odr="1"))


def test_history_odr_below_target_passes():
    assert HistoryFactor().evaluate(_seller(odr=0.99), _context()).status == "pass"


# Brand: unverified is not the same as confirmed unauthorised
@pytest.mark.parametrize("brand, status, severity, short", [
    ("verified", "pass", None, c.BRAND_PASS_SHORT.format(brand="Apple")),
    ("not_authorised", "warn", "concern", c.BRAND_WARN_SHORT),
    ("contradicted", "warn", "alert", c.BRAND_ALERT_SHORT),
    ("unverified", "na", None, c.BRAND_NA_SHORT),
])
def test_brand_states(brand, status, severity, short):
    result = BrandFactor().evaluate(_seller(brand=brand), _context())
    assert (result.status, result.severity, result.short) == (status, severity, short)


# Price: severity, not just a warning
def _price_result(price, others):
    me = _seller("me", price=price)
    rest = [_seller(f"o{i}", price=p) for i, p in enumerate(others)]
    return PriceFactor().evaluate(me, _context(me, *rest))


def test_price_exactly_30_percent_below_passes():
    result = _price_result(70000, [100000, 100000, 100000])
    assert result.status == "pass"
    assert result.text == c.PRICE_PASS_TEXT.format(price="₹70,000", typical="₹1,00,000", n=3)


def test_price_just_over_30_percent_is_a_concern_with_rounded_up_pct():
    result = _price_result(69999, [100000, 100000, 100000])
    assert (result.status, result.severity) == ("warn", "concern")
    assert result.short == c.PRICE_WARN_SHORT.format(pct=31)


def test_price_exactly_70_percent_below_is_still_a_concern():
    assert _price_result(30000, [100000, 100000]).severity == "concern"


def test_price_more_than_70_percent_below_is_an_alert():
    result = _price_result(4999, [254900, 249990, 164999, 252000])
    assert (result.status, result.severity) == ("warn", "alert")
    assert result.short == c.PRICE_ALERT_SHORT.format(pct=99)
    assert result.text == c.PRICE_ALERT_TEXT.format(price="₹4,999", pct=99, typical="₹2,50,995", n=4)


def test_price_reference_excludes_extreme_outliers():
    # without excluding ₹4,999 the reference median would be ₹2,07,495 and this would pass
    result = _price_result(169999, [249990, 164999, 252000, 4999])
    assert (result.severity, result.short) == ("concern", c.PRICE_WARN_SHORT.format(pct=32))
    assert result.text == c.PRICE_WARN_TEXT.format(price="₹1,69,999", pct=32, typical="₹2,49,990", n=3)


def test_reference_prices_keeps_outlier_seller_own_comparison():
    me = _seller("me", price=4999)
    rest = [_seller(f"o{i}", price=p) for i, p in enumerate([254900, 249990, 164999, 252000])]
    assert sorted(reference_prices(me, [me, *rest])) == [164999, 249990, 252000, 254900]


def test_price_na_with_fewer_than_two_other_sellers():
    result = _price_result(100, [100])
    assert (result.status, result.short) == ("na", c.PRICE_NA_SHORT)


# Reviews: interpreted allegations, never alerts
def test_reviews_na_below_20_reviews():
    result = ReviewsFactor().evaluate(_seller(reviews=_reviews([(19, 5, GOOD)])), _context())
    assert result.status == "na"
    assert result.text == c.REVIEWS_NA_TEXT.format(n=19)
    assert (result.flagged, result.excluded_duplicates) == ([], 0)


def test_reviews_pass_with_exactly_20_reviews_and_no_allegations():
    result = ReviewsFactor().evaluate(_seller(reviews=_reviews([(20, 5, GOOD)])), _context())
    assert (result.status, result.short, result.text) == ("pass", c.REVIEWS_PASS_SHORT, c.REVIEWS_PASS_TEXT)


def test_reviews_isolated_allegation_passes_and_is_mentioned():
    result = ReviewsFactor().evaluate(_seller(reviews=_reviews([(1, 1, FAKE), (29, 5, GOOD)])), _context())
    assert (result.status, result.short) == ("pass", c.REVIEWS_ISOLATED_SHORT)
    assert result.text == c.REVIEWS_ISOLATED_TEXT.format(n=30, concern=c.CONCERN_WORDING["Authenticity"][0])
    assert result.flagged == [FlaggedReview("Authenticity", 1, FAKE)]


def test_reviews_repeated_allegations_are_a_concern_not_an_alert():
    reviews = _reviews([(1, 1, FAKE), (1, 2, "Not an original unit."), (28, 5, GOOD)])
    result = ReviewsFactor().evaluate(_seller(reviews=reviews), _context())
    assert (result.status, result.severity) == ("warn", "concern")
    assert result.text == (c.REVIEWS_REPEATED_TEXT.format(
        k=2, n=30, concern=c.CONCERN_WORDING["Authenticity"][0]) + c.REVIEWS_TREND_UNAVAILABLE)


def test_reviews_context_stage_drops_negated_and_other_review_mentions():
    reviews = _reviews([(1, 1, "This is not fake; delivery was slow."),
                        (1, 1, "Fake reviews everywhere, battery is poor."), (28, 5, GOOD)])
    result = ReviewsFactor().evaluate(_seller(reviews=reviews), _context())
    assert (result.status, result.short) == ("pass", c.REVIEWS_PASS_SHORT)


def test_reviews_concentration_concern_mentions_copies():
    reviews = _reviews([(3, 1, FAKE), (5, 1, GENERIC), (12, 5, GOOD)])
    result = ReviewsFactor().evaluate(_seller(reviews=reviews), _context())
    assert (result.status, result.short) == ("warn", c.REVIEWS_CONCENTRATION_SHORT.format(
        concern_short=c.CONCERN_WORDING["Authenticity"][1]))
    assert result.text.endswith(c.REVIEWS_DUPLICATES.format(k=2))
    assert result.excluded_duplicates == 2


def test_concern_phrase_single_and_mixed_tags():
    assert concern_phrase(_reviews([(1, 1, WRONG)])) == c.CONCERN_WORDING["Wrong item"][0]
    mixed = _reviews([(1, 1, MISMATCH), (1, 1, "Not as shown."), (1, 1, WRONG)])
    assert concern_phrase(mixed) == c.CONCERN_JOINER.join([
        c.CONCERN_WITH_COUNT.format(concern=c.CONCERN_WORDING["Description mismatch"][0], n=2),
        c.CONCERN_WITH_COUNT.format(concern=c.CONCERN_WORDING["Wrong item"][0], n=1)])


@pytest.mark.parametrize("rising, sentence", [
    (True, c.REVIEWS_TREND_RISING), (False, c.REVIEWS_TREND_NOT_RISING), (None, c.REVIEWS_TREND_UNAVAILABLE)])
def test_trend_sentence(rising, sentence):
    assert trend_sentence(rising) == sentence


def test_flagged_reviews_capped_at_five_newest_first():
    texts = [FAKE, WRONG, MISMATCH, "Not as shown.", "Not an original unit.", "Duplicate item."]
    flagged = flagged_reviews(assess_reviews(_reviews([(1, 1, t) for t in texts])))
    assert [f.text for f in flagged] == texts[:5]


# Complaints: unknown vs zero, per order, exposure, confirmed findings
def _complaints(*specs):
    """specs: (days before cutoff, order id or None, confirmed)."""
    return [Complaint(f"c{i}", CUTOFF - timedelta(days=d), order, confirmed)
            for i, (d, order, confirmed) in enumerate(specs)]


def test_complaints_unavailable_is_not_zero():
    result = ComplaintsFactor().evaluate(_seller(complaints=None), _context())
    assert (result.status, result.short) == ("na", c.COMPLAINTS_UNAVAILABLE_SHORT)


def test_complaints_na_for_new_seller():
    result = ComplaintsFactor().evaluate(_seller(days=89), _context())
    assert (result.status, result.short) == ("na", c.COMPLAINTS_NA_SHORT)


def test_complaints_zero_and_single_order_pass():
    assert ComplaintsFactor().evaluate(_seller(), _context()).text == c.COMPLAINTS_PASS_TEXT
    single = _seller(complaints=_complaints((5, "o1", False), (6, "o1", False)))
    assert ComplaintsFactor().evaluate(single, _context()).short == c.COMPLAINTS_SINGLE_SHORT


def test_complaints_two_orders_without_volume_is_a_concern():
    seller = _seller(complaints=_complaints((0, "o1", False), (89, "o2", False)))
    result = ComplaintsFactor().evaluate(seller, _context())
    assert (result.status, result.severity, result.text) == ("warn", "concern", c.COMPLAINTS_WARN_TEXT.format(n=2))


def test_complaints_two_of_twenty_orders_shows_rate():
    seller = _seller(orders=20, complaints=_complaints((1, "o1", False), (2, "o2", False)))
    result = ComplaintsFactor().evaluate(seller, _context())
    assert result.status == "warn"
    assert result.text.endswith(c.COMPLAINTS_RATE_TEXT.format(n=2, orders="20", rate="10"))


def test_complaints_two_of_twenty_thousand_orders_passes():
    seller = _seller(orders=20000, complaints=_complaints((1, "o1", False), (2, "o2", False)))
    result = ComplaintsFactor().evaluate(seller, _context())
    assert (result.status, result.short) == ("pass", c.COMPLAINTS_LOW_RATE_SHORT.format(n=2, orders="20,000"))


def test_complaints_confirmed_finding_is_an_alert_even_for_new_seller():
    seller = _seller(days=30, complaints=_complaints((10, "o1", True)))
    result = ComplaintsFactor().evaluate(seller, _context())
    assert (result.status, result.severity, result.short) == ("warn", "alert", c.COMPLAINTS_ALERT_SHORT)
    assert result.text == c.COMPLAINTS_ALERT_TEXT.format(date="27 Oct 2026")


def test_complaints_old_confirmed_finding_outside_lookback_is_ignored():
    seller = _seller(complaints=_complaints((365, "o1", True)))
    assert ComplaintsFactor().evaluate(seller, _context()).text == c.COMPLAINTS_PASS_TEXT


def test_affected_orders_counts_each_order_once_and_ignores_outside_window():
    seller = _seller(complaints=_complaints((1, "o1", False), (2, "o1", False), (3, None, False),
                                            (90, "o9", False)) + [Complaint("future", CUTOFF + timedelta(days=1))])
    assert affected_orders(seller, CUTOFF) == 2


@pytest.mark.parametrize("value, text", [(0.5, "0.5"), (10.0, "10"), (7.894, "7.89"), (1.0, "1")])
def test_format_pct(value, text):
    assert format_pct(value) == text


def test_evaluate_all_returns_every_factor():
    me = _seller("me")
    results = evaluate_all(me, _context(me, _seller("a"), _seller("b")))
    assert list(results) == ["history", "brand", "price", "reviews", "complaints"]
