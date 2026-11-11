"""Seller-level review evidence: allegations, low-star share and the 90-day trend.

Ports the research's Checkpoint 1 screen and its measures()/evaluate() window logic
(research/generate_synthetic_indian_products.py).
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable, List, Optional, Tuple

from trust_score.config import (
    ALLEGATION_LOOKBACK_DAYS,
    HIGH_STARS,
    LOW_STAR_SHARE_THRESHOLD,
    LOW_STARS,
    MIN_DISTINCT_ALLEGATIONS,
    MIN_POLAR_REVIEWS,
    MIN_WINDOW_REVIEWS,
    SPECIFIC_RULE_TAGS,
    WINDOW_DAYS,
)
from trust_score.models import Review
from trust_score.text import interpreted_tag, norm, specific_tag


@dataclass
class ReviewEvidence:
    """Counts and rule outcomes for one seller's reviews (after record de-duplication)."""

    total: int
    low: int
    high: int
    low_star_share: Optional[float] = None
    distinct_allegations: List[Review] = field(default_factory=list)
    excluded_duplicates: int = 0
    trend_rising: Optional[bool] = None
    repeated: bool = False
    concentrated: bool = False


def dedupe_records(reviews: List[Review]) -> List[Review]:
    """Drop exact duplicate records (same reviewer, date, stars and text), keeping the first."""
    seen = set()
    unique = []
    for review in reviews:
        key = (review.reviewer_id, review.review_date, review.stars, review.text)
        if key not in seen:
            seen.add(key)
            unique.append(review)
    return unique


def is_low_star(review: Review) -> bool:
    """1-2 star review."""
    return review.stars in LOW_STARS


def is_high_star(review: Review) -> bool:
    """4-5 star review."""
    return review.stars in HIGH_STARS


def is_candidate(review: Review) -> bool:
    """Stage 1: 1-2 star review matching a Checkpoint 1 authenticity/mismatch rule (research screen)."""
    return is_low_star(review) and specific_tag(review.text) is not None


def is_allegation(review: Review) -> bool:
    """Stage 2: a candidate that still matches after excluded phrases are removed."""
    return is_low_star(review) and interpreted_tag(review.text) is not None


ReviewTest = Callable[[Review], bool]


def low_star_share(low: int, high: int) -> float:
    """Bounded low-star share L/(L+H).

    :raises ValueError: when L+H is 0, where the share is undefined.
    """
    if low + high == 0:
        raise ValueError("Low-star share is undefined when there are no 1-2 or 4-5 star reviews.")
    return low / (low + high)


def split_windows(reviews: List[Review], endpoint: date) -> Tuple[List[Review], List[Review]]:
    """Reviews in (T-90, T] and (T-180, T-90], where T is the given endpoint."""
    recent_start = endpoint - timedelta(days=WINDOW_DAYS)
    previous_start = endpoint - timedelta(days=2 * WINDOW_DAYS)
    recent = [r for r in reviews if recent_start < r.review_date <= endpoint]
    previous = [r for r in reviews if previous_start < r.review_date <= recent_start]
    return recent, previous


def allegation_share(window: List[Review], test: ReviewTest = is_allegation) -> float:
    """Share of all reviews in a non-empty window that pass the test."""
    return sum(test(r) for r in window) / len(window)


def distinct_allegation_texts(window: List[Review], test: ReviewTest = is_allegation) -> int:
    """Number of distinct normalised texts in a window that pass the test."""
    return len({norm(r.text) for r in window if test(r)})


def trend_rising(reviews: List[Review], test: ReviewTest = is_allegation) -> Optional[bool]:
    """Whether allegations rose in the latest 90 days, as in the research's evaluate().

    Returns None when either window has fewer than the minimum number of reviews. Pass
    is_candidate as the test to reproduce the research's stage 1 counts.
    """
    if not reviews:
        return None
    endpoint = max(r.review_date for r in reviews)
    recent, previous = split_windows(reviews, endpoint)
    if len(recent) < MIN_WINDOW_REVIEWS or len(previous) < MIN_WINDOW_REVIEWS:
        return None
    rising = allegation_share(recent, test) > allegation_share(previous, test)
    return rising and distinct_allegation_texts(recent, test) >= MIN_DISTINCT_ALLEGATIONS


def collapse_allegations(reviews: List[Review]) -> Tuple[List[Review], int]:
    """Distinct allegations by normalised text, newest first, and how many copies were removed."""
    allegations = sorted((r for r in reviews if is_allegation(r)),
                         key=lambda r: r.review_date, reverse=True)
    seen = set()
    distinct = []
    for review in allegations:
        key = norm(review.text)
        if key not in seen:
            seen.add(key)
            distinct.append(review)
    return distinct, len(allegations) - len(distinct)


def tag_counts(allegations: List[Review]) -> List[Tuple[str, int]]:
    """(tag, count) for tags present, most frequent first; ties keep SPECIFIC_RULE_TAGS order."""
    counts = Counter(interpreted_tag(r.text) for r in allegations)
    present = [tag for tag in SPECIFIC_RULE_TAGS.values() if counts[tag]]
    return sorted(((tag, counts[tag]) for tag in present), key=lambda pair: -pair[1])


def main_concern(allegations: List[Review]) -> str:
    """Most frequent tag among allegations; ties go to the earlier tag in SPECIFIC_RULE_TAGS."""
    return tag_counts(allegations)[0][0]


def assess_reviews(reviews: List[Review]) -> ReviewEvidence:
    """Apply record de-duplication, the allegation rules, the low-star share and the trend."""
    unique = dedupe_records(reviews)
    low = sum(is_low_star(r) for r in unique)
    high = sum(is_high_star(r) for r in unique)
    evidence = ReviewEvidence(total=len(unique), low=low, high=high)
    if not unique:
        return evidence

    endpoint = max(r.review_date for r in unique)
    lookback_start = endpoint - timedelta(days=ALLEGATION_LOOKBACK_DAYS)
    in_lookback = [r for r in unique if r.review_date > lookback_start]
    evidence.distinct_allegations, evidence.excluded_duplicates = collapse_allegations(in_lookback)
    evidence.trend_rising = trend_rising(unique)
    evidence.repeated = len(evidence.distinct_allegations) >= MIN_DISTINCT_ALLEGATIONS

    if low + high >= MIN_POLAR_REVIEWS:
        evidence.low_star_share = low_star_share(low, high)
        evidence.concentrated = (evidence.low_star_share >= LOW_STAR_SHARE_THRESHOLD
                                 and len(evidence.distinct_allegations) >= 1)
    return evidence
