"""The five scoring factors. Each turns a seller's evidence into pass / warn / na.

A warn carries a severity: "concern" (prevents High) or "alert" (serious; forces Low and is
shown prominently, even when the offer is otherwise not scored).
"""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import median
from typing import Dict, List, Optional

from trust_score import constants as c
from trust_score.config import (
    BRAND_CONTRADICTED,
    BRAND_NOT_AUTHORISED,
    BRAND_VERIFIED,
    COMPLAINT_WINDOW_DAYS,
    CONFIRMED_FINDING_LOOKBACK_DAYS,
    HISTORY_MIN_POSITIVE_PCT,
    HISTORY_MIN_RATINGS,
    MAX_FLAGGED_REVIEWS,
    MIN_AFFECTED_ORDERS_FOR_WARN,
    MIN_COMPLAINT_RATE_FOR_WARN,
    MIN_HISTORY_DAYS,
    MIN_OTHER_SELLERS_FOR_PRICE,
    MIN_REVIEWS,
    NA,
    ODR_MAX_PCT,
    PASS,
    PRICE_ALERT_FRACTION_BELOW,
    PRICE_WARN_FRACTION_BELOW,
    SEVERITY_ALERT,
    SEVERITY_CONCERN,
    WARN,
)
from trust_score.models import FactorResult, FlaggedReview, Review, SellerRecord
from trust_score.review_screen import ReviewEvidence, assess_reviews, main_concern, tag_counts
from trust_score.text import format_duration, format_indian_number, format_inr, interpreted_tag


@dataclass(frozen=True)
class ListingContext:
    """Listing-wide facts a factor may need beyond the seller being scored."""

    brand: str
    data_cutoff: date
    sellers: List[SellerRecord]


class Factor(ABC):
    """A single explainable factor; subclasses set key and source and implement evaluate."""

    key: str
    source: str

    @abstractmethod
    def evaluate(self, seller: SellerRecord, context: ListingContext) -> FactorResult:
        """Return this factor's status and explanation for the seller."""

    def result(self, status: str, short: str, text: str) -> FactorResult:
        """A pass or na result carrying this factor's source."""
        return FactorResult(status=status, short=short, text=text, source=self.source)

    def concern(self, short: str, text: str) -> FactorResult:
        """A warn that prevents a High band."""
        return FactorResult(WARN, short, text, self.source, severity=SEVERITY_CONCERN)

    def alert(self, short: str, text: str) -> FactorResult:
        """A serious warn that no other factor can outweigh."""
        return FactorResult(WARN, short, text, self.source, severity=SEVERITY_ALERT)


class HistoryFactor(Factor):
    """Seller feedback and service record. Age decides whether there is enough evidence to judge;
    it is not evidence of trustworthiness on its own."""

    key = "history"
    source = c.SOURCE_HISTORY

    def evaluate(self, seller: SellerRecord, context: ListingContext) -> FactorResult:
        duration = format_duration(seller.days_selling)
        if seller.days_selling < MIN_HISTORY_DAYS:
            return self.result(NA, c.HISTORY_NA_SHORT, c.HISTORY_NA_TEXT.format(duration=duration))
        count = format_indian_number(seller.feedback_count)
        if seller.positive_feedback_pct is None or seller.feedback_count < HISTORY_MIN_RATINGS:
            return self.result(NA, c.HISTORY_LIMITED_SHORT.format(count=count),
                               c.HISTORY_LIMITED_TEXT.format(duration=duration.capitalize(), count=count))
        pct = math.floor(seller.positive_feedback_pct)
        text = c.HISTORY_TEXT.format(duration=duration.capitalize(), pct=pct, count=count)
        if seller.odr_pct is not None:
            text += c.HISTORY_ODR_TEXT.format(odr=format_pct(seller.odr_pct))
        if seller.positive_feedback_pct < HISTORY_MIN_POSITIVE_PCT:
            return self.concern(c.HISTORY_WARN_FEEDBACK_SHORT.format(pct=pct), text)
        if seller.odr_pct is not None and seller.odr_pct >= ODR_MAX_PCT:
            return self.concern(c.HISTORY_WARN_ODR_SHORT.format(odr=format_pct(seller.odr_pct)), text)
        return self.result(PASS, c.HISTORY_PASS_SHORT.format(duration=duration.capitalize(), pct=pct),
                           text)


