"""Scoring review analyses: threshold comparison, band sensitivity and profitability scenarios.

Run from backend/:  python analysis/scoring_review.py
Writes reports/scoring_review.json. Uses the committed synthetic scenarios and demo inputs;
the real-data part needs research/data (gitignored).
"""

import itertools
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from trust_score import config  # noqa: E402
from trust_score.loaders import load_indian_products, load_listing, load_synthetic  # noqa: E402
from trust_score.review_screen import assess_reviews  # noqa: E402

FACTORS = ("history", "brand", "price", "reviews", "complaints")
CURRENT_WEIGHTS = {"history": 20, "brand": 25, "price": 20, "reviews": 20, "complaints": 15}
EQUAL_WEIGHTS = {k: 20 for k in FACTORS}
CAPPING = ("reviews", "complaints", "price")


def reviews_status(reviews, threshold):
    """Reviews-factor status with a given low-star share threshold (other rules unchanged)."""
    ev = assess_reviews(reviews)
    if ev.total < config.MIN_REVIEWS:
        return "na", ev
    concentrated = (ev.low_star_share is not None and ev.low_star_share >= threshold
                    and len(ev.distinct_allegations) >= 1)
    return ("warn" if ev.repeated or concentrated else "pass"), ev


def threshold_comparison():
    grouped, scenarios, _ = load_synthetic(
        BACKEND / "research/outputs/synthetic_indian_products/reviews_synthetic.csv")
    _, context = load_listing(BACKEND / "inputs/demo_listing.json", BACKEND / "inputs/demo_reviews.csv")
    listings = {f"synthetic:{k}": (scenarios[k], v) for k, v in grouped.items()}
    listings.update({f"demo:{s.seller_id}": ("demo seller", s.reviews) for s in context.sellers})
    real_path = BACKEND / "research/data/indian-products-on-amazon/amazon_vfl_reviews.csv"
    if real_path.exists():
        listings.update({f"real:{k}": ("real product", v) for k, v in load_indian_products(real_path).items()})
    rows, by_threshold = [], {}
    for name, (group, reviews) in listings.items():
        statuses = {t: reviews_status(reviews, t)[0] for t in config.SHARE_SENSITIVITY_THRESHOLDS}
        ev = reviews_status(reviews, 0.25)[1]
        rows.append({"listing": name, "group": group, "statuses": statuses,
                     "share": None if ev.low_star_share is None else round(ev.low_star_share, 4),
                     "distinct_allegations": len(ev.distinct_allegations), "repeated": ev.repeated})
    for t in config.SHARE_SENSITIVITY_THRESHOLDS:
        by_threshold[f"{round(t * 100)}%"] = dict(Counter(r["statuses"][t] for r in rows))
    changed = [r for r in rows if len(set(r["statuses"].values())) > 1]
    return {
        "listings": len(rows),
        "groups": dict(Counter(r["group"].split(":")[0] if r["group"] != "real product" else "real product" for r in rows)),
        "status_counts_by_threshold": by_threshold,
        "listings_whose_status_changes": [
            {k: r[k] for k in ("listing", "group", "share", "distinct_allegations")}
            | {"statuses": {f"{round(t * 100)}%": s for t, s in r["statuses"].items()}} for r in changed],
        "real_products_meeting_polar_gate": sum(1 for r in rows if r["group"] == "real product" and r["share"] is not None),
        "warns_where_repeated_rule_already_fires": sum(1 for r in rows if r["repeated"] and r["statuses"][0.25] == "warn"),
    }


def band(statuses, weights, high=75, medium=50, cap=True, na_as_zero=False):
    """Band for a factor-status profile, mirroring scoring.py with switchable choices."""
    na = [k for k in FACTORS if statuses[k] == "na"]
    if len(na) > config.MAX_NA_FACTORS:
        return "Not enough data", None
    available = sum(weights.values()) if na_as_zero else sum(weights[k] for k in FACTORS if k not in na)
    earned = sum(weights[k] for k in FACTORS if statuses[k] == "pass")
    score = (200 * earned + available) // (2 * available)
    base = "High" if score >= high else "Medium" if score >= medium else "Low"
    if cap and base == "High" and any(statuses[k] == "warn" for k in CAPPING):
        base = "Medium"
    return base, score


