"""Local demo server: serves the site and re-scores sellers when a tester edits their inputs.

Edits are scored in memory with the same rules as `build`; nothing is written to disk.
Bound to 127.0.0.1 only. Run from backend/: python -m trust_score.cli serve
"""

import copy
import json
from datetime import date, timedelta
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

from generate_demo_listing import TEMPLATES
from trust_score.config import BRAND_STATUSES, BRAND_UNVERIFIED, COMPLAINT_WINDOW_DAYS
from trust_score.export import build_document, validate
from trust_score.loaders import load_seller_reviews, parse_listing
from trust_score.models import Review
from trust_score.scoring import score_offer

MAX_RECENT_COMPLAINTS = 20
MAX_EXTRA_REVIEWS = 20
MAX_DAYS_SELLING = 365 * 30
MAX_PRICE = 10_000_000
MAX_FEEDBACK_COUNT = 10_000_000
MAX_ORDERS = 10_000_000


def recent_affected_orders(seller: Dict[str, Any], cutoff: date) -> int:
    """Distinct orders with a complaint dated within the complaints window before the cutoff."""
    window_start = cutoff - timedelta(days=COMPLAINT_WINDOW_DAYS)
    return len({c.get("order_id") or c["id"] for c in seller.get("complaints") or []
                if window_start < date.fromisoformat(c["date"]) <= cutoff})


def editable_inputs(listing: Dict[str, Any]) -> Dict[str, Any]:
    """The inputs a tester may change, per seller, as served by GET /api/inputs."""
    cutoff = date.fromisoformat(listing["data_cutoff"])
    return {"dataCutoff": listing["data_cutoff"], "brandStatuses": list(BRAND_STATUSES), "sellers": [{
        "id": s["id"],
        "name": s["name"],
        "price": s["price"],
        "daysSelling": s["days_selling"],
        "positiveFeedbackPct": s.get("positive_feedback_pct"),
        "feedbackCount": s.get("feedback_count", 0),
        "odrPct": s.get("odr_pct"),
        "brandStatus": s.get("brand_status", BRAND_UNVERIFIED),
        "complaintsAvailable": s.get("complaints") is not None,
        "recentComplaints": recent_affected_orders(s, cutoff),
        "ordersInWindow": s.get("orders_in_window"),
        "confirmedCounterfeit": any(c.get("confirmed_counterfeit") for c in s.get("complaints") or []),
        "extraFakeReviews": 0,
    } for s in listing["sellers"]]}


def whole_number(edit: Dict[str, Any], key: str, low: int, high: int) -> int:
    """An integer field within [low, high].

    :raises ValueError: when the value is missing, not a whole number, or out of range.
    """
    value = edit.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{edit.get('id', '?')}: {key} must be a whole number from {low} to {high}.")
    return value


def optional_number(edit: Dict[str, Any], key: str, low: float, high: float) -> Optional[float]:
    """A number within [low, high], or None.

    :raises ValueError: when the value is present but not a number in range.
    """
    value = edit.get(key)
    if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                              or not low <= value <= high):
        raise ValueError(f"{edit.get('id', '?')}: {key} must be from {low:g} to {high:g}, or null.")
    return value


def flag(edit: Dict[str, Any], key: str) -> bool:
    """A required true/false field.

    :raises ValueError: when the value is not a boolean.
    """
    value = edit.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{edit.get('id', '?')}: {key} must be true or false.")
    return value


