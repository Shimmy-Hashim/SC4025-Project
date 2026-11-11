from datetime import date, timedelta

import pytest

from trust_score.models import Review
from trust_score.review_screen import (
    allegation_share,
    assess_reviews,
    collapse_allegations,
    dedupe_records,
    distinct_allegation_texts,
    is_allegation,
    is_candidate,
    is_high_star,
    is_low_star,
    low_star_share,
    main_concern,
    split_windows,
    tag_counts,
    trend_rising,
)

END = date(2026, 6, 30)
FAKE = "This phone is fake."
FAKE_2 = "Serial check failed, counterfeit unit."
WRONG = "Received a different model."
MISMATCH = "Not as described."
GENERIC = "Battery drains fast."
GOOD = "Great phone."

_counter = [0]


def _review(stars, text, days_before_end=0, reviewer=None):
    _counter[0] += 1
    return Review(review_id=f"r{_counter[0]}", stars=stars, text=text,
                  review_date=END - timedelta(days=days_before_end),
                  reviewer_id=reviewer or f"u{_counter[0]}")


def _many(n, stars, text, days_before_end=0):
    return [_review(stars, text, days_before_end) for _ in range(n)]


def test_dedupe_records_drops_exact_duplicates_only():
    a = _review(1, FAKE, 3, reviewer="x")
    same = Review("other-id", 1, a.review_date, FAKE, "x")
    other_reviewer = Review("id3", 1, a.review_date, FAKE, "y")
    assert dedupe_records([a, same, other_reviewer]) == [a, other_reviewer]


@pytest.mark.parametrize("stars, low, high", [(1, True, False), (2, True, False),
                                              (3, False, False), (4, False, True), (5, False, True)])
def test_star_groups(stars, low, high):
    review = _review(stars, GOOD)
    assert is_low_star(review) is low
    assert is_high_star(review) is high


def test_is_allegation_needs_low_star_and_specific_wording():
    assert is_allegation(_review(2, FAKE)) is True
    assert is_allegation(_review(3, FAKE)) is False
    assert is_allegation(_review(1, GENERIC)) is False


def test_low_star_share_is_bounded():
    assert low_star_share(5, 15) == 0.25


def test_low_star_share_with_no_high_stars_is_100_percent():
    assert low_star_share(20, 0) == 1.0


def test_low_star_share_raises_when_undefined():
    with pytest.raises(ValueError, match="Low-star share is undefined"):
        low_star_share(0, 0)


def test_split_windows_boundaries():
    at_end = _review(5, GOOD, 0)
    at_90 = _review(5, GOOD, 90)
    at_179 = _review(5, GOOD, 179)
    at_180 = _review(5, GOOD, 180)
    recent, previous = split_windows([at_end, at_90, at_179, at_180], END)
    assert recent == [at_end]
    assert previous == [at_90, at_179]


def test_allegation_share_and_distinct_texts():
    window = [_review(1, FAKE), _review(1, FAKE), _review(5, GOOD), _review(5, GOOD)]
    assert allegation_share(window) == 0.5
    assert distinct_allegation_texts(window) == 1


def _trend_listing(recent_allegations, previous_allegations, recent_n=10, previous_n=10):
    recent = recent_allegations + _many(recent_n - len(recent_allegations), 5, GOOD, 10)
    previous = previous_allegations + _many(previous_n - len(previous_allegations), 5, GOOD, 100)
    return recent + previous


def test_trend_rising_true_when_share_rises_with_two_distinct_texts():
    reviews = _trend_listing([_review(1, FAKE, 5), _review(1, WRONG, 6)], [])
    assert trend_rising(reviews) is True


def test_trend_rising_false_when_share_flat():
    reviews = _trend_listing([_review(1, FAKE, 5)], [_review(1, WRONG, 100)])
    assert trend_rising(reviews) is False


def test_trend_rising_false_when_rise_is_one_copied_text():
    reviews = _trend_listing([_review(1, FAKE, 5), _review(1, FAKE, 6)], [])
    assert trend_rising(reviews) is False


