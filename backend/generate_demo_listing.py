"""Generate the synthetic iPhone listing (sellers A-D) that the pipeline scores into data.json.

Seeded and deterministic. Reviews use phone-specific templates in the same text classes as the
research generator (research/generate_synthetic_indian_products.py). Each seller's inputs are
written to produce the persona statuses in the plan; the weights are not tuned to them.

Run from backend/:  python generate_demo_listing.py
"""

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

SEED = 4025
DATA_CUTOFF = date(2026, 11, 6)
OUT_DIR = Path(__file__).resolve().parent / "inputs"

TEMPLATES = {
    "positive": [
        "Genuine Apple product, sealed box and the serial number checked out on Apple's site.",
        "Phone arrived quickly and works perfectly. Very happy with the purchase.",
        "Display and camera are excellent. Activation was smooth.",
        "Packaging was intact and the phone is brand new.",
        "Great seller, the phone matched the listing exactly.",
        "Battery life is good and the phone feels premium.",
        "Smooth delivery and the invoice was included.",
        "Exactly what I ordered, no issues so far.",
    ],
    "neutral": [
        "Phone is fine but delivery took longer than promised.",
        "Works as expected, though the price is high.",
        "Average experience, nothing special about the seller.",
    ],
    "generic_negative": [
        "Battery drains faster than I expected for the price.",
        "Delivery was late and the outer box was dented.",
        "Waste of money for me, the phone heats up while gaming.",
        "Customer support was slow to respond to my questions.",
        "Poor quality packaging, the outer carton was torn.",
    ],
    "authenticity": [
        "Battery health showed 91% on day one. This is not a genuine new phone.",
        "The box seal had been opened and resealed, and the phone feels fake.",
        "IMEI on the phone did not match the box label, I think this is a duplicate unit.",
        "Charger and cable look like a knock-off, not original Apple accessories.",
        "Serial number check failed on Apple's site, this seems counterfeit.",
        "Logo print is uneven and the phone is not an original unit.",
    ],
    "wrong_item": [
        "Received a different model from the one I ordered.",
        "Wrong colour arrived, I ordered Glacier.",
        "Sent a different variant with 256 GB instead of 1 TB.",
        "This is not what I ordered, the storage is smaller.",
    ],
    "mismatch": [
        "Box contents are not as described, the cable shown in the listing was missing.",
        "Phone colour does not match the picture on the listing.",
        "The finish is not as shown in the product photos.",
        "Misleading description, the listing says sealed but the box was open.",
    ],
}

PRODUCT = {
    "title": ("Apple iPhone 18 Pro Max (1 TB) - Glacier | 17.42 cm (6.9″) Super Retina XDR Display "
              "with ProMotion, A20 Pro Chip, 48MP Fusion Main Camera with Variable Aperture"),
    "shortTitle": "Apple iPhone 18 Pro Max (1 TB) - Glacier",
    "store": "Visit the Apple Store",
    "rating": 4.5,
    "ratingCount": 1284,
    "image": "assets/product.jpg",
    "breadcrumb": ["Electronics", "Mobiles & Accessories", "Smartphones"],
    "bullets": [
        "17.42 cm (6.9″) Super Retina XDR display with ProMotion",
        "A20 Pro chip",
        "48MP Fusion main camera with variable aperture",
        "1 TB storage, Glacier finish",
    ],
}

