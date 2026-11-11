"""Input and result types for the scoring pipeline."""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass(frozen=True)
class Review:
    """One customer review of a seller's offer."""

    review_id: str
    stars: int
    review_date: date
    text: str
    reviewer_id: Optional[str] = None


@dataclass(frozen=True)
class Complaint:
    """One customer-service authenticity complaint about a seller, separate from reviews.

    `confirmed_counterfeit` marks a complaint whose investigation confirmed a counterfeit item.
    """

    complaint_id: str
    complaint_date: date
    order_id: Optional[str] = None
    confirmed_counterfeit: bool = False


@dataclass
class SellerRecord:
    """A seller's offer on the listing, with the evidence used to score it.

    `complaints` is None when no complaints data is available, which is not the same as [].
    `brand_status` is one of config.BRAND_STATUSES.
    """

    seller_id: str
    name: str
    price: int
    delivery: str
    days_selling: int
    positive_feedback_pct: Optional[float] = None
    feedback_count: int = 0
    odr_pct: Optional[float] = None
    brand_status: str = "unverified"
    orders_in_window: Optional[int] = None
    reviews: List[Review] = field(default_factory=list)
    complaints: Optional[List[Complaint]] = field(default_factory=list)


@dataclass(frozen=True)
class FlaggedReview:
    """A distinct 1-2 star review interpreted as an authenticity or mismatch allegation."""

    tag: str
    stars: int
    text: str


@dataclass
class FactorResult:
    """One factor's status and explanation, in the shape the frontend reads.

    `severity` refines a warn status: "concern" or "alert" (serious, cannot be outweighed).
    """

    status: str
    short: str
    text: str
    source: str
    severity: Optional[str] = None
    flagged: Optional[List[FlaggedReview]] = None
    excluded_duplicates: Optional[int] = None
