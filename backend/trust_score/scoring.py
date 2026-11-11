"""Turn factor results into an overall band, score and alert, in a fixed decision order:

1. Serious alerts are collected first; they are shown even when the offer is not scored.
2. Gate: too new, too few reviews, or two or more unknown factors -> Not enough data.
3. Any serious alert -> Low, whatever the other factors say.
4. Weighted score -> base band; a concern on a capping factor limits the band to Medium.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from trust_score import constants as c
from trust_score.config import (
    BAND_HIGH,
    BAND_LOW,
    BAND_MEDIUM,
    BAND_NOT_ENOUGH_DATA,
    CAPPING_FACTORS,
    FACTOR_ORDER,
    FACTOR_WEIGHTS,
    HIGH_MIN_SCORE,
    INLINE_COUNT,
    INLINE_FALLBACK_ORDER,
    MAX_NA_FACTORS,
    MEDIUM_MIN_SCORE,
    MIN_HISTORY_DAYS,
    MIN_REVIEWS,
    NA,
    PASS,
    SEVERITY_ALERT,
    WARN,
)
from trust_score.factors import ListingContext, evaluate_all
from trust_score.models import FactorResult, SellerRecord
from trust_score.review_screen import dedupe_records
from trust_score.text import format_duration


@dataclass
class ScoredOffer:
    """A seller's overall result: band, score (None when not scored), reason, alert and factors."""

    seller: SellerRecord
    band: str
    score: Optional[int]
    reason: Optional[str]
    inline: List[str]
    factors: Dict[str, FactorResult]
    alert: Optional[str] = None


def eligibility_reason(seller: SellerRecord) -> Optional[str]:
    """Reason (without the closing sentence) when the seller fails the overall gate."""
    is_new = seller.days_selling < MIN_HISTORY_DAYS
    review_count = len(dedupe_records(seller.reviews))
    too_few = review_count < MIN_REVIEWS
    duration = format_duration(seller.days_selling)
    if is_new and too_few:
        return c.REASON_NEW_AND_FEW_REVIEWS.format(duration=duration, n=review_count)
    if is_new:
        return c.REASON_NEW.format(duration=duration)
    if too_few:
        return c.REASON_FEW_REVIEWS.format(n=review_count)
    return None


def alert_factors(factors: Dict[str, FactorResult]) -> List[str]:
    """Keys of factors raising a serious alert, in the fixed factor order."""
    return [k for k in FACTOR_ORDER if factors[k].severity == SEVERITY_ALERT]


def weighted_score(factors: Dict[str, FactorResult]) -> int:
    """100 x earned points / weight of the factors that are not na, rounded half up.

    :raises ValueError: when every factor is na, where the score is undefined.
    """
    available = sum(FACTOR_WEIGHTS[k] for k, f in factors.items() if f.status != NA)
    if available == 0:
        raise ValueError("Score is undefined when every factor is na.")
    earned = sum(FACTOR_WEIGHTS[k] for k, f in factors.items() if f.status == PASS)
    return (200 * earned + available) // (2 * available)


def base_band(score: int) -> str:
    """Band from the score cut-offs alone."""
    if score >= HIGH_MIN_SCORE:
        return BAND_HIGH
    if score >= MEDIUM_MIN_SCORE:
        return BAND_MEDIUM
    return BAND_LOW


def apply_cap(band: str, factors: Dict[str, FactorResult]) -> str:
    """A warning on any capping factor limits the band to Medium."""
    if band == BAND_HIGH and any(factors[k].status == WARN for k in CAPPING_FACTORS):
        return BAND_MEDIUM
    return band


def pick_inline(factors: Dict[str, FactorResult]) -> List[str]:
    """Alerts first, then other warnings, then the fallback order; exactly INLINE_COUNT keys."""
    alerts = [k for k in INLINE_FALLBACK_ORDER if factors[k].severity == SEVERITY_ALERT]
    warns = [k for k in INLINE_FALLBACK_ORDER if factors[k].status == WARN and k not in alerts]
    rest = [k for k in INLINE_FALLBACK_ORDER if k not in alerts and k not in warns]
    return (alerts + warns + rest)[:INLINE_COUNT]


def score_offer(seller: SellerRecord, context: ListingContext) -> ScoredOffer:
    """Evaluate every factor, then apply the decision order in the module docstring."""
    factors = evaluate_all(seller, context)
    factors = {k: factors[k] for k in FACTOR_ORDER}
    inline = pick_inline(factors)
    alerts = alert_factors(factors)
    alert = factors[alerts[0]].short if alerts else None
    reason = eligibility_reason(seller)
    if reason is None and sum(f.status == NA for f in factors.values()) > MAX_NA_FACTORS:
        reason = c.REASON_MISSING_FACTORS
    if reason is not None:
        reason += c.REASON_SEE_ALERT if alert else c.REASON_NOT_A_WARNING
        return ScoredOffer(seller, BAND_NOT_ENOUGH_DATA, None, reason, inline, factors, alert)
    score = weighted_score(factors)
    band = BAND_LOW if alerts else apply_cap(base_band(score), factors)
    return ScoredOffer(seller, band, score, None, inline, factors, alert)