class BrandFactor(Factor):
    """Reseller authorisation recorded by the brand owner (Brand Registry Reseller role)."""

    key = "brand"
    source = c.SOURCE_BRAND

    def evaluate(self, seller: SellerRecord, context: ListingContext) -> FactorResult:
        if seller.brand_status == BRAND_VERIFIED:
            return self.result(PASS, c.BRAND_PASS_SHORT.format(brand=context.brand), c.BRAND_PASS_TEXT)
        if seller.brand_status == BRAND_NOT_AUTHORISED:
            return self.concern(c.BRAND_WARN_SHORT, c.BRAND_WARN_TEXT)
        if seller.brand_status == BRAND_CONTRADICTED:
            return self.alert(c.BRAND_ALERT_SHORT, c.BRAND_ALERT_TEXT)
        return self.result(NA, c.BRAND_NA_SHORT, c.BRAND_NA_TEXT)


class PriceFactor(Factor):
    """Offer price against the median of the other sellers on the same listing.

    Every offer on a listing is the same variant and condition, so all other sellers compare.
    """

    key = "price"
    source = c.SOURCE_PRICE

    def evaluate(self, seller: SellerRecord, context: ListingContext) -> FactorResult:
        others = reference_prices(seller, context.sellers)
        if len(others) < MIN_OTHER_SELLERS_FOR_PRICE:
            return self.result(NA, c.PRICE_NA_SHORT, c.PRICE_NA_TEXT)
        fraction_below = (median(others) - seller.price) / median(others)
        values = {"price": format_inr(seller.price), "n": len(others),
                  "typical": format_inr(round(median(others)))}
        pct = math.ceil(fraction_below * 100)
        if fraction_below > PRICE_ALERT_FRACTION_BELOW:
            return self.alert(c.PRICE_ALERT_SHORT.format(pct=pct), c.PRICE_ALERT_TEXT.format(pct=pct, **values))
        if fraction_below > PRICE_WARN_FRACTION_BELOW:
            return self.concern(c.PRICE_WARN_SHORT.format(pct=pct), c.PRICE_WARN_TEXT.format(pct=pct, **values))
        return self.result(PASS, c.PRICE_PASS_SHORT, c.PRICE_PASS_TEXT.format(**values))


class ReviewsFactor(Factor):
    """Authenticity and mismatch allegations in the seller's 1-2 star reviews (after the
    context stage). Reviews are reports, not findings, so they raise concerns, never alerts."""

    key = "reviews"
    source = c.SOURCE_REVIEWS

    def evaluate(self, seller: SellerRecord, context: ListingContext) -> FactorResult:
        evidence = assess_reviews(seller.reviews)
        if evidence.total < MIN_REVIEWS:
            result = self.result(NA, c.REVIEWS_NA_SHORT.format(n=evidence.total),
                                 c.REVIEWS_NA_TEXT.format(n=evidence.total))
        elif evidence.repeated or evidence.concentrated:
            result = self.warn_result(evidence)
        elif evidence.distinct_allegations:
            concern = c.CONCERN_WORDING[main_concern(evidence.distinct_allegations)][0]
            result = self.result(PASS, c.REVIEWS_ISOLATED_SHORT,
                                 c.REVIEWS_ISOLATED_TEXT.format(n=evidence.total, concern=concern))
        else:
            result = self.result(PASS, c.REVIEWS_PASS_SHORT, c.REVIEWS_PASS_TEXT)
        result.flagged = flagged_reviews(evidence) if result.status != NA else []
        result.excluded_duplicates = evidence.excluded_duplicates if result.status != NA else 0
        return result

    def warn_result(self, evidence: ReviewEvidence) -> FactorResult:
        """Concern: repeated allegations, or a high low-star share with an allegation."""
        concern_short = c.CONCERN_WORDING[main_concern(evidence.distinct_allegations)][1]
        concern = concern_phrase(evidence.distinct_allegations)
        k = len(evidence.distinct_allegations)
        if evidence.repeated:
            short = c.REVIEWS_REPEATED_SHORT.format(concern_short=concern_short)
            text = c.REVIEWS_REPEATED_TEXT.format(k=k, n=evidence.total, concern=concern)
        else:
            short = c.REVIEWS_CONCENTRATION_SHORT.format(concern_short=concern_short)
            text = c.REVIEWS_CONCENTRATION_TEXT.format(
                pct=round((evidence.low_star_share or 0) * 100), k=k, n=evidence.total, concern=concern)
        text += trend_sentence(evidence.trend_rising)
        if evidence.excluded_duplicates:
            text += c.REVIEWS_DUPLICATES.format(k=evidence.excluded_duplicates)
        return self.concern(short, text)


