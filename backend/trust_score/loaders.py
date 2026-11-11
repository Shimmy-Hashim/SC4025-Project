"""Read pipeline inputs: the demo listing, its reviews, and the research review datasets."""

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from trust_score.config import BRAND_STATUSES, BRAND_UNVERIFIED
from trust_score.factors import ListingContext
from trust_score.models import Complaint, Review, SellerRecord
from trust_score.text import is_missing_text

INDIAN_PRODUCTS_KEY = ("asin", "name", "date", "rating", "review")


def load_listing(listing_path: Path, reviews_path: Path) -> Tuple[Dict[str, Any], ListingContext]:
    """Product block and listing context (sellers with their reviews and complaints)."""
    listing = json.loads(listing_path.read_text(encoding="utf-8"))
    return parse_listing(listing, load_seller_reviews(reviews_path))


def parse_listing(listing: Dict[str, Any], reviews_by_seller: Dict[str, List[Review]]
                  ) -> Tuple[Dict[str, Any], ListingContext]:
    """Product block and listing context from an already-loaded listing document."""
    sellers = [
        SellerRecord(
            seller_id=s["id"],
            name=s["name"],
            price=s["price"],
            delivery=s["delivery"],
            days_selling=s["days_selling"],
            positive_feedback_pct=s.get("positive_feedback_pct"),
            feedback_count=s.get("feedback_count", 0),
            odr_pct=s.get("odr_pct"),
            brand_status=s.get("brand_status", BRAND_UNVERIFIED),
            orders_in_window=s.get("orders_in_window"),
            reviews=reviews_by_seller.get(s["id"], []),
            complaints=parse_complaints(s.get("complaints")),
        )
        for s in listing["sellers"]
    ]
    unknown = [s.seller_id for s in sellers if s.brand_status not in BRAND_STATUSES]
    if unknown:
        raise ValueError(f"Unknown brand_status for sellers {unknown}; use one of {BRAND_STATUSES}.")
    context = ListingContext(brand=listing["brand"],
                             data_cutoff=date.fromisoformat(listing["data_cutoff"]), sellers=sellers)
    return listing["product"], context


def parse_complaints(raw: Optional[List[Dict[str, Any]]]) -> Optional[List[Complaint]]:
    """Complaint records; None (no complaints data) stays None, distinct from an empty list."""
    if raw is None:
        return None
    return [Complaint(complaint_id=x["id"], complaint_date=date.fromisoformat(x["date"]),
                      order_id=x.get("order_id"),
                      confirmed_counterfeit=bool(x.get("confirmed_counterfeit", False)))
            for x in raw]


def load_seller_reviews(path: Path) -> Dict[str, List[Review]]:
    """Demo reviews CSV (seller_id, review_id, reviewer_id, date, stars, text) grouped by seller."""
    grouped: Dict[str, List[Review]] = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            grouped[row["seller_id"]].append(Review(
                review_id=row["review_id"], stars=int(row["stars"]),
                review_date=date.fromisoformat(row["date"]), text=row["text"],
                reviewer_id=row["reviewer_id"] or None))
    return grouped


def load_indian_products(path: Path) -> Dict[str, List[Review]]:
    """Indian Products on Amazon reviews grouped by ASIN, prepared as the research did.

    Exact duplicate rows are dropped, then rows whose review text pandas would read as
    missing are removed.
    """
    grouped: Dict[str, List[Review]] = defaultdict(list)
    seen = set()
    with path.open(encoding="utf-8", newline="") as source:
        for i, row in enumerate(csv.DictReader(source)):
            key = tuple(row[k] for k in INDIAN_PRODUCTS_KEY)
            if key in seen:
                continue
            seen.add(key)
            if is_missing_text(row["review"]):
                continue
            grouped[row["asin"]].append(Review(
                review_id=f"{row['asin']}_{i}", stars=int(float(row["rating"])),
                review_date=date.fromisoformat(row["date"]), text=row["review"]))
    return grouped


def load_synthetic(path: Path) -> Tuple[Dict[str, List[Review]], Dict[str, str], Dict[str, int]]:
    """Synthetic scenario reviews grouped by listing, each listing's scenario, and the
    research's own screen_specific_wording count per listing (for a consistency check)."""
    grouped: Dict[str, List[Review]] = defaultdict(list)
    scenarios: Dict[str, str] = {}
    research_specific: Dict[str, int] = defaultdict(int)
    with path.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            grouped[row["asin"]].append(Review(
                review_id=row["review_record_id"], stars=int(float(row["rating"])),
                review_date=date.fromisoformat(row["date"]), text=row["review"],
                reviewer_id=row["synthetic_reviewer_id"] or None))
            scenarios[row["asin"]] = row["synthetic_scenario"]
            research_specific[row["asin"]] += int(row["screen_specific_wording"])
    return grouped, scenarios, research_specific