def sensitivity():
    profiles = [dict(zip(FACTORS, combo)) for combo in itertools.product(("pass", "warn", "na"), repeat=5)]
    variants = {
        "current (weights 20/25/20/20/15, 75/50, cap)": dict(weights=CURRENT_WEIGHTS),
        "equal weights, 75/50, cap": dict(weights=EQUAL_WEIGHTS),
        "current weights, no cap": dict(weights=CURRENT_WEIGHTS, cap=False),
        "equal weights, no cap": dict(weights=EQUAL_WEIGHTS, cap=False),
        "current weights, cut-offs 80/55": dict(weights=CURRENT_WEIGHTS, high=80, medium=55),
        "current weights, cut-offs 70/45": dict(weights=CURRENT_WEIGHTS, high=70, medium=45),
        "current weights, na scored as 0": dict(weights=CURRENT_WEIGHTS, na_as_zero=True),
    }
    baseline = {i: band(p, CURRENT_WEIGHTS)[0] for i, p in enumerate(profiles)}
    scored = [i for i, b in baseline.items() if b != "Not enough data"]
    out = {"profiles": len(profiles), "scored_profiles": len(scored),
           "baseline_band_counts": dict(Counter(baseline[i] for i in scored)), "variants": {}}
    for name, kwargs in variants.items():
        changes = defaultdict(int)
        examples = []
        for i in scored:
            new = band(profiles[i], **kwargs)[0]
            if new != baseline[i]:
                changes[f"{baseline[i]} -> {new}"] += 1
                if len(examples) < 4:
                    examples.append({"profile": profiles[i], "baseline": baseline[i], "variant": new})
        total = sum(changes.values())
        out["variants"][name] = {"profiles_changed": total, "share_changed": round(total / len(scored), 3),
                                 "transitions": dict(changes), "examples": examples}
    demo = {"A": dict(history="pass", brand="pass", price="pass", reviews="pass", complaints="pass"),
            "B": dict(history="pass", brand="warn", price="pass", reviews="warn", complaints="pass"),
            "C": dict(history="warn", brand="warn", price="warn", reviews="warn", complaints="warn")}
    out["demo_sellers"] = {s: {name: band(p, **kw)[0] for name, kw in variants.items()} for s, p in demo.items()}
    single = {}
    for k in FACTORS:
        p = {f: "pass" for f in FACTORS}
        p[k] = "warn"
        single[k] = {"current": band(p, CURRENT_WEIGHTS), "equal": band(p, EQUAL_WEIGHTS)}
    out["single_warning_profiles"] = single
    return out


SCENARIOS = {
    # All values are labelled assumptions for illustration, not measurements.
    "pessimistic": dict(flag_exposure=0.10, purchase_rate=0.08, switch=0.10, abandon=0.15,
                        incident_flagged=0.005, incident_higher=0.002, incident_cost=0.05,
                        contribution=0.040, feature_cost_per_session=0.05),
    "base": dict(flag_exposure=0.10, purchase_rate=0.08, switch=0.25, abandon=0.08,
                 incident_flagged=0.020, incident_higher=0.003, incident_cost=0.10,
                 contribution=0.035, feature_cost_per_session=0.02),
    "optimistic": dict(flag_exposure=0.10, purchase_rate=0.08, switch=0.40, abandon=0.03,
                       incident_flagged=0.050, incident_higher=0.003, incident_cost=0.15,
                       contribution=0.030, feature_cost_per_session=0.01),
}
PRICE = 25000  # assumed average order value for an eligible branded-electronics session (₹)


def contribution_change(p, price=PRICE):
    """Incremental Amazon contribution per eligible session (₹).

    Among sessions that see a flagged offer and would have bought it: switchers keep the order
    (same product, so the same commission) and move to a lower incident rate; abandoners lose
    the order's contribution but also avoid its expected incident cost.
    """
    buyers = p["flag_exposure"] * p["purchase_rate"]
    switch_gain = p["switch"] * (p["incident_flagged"] - p["incident_higher"]) * p["incident_cost"] * price
    abandon_effect = p["abandon"] * (p["incident_flagged"] * p["incident_cost"] - p["contribution"]) * price
    return buyers * (switch_gain + abandon_effect) - p["feature_cost_per_session"]


def break_even_abandon(p, price=PRICE):
    """Abandonment rate at which the incremental contribution is zero (others fixed)."""
    buyers = p["flag_exposure"] * p["purchase_rate"]
    switch_gain = p["switch"] * (p["incident_flagged"] - p["incident_higher"]) * p["incident_cost"] * price
    per_abandon = (p["incident_flagged"] * p["incident_cost"] - p["contribution"]) * price
    if per_abandon >= 0:
        return None  # abandonment never reduces contribution under these values
    return (buyers * switch_gain - p["feature_cost_per_session"]) / (-buyers * per_abandon)


def profitability():
    out = {"price_assumption_inr": PRICE, "scenarios": {}}
    for name, p in SCENARIOS.items():
        out["scenarios"][name] = {"assumptions": p,
                                  "delta_contribution_per_1000_sessions_inr": round(1000 * contribution_change(p), 0),
                                  "break_even_abandon_rate": None if break_even_abandon(p) is None
                                  else round(break_even_abandon(p), 4)}
    base = SCENARIOS["base"]
    grid = {}
    for inc in (0.005, 0.01, 0.02, 0.05):
        for ab in (0.02, 0.05, 0.08, 0.15):
            grid[f"incident_flagged={inc}, abandon={ab}"] = round(
                1000 * contribution_change(dict(base, incident_flagged=inc, abandon=ab)), 0)
    out["base_grid_per_1000_sessions_inr"] = grid
    return out


def main():
    report = {"threshold_comparison": threshold_comparison(), "sensitivity": sensitivity(),
              "profitability": profitability()}
    path = BACKEND / "reports/scoring_review.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