class ComplaintsFactor(Factor):
    """Customer-service authenticity complaints, counted once per affected order.

    No data (None) is reported as unavailable, never as zero complaints. A confirmed counterfeit
    finding is a serious alert regardless of the complaint count.
    """

    key = "complaints"
    source = c.SOURCE_COMPLAINTS

    def evaluate(self, seller: SellerRecord, context: ListingContext) -> FactorResult:
        if seller.complaints is None:
            return self.result(NA, c.COMPLAINTS_UNAVAILABLE_SHORT, c.COMPLAINTS_UNAVAILABLE_TEXT)
        finding_start = context.data_cutoff - timedelta(days=CONFIRMED_FINDING_LOOKBACK_DAYS)
        findings = sorted(x.complaint_date for x in seller.complaints if x.confirmed_counterfeit
                          and finding_start < x.complaint_date <= context.data_cutoff)
        if findings:
            return self.alert(c.COMPLAINTS_ALERT_SHORT,
                              c.COMPLAINTS_ALERT_TEXT.format(date=findings[-1].strftime("%-d %b %Y")))
        if seller.days_selling < MIN_HISTORY_DAYS:
            return self.result(NA, c.COMPLAINTS_NA_SHORT, c.COMPLAINTS_NA_TEXT)
        n = affected_orders(seller, context.data_cutoff)
        orders = seller.orders_in_window
        if n >= MIN_AFFECTED_ORDERS_FOR_WARN:
            rate = n / orders if orders else None
            if rate is not None and rate < MIN_COMPLAINT_RATE_FOR_WARN:
                return self.result(PASS, c.COMPLAINTS_LOW_RATE_SHORT.format(n=n, orders=format_indian_number(orders)),
                                   c.COMPLAINTS_LOW_RATE_TEXT.format(n=n, orders=format_indian_number(orders),
                                                                     rate=format_pct(rate * 100)))
            text = c.COMPLAINTS_WARN_TEXT.format(n=n)
            if rate is not None:
                text += c.COMPLAINTS_RATE_TEXT.format(n=n, orders=format_indian_number(orders),
                                                      rate=format_pct(rate * 100))
            return self.concern(c.COMPLAINTS_WARN_SHORT.format(n=n), text)
        if n == 1:
            return self.result(PASS, c.COMPLAINTS_SINGLE_SHORT, c.COMPLAINTS_SINGLE_TEXT)
        return self.result(PASS, c.COMPLAINTS_PASS_SHORT, c.COMPLAINTS_PASS_TEXT)


FACTORS: List[Factor] = [HistoryFactor(), BrandFactor(), PriceFactor(), ReviewsFactor(),
                         ComplaintsFactor()]


def reference_prices(seller: SellerRecord, sellers: List[SellerRecord]) -> List[int]:
    """Other sellers' prices used as the comparison, leaving out extreme outliers: offers more than
    PRICE_ALERT_FRACTION_BELOW below the median of all offers on the listing. Without this, one
    implausible offer (a ₹4,999 iPhone) would drag the reference down for everyone else."""
    floor = median(s.price for s in sellers) * (1 - PRICE_ALERT_FRACTION_BELOW)
    return [s.price for s in sellers if s.seller_id != seller.seller_id and s.price >= floor]


def affected_orders(seller: SellerRecord, cutoff: date) -> int:
    """Distinct orders with an authenticity complaint in the window (a complaint without an
    order id counts as its own order)."""
    window_start = cutoff - timedelta(days=COMPLAINT_WINDOW_DAYS)
    return len({x.order_id or x.complaint_id for x in seller.complaints or []
                if window_start < x.complaint_date <= cutoff})


def format_pct(value: float) -> str:
    """Percentage with up to two decimals and no trailing zeros: 0.5 -> '0.5', 10.0 -> '10'."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


def concern_phrase(allegations: List[Review]) -> str:
    """Concern wording; with several tags, each is named with its count, most frequent first."""
    counts = tag_counts(allegations)
    if len(counts) == 1:
        return c.CONCERN_WORDING[counts[0][0]][0]
    return c.CONCERN_JOINER.join(c.CONCERN_WITH_COUNT.format(concern=c.CONCERN_WORDING[tag][0], n=n)
                                 for tag, n in counts)


def trend_sentence(rising: Optional[bool]) -> str:
    """Trend explanation appended to a reviews warning; never changes the status."""
    if rising is None:
        return c.REVIEWS_TREND_UNAVAILABLE
    return c.REVIEWS_TREND_RISING if rising else c.REVIEWS_TREND_NOT_RISING


def flagged_reviews(evidence: ReviewEvidence) -> List[FlaggedReview]:
    """Up to MAX_FLAGGED_REVIEWS distinct allegations, newest first, for the US7 panel."""
    return [FlaggedReview(tag=interpreted_tag(r.text) or "", stars=r.stars, text=r.text)
            for r in evidence.distinct_allegations[:MAX_FLAGGED_REVIEWS]]


def evaluate_all(seller: SellerRecord, context: ListingContext) -> Dict[str, FactorResult]:
    """Every factor's result for one seller, keyed by factor key."""
    return {factor.key: factor.evaluate(seller, context) for factor in FACTORS}