def apply_edits(listing: Dict[str, Any], edits: Dict[str, Any]) -> Dict[str, Any]:
    """A copy of the listing with each edited seller's profile and complaints replaced.

    :raises ValueError: for an unknown seller id or an invalid field value.
    """
    edited = copy.deepcopy(listing)
    by_id = {s["id"]: s for s in edited["sellers"]}
    cutoff = date.fromisoformat(edited["data_cutoff"])
    for edit in edits.get("sellers") or []:
        seller = by_id.get(edit.get("id"))
        if seller is None:
            raise ValueError(f"Unknown seller id: {edit.get('id')!r}.")
        brand_status = edit.get("brandStatus")
        if brand_status not in BRAND_STATUSES:
            raise ValueError(f"{seller['id']}: brandStatus must be one of {', '.join(BRAND_STATUSES)}.")
        seller["price"] = whole_number(edit, "price", 1, MAX_PRICE)
        seller["days_selling"] = whole_number(edit, "daysSelling", 0, MAX_DAYS_SELLING)
        seller["positive_feedback_pct"] = optional_number(edit, "positiveFeedbackPct", 0, 100)
        seller["feedback_count"] = whole_number(edit, "feedbackCount", 0, MAX_FEEDBACK_COUNT)
        seller["odr_pct"] = optional_number(edit, "odrPct", 0, 100)
        seller["brand_status"] = brand_status
        orders = edit.get("ordersInWindow")
        seller["orders_in_window"] = None if orders is None else whole_number(edit, "ordersInWindow", 1, MAX_ORDERS)
        complaints = whole_number(edit, "recentComplaints", 0, MAX_RECENT_COMPLAINTS)
        confirmed = flag(edit, "confirmedCounterfeit")
        if not flag(edit, "complaintsAvailable"):
            seller["complaints"] = None
            continue
        seller["complaints"] = [{"id": f"{seller['id']}-E{i}", "order_id": f"{seller['id']}-EO{i}",
                                 "date": (cutoff - timedelta(days=i * 4)).isoformat(),
                                 "confirmed_counterfeit": confirmed and i == 0}
                                for i in range(max(complaints, 1 if confirmed else 0))]
    return edited


def extra_fake_reviews(seller_id: str, count: int, cutoff: date) -> List[Review]:
    """`count` recent 1-star authenticity reviews; texts cycle, so repeats count as copies."""
    texts = TEMPLATES["authenticity"]
    return [Review(review_id=f"{seller_id}-X{i}", stars=1, text=texts[i % len(texts)],
                   review_date=cutoff - timedelta(days=i), reviewer_id=f"{seller_id}-XU{i}")
            for i in range(count)]


def rescore(listing: Dict[str, Any], reviews_by_seller: Dict[str, List[Review]],
            edits: Dict[str, Any]) -> Dict[str, Any]:
    """Score the listing after applying the edits; returns a validated data.json document.

    :raises ValueError: for invalid edits.
    """
    edited = apply_edits(listing, edits)
    cutoff = date.fromisoformat(edited["data_cutoff"])
    reviews = {k: list(v) for k, v in reviews_by_seller.items()}
    for edit in edits.get("sellers") or []:
        count = whole_number(edit, "extraFakeReviews", 0, MAX_EXTRA_REVIEWS)
        reviews.setdefault(edit["id"], []).extend(extra_fake_reviews(edit["id"], count, cutoff))
    product, context = parse_listing(edited, reviews)
    doc = build_document(product, [score_offer(s, context) for s in context.sellers],
                         context.data_cutoff)
    problems = validate(doc)
    if problems:
        raise ValueError("Scored document is invalid: " + "; ".join(problems))
    return doc


class DemoHandler(SimpleHTTPRequestHandler):
    """Static files from the site root, plus GET /api/inputs and POST /api/score."""

    listing: Dict[str, Any] = {}
    reviews_by_seller: Dict[str, List[Review]] = {}

    def end_headers(self) -> None:
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-store")  # edited frontend files reach the browser at once
        super().end_headers()

    def do_GET(self) -> None:
        if self.path.split("?")[0] == "/api/inputs":
            self.send_json(200, editable_inputs(self.listing))
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path.split("?")[0] != "/api/score":
            self.send_json(404, {"error": "Not found."})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            edits = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(edits, dict):
                raise ValueError("Request body must be a JSON object.")
            self.send_json(200, rescore(self.listing, self.reviews_by_seller, edits))
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json(400, {"error": str(error)})

    def send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def serve(site_root: Path, listing_path: Path, reviews_path: Path, port: int) -> None:
    """Serve the site on 127.0.0.1:port until interrupted."""
    DemoHandler.listing = json.loads(listing_path.read_text(encoding="utf-8"))
    DemoHandler.reviews_by_seller = load_seller_reviews(reviews_path)
    handler = partial(DemoHandler, directory=str(site_root))
    with ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving {site_root} with live re-scoring at http://localhost:{port}  (Ctrl+C to stop)")
        httpd.serve_forever()