def test_trend_rising_none_when_a_window_has_fewer_than_10():
    reviews = _trend_listing([_review(1, FAKE, 5), _review(1, WRONG, 6)], [], recent_n=10, previous_n=9)
    assert trend_rising(reviews) is None


def test_trend_rising_none_for_no_reviews():
    assert trend_rising([]) is None


def test_collapse_allegations_keeps_newest_copy_and_counts_removed():
    old_copy = _review(1, FAKE, 30)
    new_copy = _review(2, "  this PHONE is fake. ", 1)
    other = _review(1, WRONG, 10)
    distinct, removed = collapse_allegations([old_copy, other, new_copy, _review(5, GOOD)])
    assert distinct == [new_copy, other]
    assert removed == 1


def test_tag_counts_orders_by_count_then_tag_priority():
    allegations = [_review(1, MISMATCH), _review(1, WRONG), _review(1, "Not as shown.")]
    assert tag_counts(allegations) == [("Description mismatch", 2), ("Wrong item", 1)]
    assert main_concern([_review(1, WRONG), _review(1, FAKE)]) == "Authenticity"


def test_assess_reviews_counts_after_record_dedupe():
    a = _review(5, GOOD, 1, reviewer="x")
    evidence = assess_reviews([a, Review("dup", 5, a.review_date, GOOD, "x")])
    assert (evidence.total, evidence.low, evidence.high) == (1, 0, 1)


def test_assess_reviews_empty():
    evidence = assess_reviews([])
    assert (evidence.total, evidence.repeated, evidence.concentrated) == (0, False, False)


def test_assess_reviews_repeated_needs_two_distinct_allegations():
    evidence = assess_reviews([_review(1, FAKE), _review(1, WRONG)] + _many(30, 5, GOOD))
    assert evidence.repeated is True


def test_assess_reviews_copies_do_not_count_as_repetition():
    evidence = assess_reviews(_many(5, 1, FAKE) + _many(30, 5, GOOD))
    assert evidence.repeated is False
    assert evidence.excluded_duplicates == 4


def test_assess_reviews_lookback_excludes_allegations_365_days_before_last_review():
    evidence = assess_reviews([_review(1, FAKE, 365), _review(1, WRONG, 364), _review(5, GOOD, 0)])
    assert [r.text for r in evidence.distinct_allegations] == [WRONG]


def test_assess_reviews_concentration_at_exactly_25_percent_with_an_allegation():
    evidence = assess_reviews([_review(1, FAKE)] + _many(4, 1, GENERIC) + _many(15, 5, GOOD))
    assert evidence.low_star_share == 0.25
    assert evidence.concentrated is True


def test_assess_reviews_no_concentration_without_an_allegation():
    evidence = assess_reviews(_many(5, 1, GENERIC) + _many(15, 5, GOOD))
    assert evidence.concentrated is False


def test_assess_reviews_no_concentration_below_25_percent():
    evidence = assess_reviews([_review(1, FAKE)] + _many(3, 1, GENERIC) + _many(16, 5, GOOD))
    assert evidence.low_star_share == 0.2
    assert evidence.concentrated is False


def test_assess_reviews_share_skipped_below_20_polar_reviews():
    evidence = assess_reviews([_review(1, FAKE)] + _many(18, 5, GOOD) + _many(5, 3, GOOD))
    assert evidence.low_star_share is None
    assert evidence.concentrated is False


def test_assess_reviews_all_low_star_share_is_100_percent():
    evidence = assess_reviews([_review(1, FAKE)] + _many(19, 1, GENERIC))
    assert evidence.low_star_share == 1.0
    assert evidence.concentrated is True


def test_is_candidate_keeps_stage_one_while_allegation_uses_context():
    negated = _review(1, "This is not fake, battery drains.")
    assert is_candidate(negated) is True
    assert is_allegation(negated) is False


def test_trend_rising_can_use_stage_one_for_research_reproduction():
    negated = ["Not fake at all, slow delivery.", "Not a fake, poor box."]
    reviews = _trend_listing([_review(1, t, 5 + i) for i, t in enumerate(negated)], [])
    assert trend_rising(reviews, is_candidate) is True
    assert trend_rising(reviews) is False