# Per seller: profile, review mix as (text class, stars choices, count), copies of one allegation,
# review span in days, and complaints as (age in days, order id, confirmed counterfeit).
SELLERS = [
    {"id": "A", "name": "NovaMobile Authorised", "price": 254900,
     "delivery": "FREE delivery Tomorrow, 8 November", "days_selling": 6 * 365 + 40,
     "positive_feedback_pct": 98.0, "feedback_count": 8410, "odr_pct": 0.4,
     "brand_status": "verified", "orders_in_window": 900,
     "mix": [("positive", (4, 5), 124), ("neutral", (3,), 8), ("generic_negative", (1, 2), 8)],
     "copies": 0, "span": 400, "complaints": []},
    {"id": "B", "name": "Metro Phone Hub", "price": 249990,
     "delivery": "FREE delivery Monday, 10 November", "days_selling": 3 * 365 + 20,
     "positive_feedback_pct": 94.0, "feedback_count": 1920, "odr_pct": 0.8,
     "brand_status": "not_authorised", "orders_in_window": 310,
     "mix": [("positive", (4, 5), 90), ("neutral", (3,), 6), ("generic_negative", (1, 2), 6),
             ("mismatch", (1, 2), 4), ("wrong_item", (1, 2), 2)],
     "copies": 4, "span": 360, "complaints": [(140, "B-O-1187", False)]},
    {"id": "C", "name": "QuickDeal Gadgets", "price": 164999,
     "delivery": "Delivery Wednesday, 12 November · ₹99", "days_selling": 125,
     "positive_feedback_pct": 81.0, "feedback_count": 46, "odr_pct": 2.6,
     "brand_status": "not_authorised", "orders_in_window": 38,
     "mix": [("positive", (4, 5), 14), ("neutral", (3,), 2), ("generic_negative", (1, 2), 4),
             ("authenticity", (1, 2), 4), ("wrong_item", (1, 2), 1)],
     "copies": 2, "span": 120,
     "complaints": [(12, "C-O-0031", False), (37, "C-O-0022", False), (40, "C-O-0022", False),
                    (71, "C-O-0009", False)]},
    {"id": "D", "name": "FreshTech Store", "price": 252000,
     "delivery": "FREE delivery Tuesday, 11 November", "days_selling": 21,
     "positive_feedback_pct": None, "feedback_count": 0, "odr_pct": None,
     "brand_status": "unverified", "orders_in_window": 6,
     "mix": [("positive", (5,), 2)], "copies": 0, "span": 20, "complaints": []},
    {"id": "E", "name": "MegaSteal Deals", "price": 4999,
     "delivery": "FREE delivery Friday, 14 November", "days_selling": 30,
     "positive_feedback_pct": None, "feedback_count": 3, "odr_pct": None,
     "brand_status": "unverified", "orders_in_window": 3,
     "mix": [("positive", (5,), 3)], "copies": 0, "span": 25, "complaints": []},
]


def seller_reviews(seller: Dict, rng: random.Random) -> List[Dict]:
    """Review rows for one seller; the first allegation is re-posted `copies` times."""
    rows = []
    for text_class, stars, count in seller["mix"]:
        for i in range(count):
            rows.append({"text": TEMPLATES[text_class][i % len(TEMPLATES[text_class])],
                         "stars": rng.choice(stars), "class": text_class})
    allegation = next((r for r in rows if r["class"] in ("authenticity", "wrong_item", "mismatch")), None)
    for _ in range(seller["copies"] if allegation else 0):
        rows.append(dict(allegation))
    out = []
    for i, row in enumerate(rows):
        review_date = DATA_CUTOFF - timedelta(days=rng.randrange(seller["span"]))
        out.append({"seller_id": seller["id"], "review_id": f"{seller['id']}-R{i:03d}",
                    "reviewer_id": f"{seller['id']}-U{i:03d}", "date": review_date.isoformat(),
                    "stars": row["stars"], "text": row["text"]})
    return sorted(out, key=lambda r: (r["date"], r["review_id"]))


def listing_document() -> Dict:
    """The demo listing JSON (product, brand, cutoff and seller profiles with complaints)."""
    sellers = []
    for s in SELLERS:
        profile = {k: s[k] for k in ("id", "name", "price", "delivery", "days_selling",
                                     "positive_feedback_pct", "feedback_count", "odr_pct",
                                     "brand_status", "orders_in_window")}
        profile["complaints"] = [
            {"id": f"{s['id']}-C{i}", "date": (DATA_CUTOFF - timedelta(days=age)).isoformat(),
             "order_id": order_id, "confirmed_counterfeit": confirmed}
            for i, (age, order_id, confirmed) in enumerate(s["complaints"])]
        sellers.append(profile)
    return {"_note": "Synthetic demo listing. Generated by generate_demo_listing.py; do not edit.",
            "data_cutoff": DATA_CUTOFF.isoformat(), "brand": "Apple", "product": PRODUCT,
            "sellers": sellers}


def main() -> None:
    rng = random.Random(SEED)
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "demo_listing.json").write_text(
        json.dumps(listing_document(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rows = [r for s in SELLERS for r in seller_reviews(s, rng)]
    with (OUT_DIR / "demo_reviews.csv").open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["seller_id", "review_id", "reviewer_id",
                                                    "date", "stars", "text"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(SELLERS)} sellers and {len(rows)} reviews to {OUT_DIR}")


if __name__ == "__main__":
    main()
