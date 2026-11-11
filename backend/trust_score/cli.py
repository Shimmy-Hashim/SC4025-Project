"""Command line for the offline scoring pipeline. Run from backend/: python -m trust_score.cli -h"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

from trust_score.config import (
    LOW_STAR_SHARE_THRESHOLD,
    MIN_POLAR_REVIEWS,
    SHARE_SENSITIVITY_THRESHOLDS,
)
from trust_score.export import build_document, validate
from trust_score.factors import ListingContext, ReviewsFactor
from trust_score.loaders import load_indian_products, load_listing, load_synthetic
from trust_score.models import Review, SellerRecord
from trust_score.review_screen import (
    assess_reviews,
    is_allegation,
    is_candidate,
    is_high_star,
    is_low_star,
    low_star_share,
    trend_rising,
)
from trust_score.scoring import score_offer
from trust_score.server import serve
from trust_score.text import matched_rules

BACKEND = Path(__file__).resolve().parent.parent
RESEARCH = BACKEND / "research"
INDIAN_CSV = RESEARCH / "data/indian-products-on-amazon/amazon_vfl_reviews.csv"
SYNTHETIC_DIR = RESEARCH / "outputs/synthetic_indian_products"
REPORTS = BACKEND / "reports"

# Expected outcome of the reviews factor per synthetic scenario: (status, warn route).
# "repeated" = 2+ distinct allegations; "concentration" = share >= 25% with an allegation.
SCENARIO_EXPECTATIONS = {
    "stable_positive": ("pass", None),
    "isolated_concern": ("pass", None),
    "authenticity_surge": ("warn", "repeated"),
    "mismatch_surge": ("warn", "repeated"),
    "generic_quality_surge": ("pass", None),
    "historical_recovery": ("warn", "repeated"),
    "sparse_history": ("na", None),
    "copied_complaint_burst": ("warn", "concentration"),
    "context_trap_burst": ("pass", None),
}


def cmd_build(args: argparse.Namespace) -> int:
    product, context = load_listing(args.listing, args.reviews)
    doc = build_document(product, [score_offer(s, context) for s in context.sellers],
                         context.data_cutoff)
    problems = validate(doc)
    if problems:
        print("Generated document is invalid:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    args.out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for s in doc["sellers"]:
        print(f"{s['id']} {s['name']:24} {s['band']:16} score={s['score']}")
    print(f"Wrote {args.out}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    problems = validate(json.loads(args.path.read_text(encoding="utf-8")))
    print("\n".join(problems) if problems else f"{args.path} is valid.")
    return 1 if problems else 0


def cmd_screen(args: argparse.Namespace) -> int:
    by_asin = load_indian_products(args.csv)
    reviews = [r for listing in by_asin.values() for r in listing]
    low = [r for r in reviews if is_low_star(r)]
    rule_counts = Counter(rule for r in low for rule in matched_rules(r.text))
    summary = {
        "source": "Indian Products on Amazon (nehaprabhavalkar), prepared as in the research",
        "scope": "Product-level regex stage only. Not seller-level, not validated complaint labels.",
        "nonempty_reviews": len(reviews),
        "asins": len(by_asin),
        "one_or_two_star_reviews": len(low),
        "low_star_with_any_selected_wording": sum(bool(matched_rules(r.text)) for r in low),
        "low_star_with_authenticity_or_mismatch_wording": sum(is_candidate(r) for r in reviews),
        "stage2_interpreted_allegations": sum(is_allegation(r) for r in reviews),
        "low_star_rule_counts": dict(sorted(rule_counts.items())),
        "listing_share_sensitivity": share_sensitivity(by_asin),
    }
    write_report("screen_indian_products.json", summary)
    return 0


def share_sensitivity(by_listing: Dict[str, List[Review]]) -> Dict[str, int]:
    """Listings meeting the 20-polar-review gate, and how many reach each share threshold."""
    shares = []
    for listing in by_listing.values():
        low = sum(is_low_star(r) for r in listing)
        high = sum(is_high_star(r) for r in listing)
        if low + high >= MIN_POLAR_REVIEWS:
            shares.append(low_star_share(low, high))
    out = {"listings_meeting_polar_gate": len(shares)}
    for t in SHARE_SENSITIVITY_THRESHOLDS:
        out[f"at_or_above_{round(t * 100)}pct"] = sum(s >= t for s in shares)
    return out


def cmd_check_synthetic(args: argparse.Namespace) -> int:
    grouped, scenarios, research_specific = load_synthetic(args.dir / "reviews_synthetic.csv")
    research = json.loads((args.dir / "calibration_and_validation.json").read_text())["scenario_checks"]
    ours = defaultdict(lambda: {"ratio_25pct_flags": 0, "wording_increase_flags": 0})
    outcomes = defaultdict(Counter)
    failures = []
    for listing_id, reviews in grouped.items():
        scenario = scenarios[listing_id]
        if sum(is_candidate(r) for r in reviews) != research_specific[listing_id]:
            failures.append(f"{listing_id}: stage 1 candidate count differs from research screen")
        low = sum(is_low_star(r) for r in reviews)
        high = sum(is_high_star(r) for r in reviews)
        ours[scenario]["ratio_25pct_flags"] += (low + high >= MIN_POLAR_REVIEWS and
                                                low_star_share(low, high) >= LOW_STAR_SHARE_THRESHOLD)
        ours[scenario]["wording_increase_flags"] += bool(trend_rising(reviews, is_candidate))
        status, route = reviews_outcome(listing_id, reviews)
        outcomes[scenario][f"{status}/{route}"] += 1
        expected = SCENARIO_EXPECTATIONS.get(scenario)
        if expected and (status, route) != expected:
            failures.append(f"{listing_id} ({scenario}): got {status}/{route}, expected {expected}")
    for scenario, counts in research.items():
        for key in ("ratio_25pct_flags", "wording_increase_flags"):
            if ours[scenario][key] != counts[key]:
                failures.append(f"{scenario} {key}: ours {ours[scenario][key]} vs research {counts[key]}")
    write_report("check_synthetic.json", {
        "scope": "Rule behaviour on designed scenarios. Not real-world detection accuracy.",
        "flag_counts_ours_vs_research": {s: {"ours": ours[s], "research": {
            k: research[s][k] for k in ("ratio_25pct_flags", "wording_increase_flags")}} for s in research},
        "reviews_factor_outcomes": {s: dict(c) for s, c in outcomes.items()},
        "expectations": {s: list(e) for s, e in SCENARIO_EXPECTATIONS.items()},
        "note": "Flag counts use stage 1 (Checkpoint 1) to reproduce the research. Outcomes use "
                "stage 2. context_trap_burst passes only because its templates use phrases the "
                "stage 2 exclusions were written for; this is not independent evidence.",
        "failures": failures,
    })
    print("\n".join(failures) if failures else "All synthetic checks passed.")
    return 1 if failures else 0


def reviews_outcome(listing_id: str, reviews: List[Review]):
    """Reviews-factor status for a listing and which warn route fired (or None)."""
    seller = SellerRecord(seller_id=listing_id, name=listing_id, price=0, delivery="",
                          days_selling=365, reviews=reviews)
    context = ListingContext(brand="", data_cutoff=max(r.review_date for r in reviews),
                             sellers=[seller])
    result = ReviewsFactor().evaluate(seller, context)
    if result.status != "warn":
        return result.status, None
    evidence = assess_reviews(reviews)
    return result.status, "repeated" if evidence.repeated else "concentration"


def write_report(name: str, payload: Dict) -> None:
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / name
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="trust_score", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build", help="score the demo listing and write data.json")
    b.add_argument("--listing", type=Path, default=BACKEND / "inputs/demo_listing.json")
    b.add_argument("--reviews", type=Path, default=BACKEND / "inputs/demo_reviews.csv")
    b.add_argument("--out", type=Path, default=BACKEND.parent / "data.json")
    b.set_defaults(func=cmd_build)
    v = sub.add_parser("validate", help="check a data.json the way the frontend does")
    v.add_argument("path", type=Path)
    v.set_defaults(func=cmd_validate)
    s = sub.add_parser("screen", help="run the review screen on the real Indian Products data")
    s.add_argument("--csv", type=Path, default=INDIAN_CSV)
    s.set_defaults(func=cmd_screen)
    c = sub.add_parser("check-synthetic", help="check rule behaviour on the research scenarios")
    c.add_argument("--dir", type=Path, default=SYNTHETIC_DIR)
    c.set_defaults(func=cmd_check_synthetic)
    sv = sub.add_parser("serve", help="serve the site with live re-scoring of edited inputs")
    sv.add_argument("--port", type=int, default=8000)
    sv.add_argument("--listing", type=Path, default=BACKEND / "inputs/demo_listing.json")
    sv.add_argument("--reviews", type=Path, default=BACKEND / "inputs/demo_reviews.csv")
    sv.set_defaults(func=cmd_serve)
    return p


def cmd_serve(args: argparse.Namespace) -> int:
    serve(BACKEND.parent, args.listing, args.reviews, args.port)
    return 0


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
