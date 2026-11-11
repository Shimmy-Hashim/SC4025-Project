"""Generate reproducible, real-informed prototype fixtures using only Python stdlib.

Indian Products on Amazon is the calibration source. General Amazon is NOT an
input to generation. Constructed scenarios are not observed counterfeit events.
"""
import argparse
import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from analyse_listing_evidence import load_supplement, norm

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
DEFAULT_DEST = OUT / "synthetic_indian_products"
RAW = ROOT / "data/indian-products-on-amazon/amazon_vfl_reviews.csv"
PREPARED = OUT / "indian_reviews_deduplicated_flagged.csv"
CONTEXT = OUT / "listing_context_audit.json"
RULE_FILE = OUT / "low_star_review_analysis.json"
CHECKPOINT = ROOT / "checkpoints/checkpoint_01_low_star_and_text.json"
ORIGINAL = ["asin", "name", "date", "rating", "review"]
EXTRA = ["source_dataset", "is_synthetic", "review_record_id", "screen_low_star",
         "screen_any_wording", "screen_specific_wording", "synthetic_scenario",
         "synthetic_phase", "synthetic_reviewer_id", "synthetic_template_family",
         "synthetic_intended_text_class", "synthetic_reference_asin",
         "synthetic_reference_collection_family", "synthetic_dataset_cutoff",
         "synthetic_seed", "synthetic_generation_method", "fraud_ground_truth"]
SCENARIOS = ["empirical_reference", "stable_positive", "isolated_concern",
             "authenticity_surge", "mismatch_surge", "generic_quality_surge",
             "historical_recovery", "sparse_history", "copied_complaint_burst",
             "context_trap_burst"]

# Hand-designed semantic families, expanded in a loop; no per-row LLM calls.
TEMPLATES = {
    "positive": [
        "The item arrived in good condition and works as expected.",
        "I am happy with the product and the packaging was intact.",
        "The product is satisfactory for my usual use.",
        "The quality meets my expectations after trying the item."],
    "neutral": [
        "The item is average and there is room for improvement.",
        "Some aspects are satisfactory but the overall experience is mixed.",
        "It is an ordinary product for the price.",
        "I have used it briefly and have mixed views."],
    "other_negative": [
        "The item stopped performing properly after a short period.",
        "The package arrived damaged and the experience was disappointing.",
        "The product did not perform well during my usual use.",
        "I had a disappointing experience with the item."],
    "generic_dissatisfaction": [
        "This was a waste of money because the performance was disappointing.",
        "The product is not good at all and I am dissatisfied with its quality.",
        "The poor quality made the item disappointing to use.",
        "The bad quality is the reason for my low rating."],
    "authenticity_concern": [
        "I suspect this item is fake because the packaging differs from my previous purchase.",
        "The label and finish make me doubt that this is an original product; it may be counterfeit.",
        "This does not look genuine to me; I suspect a duplicate product after comparing the label.",
        "The packaging looks unusual and I think the item is not original."],
    "mismatch_concern": [
        "The information on the received label is not as described on the product page.",
        "The received product is not as advertised when I compare its label with the listing.",
        "The package does not match the description that influenced my purchase.",
        "The item is not as shown in the listing pictures."],
    "wrong_item_concern": [
        "I received a different product from the one I ordered.",
        "The wrong item arrived even though I selected the intended product.",
        "The seller sent a different size from the size stated in my order.",
        "I received the wrong brand instead of the one shown in my order."],
    "ambiguous_specific_wording": [
        "I dislike the fake reviews online, but I am making no claim about this item's authenticity.",
        "I ordered the wrong size myself; the delivered item matches my selected order.",
        "This is not fake; my dissatisfaction concerns delivery delays.",
        "Calling it a duplicate of a competing product is a comparison, not an authentication result."],
}
LEADS = ["", "After checking the item, ", "Based on my purchase experience, ",
         "Having tried the product, "]
ENDS = ["", " This describes my experience with this purchase.",
        " I checked the packaging before using it.",
        " I am sharing my experience to explain my rating."]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(row, annotations, patterns):
    annotation = annotations.get(row["record_id"], {})
    if annotation.get("target_relevant_allegation"):
        return ("mismatch_concern" if annotation["context_class"] == "mismatch_allegation"
                else "authenticity_concern")
    if any(patterns[k].search(row["text"]) for k in
           ["counterfeit_wording", "wrong_product_wording", "not_as_advertised_wording"]):
        return "ambiguous_specific_wording"
    if any(p.search(row["text"]) for p in patterns.values()):
        return "generic_dissatisfaction"
    return "other_negative" if row["stars"] <= 2 else "neutral" if row["stars"] == 3 else "positive"


def screen(row, patterns):
    low = int(float(row["rating"]) <= 2)
    return {"screen_low_star": low,
            "screen_any_wording": int(low and any(p.search(row["review"]) for p in patterns.values())),
            "screen_specific_wording": int(low and any(patterns[k].search(row["review"]) for k in
                ["counterfeit_wording", "wrong_product_wording", "not_as_advertised_wording"]))}


def load_inputs():
    rules = json.loads(RULE_FILE.read_text(encoding="utf-8"))["patterns"]
    patterns = {k: re.compile(v, re.I) for k, v in rules.items()}
    annotations = {r["record_id"]: r for r in json.loads(CONTEXT.read_text(encoding="utf-8"))["annotations"]}
    rows = load_supplement()
    states = [{"rating": int(r["stars"]), "text_class": classify(r, annotations, patterns)} for r in rows]
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["asin"]].append(r)
    families = defaultdict(list)
    for asin, reviews in sorted(grouped.items()):
        signature = json.dumps(sorted((r["date_or_timestamp"], r["stars"], norm(r["text"])) for r in reviews))
        family = hashlib.sha256(signature.encode()).hexdigest()[:20]
        families[family].append(asin)
    first = min(date.fromisoformat(r["date_or_timestamp"]) for r in rows)
    last = max(date.fromisoformat(r["date_or_timestamp"]) for r in rows)
    profiles = []
    for family, asins in sorted(families.items()):
        representative = sorted(asins)[0]
        endpoint = max(date.fromisoformat(r["date_or_timestamp"]) for r in grouped[representative])
        if endpoint >= first + timedelta(days=180):
            profiles.append({"reference_asin": representative, "family": family, "cutoff": endpoint})
    star_counts = Counter(s["rating"] for s in states)
    class_counts = Counter(s["text_class"] for s in states)
    calibration = {"primary_source": "nehaprabhavalkar/indian-products-on-amazon",
        "primary_url": "https://www.kaggle.com/datasets/nehaprabhavalkar/indian-products-on-amazon",
        "usable_real_reviews": len(rows), "real_asins": len(grouped),
        "date_min": first.isoformat(), "date_max": last.isoformat(),
        "star_counts": dict(sorted(star_counts.items())), "screening_text_state_counts": dict(class_counts),
        "rating_text_joint_counts": dict(Counter(f"{s['rating']}|{s['text_class']}" for s in states)),
        "low_star_reviews": sum(r["stars"] <= 2 for r in rows),
        "low_star_any_wording": sum(r["stars"] <= 2 and any(p.search(r["text"]) for p in patterns.values()) for r in rows),
        "low_star_specific_wording": sum(r["stars"] <= 2 and any(patterns[k].search(r["text"]) for k in
            ["counterfeit_wording", "wrong_product_wording", "not_as_advertised_wording"]) for r in rows),
        "assistant_context_relevant_low_star_reviews": sum(annotations.get(r["record_id"], {}).get("target_relevant_allegation", False) for r in rows),
        "distinct_full_collection_families": len(families),
        "copied_full_collections": [asins for asins in families.values() if len(asins) > 1],
        "eligible_historical_anchor_profiles": len(profiles),
        "calibration_weighting": "Pooled 1388 prepared reviews; collection copies remain in this descriptive distribution. Anchor profiles use one representative per identical collection family.",
        "context_label_limit": "Assistant judgments and a keyword heuristic, not independently adjudicated outcomes. Above-two-star specific wording is unreviewed context, not established irrelevance.",
        "general_amazon_used_to_generate": False}
    assert len(rows) == 1388 and len(grouped) == 145
    assert (calibration["low_star_reviews"], calibration["low_star_any_wording"],
            calibration["low_star_specific_wording"], calibration["assistant_context_relevant_low_star_reviews"]) == (338, 77, 42, 39)
    return rows, states, patterns, profiles, calibration


def controlled_states(scenario, phase, rng, states):
    if scenario == "empirical_reference":
        return [dict(rng.choice(states)) for _ in range(60)]
    if scenario == "sparse_history":
        low, neutral, high, target = (1, 0, 5, 0) if phase == "previous" else (4, 0, 2, 3)
    else:
        surge = ((scenario in {"authenticity_surge", "mismatch_surge", "generic_quality_surge",
                    "copied_complaint_burst", "context_trap_burst"} and phase == "recent")
                 or (scenario == "historical_recovery" and phase == "previous"))
        low, neutral, high = (36, 4, 20) if surge else (6, 4, 50)
        target = 24 if surge and scenario != "generic_quality_surge" else 0
        if scenario == "isolated_concern" and phase == "recent":
            target = 1
    low_ratings = [s["rating"] for s in states if s["rating"] <= 2]
    high_ratings = [s["rating"] for s in states if s["rating"] >= 4]
    result = []
    for i in range(low):
        if i < target:
            cls = "ambiguous_specific_wording" if scenario == "context_trap_burst" else (
                ("wrong_item_concern" if i % 2 else "mismatch_concern") if scenario == "mismatch_surge"
                else "authenticity_concern")
        else:
            cls = "generic_dissatisfaction" if low == 36 or (scenario == "sparse_history" and phase == "recent") else "other_negative"
        result.append({"rating": rng.choice(low_ratings), "text_class": cls})
    result.extend({"rating": 3, "text_class": "neutral"} for _ in range(neutral))
    result.extend({"rating": rng.choice(high_ratings), "text_class": "positive"} for _ in range(high))
    return result


def generate(seed, copies, states, patterns, profiles):
    rng = random.Random(seed)
    rows = []
    listing_number = 0
    for scenario in SCENARIOS:
        for _ in range(copies):
            listing_number += 1
            profile = rng.choice(profiles)
            asin = f"SYNTH_IPA_{listing_number:04d}"
            for phase in ["previous", "recent"]:
                phase_states = controlled_states(scenario, phase, rng, states)
                for i, state in enumerate(phase_states):
                    cls = state["text_class"]
                    template_idx = i % len(TEMPLATES[cls])
                    lead = rng.choice(LEADS)
                    base = TEMPLATES[cls][template_idx]
                    if lead and not base.startswith("I "):
                        base = base[0].lower() + base[1:]
                    text = lead + base + rng.choice(ENDS)
                    reviewer = f"{asin}_USER_{phase}_{i:03d}"
                    template_family = cls
                    if scenario == "copied_complaint_burst" and phase == "recent" and cls == "authenticity_concern":
                        text = TEMPLATES["authenticity_concern"][0]
                        reviewer = f"{asin}_COPIED_ACCOUNT"
                        template_family = "copied_authenticity_text"
                    offset = rng.randrange(90) + (90 if phase == "previous" else 0)
                    if phase == "recent" and i == 0:
                        offset = 0  # make the declared historical endpoint observable
                    row = {"asin": asin, "name": f"Synthetic product profile {listing_number:04d}",
                        "date": (profile["cutoff"] - timedelta(days=offset)).isoformat(),
                        "rating": state["rating"], "review": text,
                        "source_dataset": "real_informed_indian_products_simulation_v1", "is_synthetic": 1,
                        "review_record_id": f"{asin}_{phase}_{i:03d}",
                        "synthetic_scenario": scenario, "synthetic_phase": phase,
                        "synthetic_reviewer_id": reviewer, "synthetic_template_family": template_family,
                        "synthetic_intended_text_class": cls,
                        "synthetic_reference_asin": profile["reference_asin"],
                        "synthetic_reference_collection_family": profile["family"],
                        "synthetic_dataset_cutoff": profile["cutoff"].isoformat(),
                        "synthetic_seed": seed, "synthetic_generation_method": "seeded_state_resampling_and_controlled_templates_v1",
                        "fraud_ground_truth": ""}
                    row.update(screen(row, patterns))
                    rows.append(row)
    return sorted(rows, key=lambda r: (r["asin"], r["date"], r["review_record_id"]))


def measures(rows):
    n = len(rows)
    low = sum(float(r["rating"]) <= 2 for r in rows)
    high = sum(float(r["rating"]) >= 4 for r in rows)
    specific = [r for r in rows if r["screen_specific_wording"]]
    constructed = [r for r in rows if float(r["rating"]) <= 2 and r["synthetic_intended_text_class"] in
                   {"authenticity_concern", "mismatch_concern", "wrong_item_concern"}]
    return {"n": n, "low": low, "neutral": n-low-high, "high": high,
        "polar_n": low+high, "bounded_low_share": low/(low+high) if low+high else None,
        "specific_wording_n": len(specific), "specific_wording_share": len(specific)/n if n else None,
        "distinct_specific_texts": len({norm(r["review"]) for r in specific}),
        "distinct_specific_synthetic_users": len({r["synthetic_reviewer_id"] for r in specific}),
        "constructed_relevant_low_star_n": len(constructed)}


def evaluate(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r["asin"]].append(r)
    checks = []
    for asin, listing in groups.items():
        cutoff = max(date.fromisoformat(r["date"]) for r in listing)
        recent = [r for r in listing if cutoff-timedelta(days=90) < date.fromisoformat(r["date"]) <= cutoff]
        previous = [r for r in listing if cutoff-timedelta(days=180) < date.fromisoformat(r["date"]) <= cutoff-timedelta(days=90)]
        all_m, now, before = measures(listing), measures(recent), measures(previous)
        enough = now["n"] >= 10 and before["n"] >= 10
        delta = 100*(now["specific_wording_share"]-before["specific_wording_share"]) if enough else None
        record = {"asin": asin, "scenario": listing[0]["synthetic_scenario"], "dataset_cutoff": cutoff.isoformat(),
            **{f"overall_{k}": v for k,v in all_m.items()},
            **{f"recent_{k}": v for k,v in now.items()}, **{f"previous_{k}": v for k,v in before.items()},
            "ratio_count_gate_met": all_m["polar_n"] >= 20,
            "temporal_count_gate_met": enough,
            "specific_wording_change_pp": delta,
            "wording_increase_with_repetition": (delta > 0 and now["distinct_specific_texts"] >= 2) if enough else None,
            "fraud_ground_truth": ""}
        for threshold in [20,25,30]:
            record[f"negative_concentration_at_{threshold}pct"] = (all_m["bounded_low_share"] >= threshold/100) if all_m["polar_n"] >= 20 else None
        checks.append(record)
    return checks


def validate(rows, checks, calibration, real_rows, copies):
    assert len(rows) == copies*(9*120+12)
    assert len({r["review_record_id"] for r in rows}) == len(rows)
    assert len({r["asin"] for r in rows}) == copies*len(SCENARIOS)
    assert not ({r["asin"] for r in rows} & {r["asin"] for r in real_rows})
    assert all(r["is_synthetic"] == 1 and not r["fraud_ground_truth"] for r in rows)
    assert all(calibration["date_min"] <= r["date"] <= calibration["date_max"] for r in rows)
    for c in checks:
        s = c["scenario"]
        if s == "sparse_history":
            assert not c["temporal_count_gate_met"] and c["specific_wording_change_pp"] is None
            assert c["negative_concentration_at_25pct"] is None
        else:
            assert c["recent_n"] == c["previous_n"] == 60
        if s == "generic_quality_surge":
            assert c["negative_concentration_at_25pct"] and c["overall_specific_wording_n"] == 0
        if s in {"authenticity_surge", "mismatch_surge"}:
            assert c["wording_increase_with_repetition"] and c["negative_concentration_at_25pct"]
        if s == "isolated_concern":
            assert c["overall_specific_wording_n"] == 1 and not c["negative_concentration_at_25pct"]
        if s == "historical_recovery":
            assert c["specific_wording_change_pp"] < 0
        if s == "copied_complaint_burst":
            assert c["recent_specific_wording_n"] == 24
            assert c["recent_distinct_specific_texts"] == c["recent_distinct_specific_synthetic_users"] == 1
            assert not c["wording_increase_with_repetition"]
        if s == "context_trap_burst":
            assert c["wording_increase_with_repetition"] and c["overall_constructed_relevant_low_star_n"] == 0


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", restval="")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=4025)
    parser.add_argument("--listings-per-scenario", type=int, default=10)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DEST)
    args = parser.parse_args()
    if args.listings_per_scenario < 1:
        parser.error("--listings-per-scenario must be positive")
    inputs = [RAW, PREPARED, CONTEXT, RULE_FILE, CHECKPOINT, Path(__file__).resolve()]
    before_hashes = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    real, states, patterns, profiles, calibration = load_inputs()
    synthetic = generate(args.seed, args.listings_per_scenario, states, patterns, profiles)
    assert synthetic == generate(args.seed, args.listings_per_scenario, states, patterns, profiles), "Seed reproducibility failed"
    checks = evaluate(synthetic)
    validate(synthetic, checks, calibration, real, args.listings_per_scenario)
    with PREPARED.open(encoding="utf-8-sig", newline="") as f:
        original_records = [{k: r[k] for k in ORIGINAL} for r in csv.DictReader(f) if r["review"].strip()]
    real_export = []
    for r, loaded in zip(original_records, real):
        assert r["asin"] == loaded["asin"] and r["review"] == loaded["text"]
        enriched = {**r, "source_dataset": "nehaprabhavalkar/indian-products-on-amazon",
                    "is_synthetic": 0, "review_record_id": loaded["record_id"], "fraud_ground_truth": ""}
        enriched.update(screen(enriched, patterns))
        real_export.append(enriched)
    assert len(real_export) == len(real) == len(original_records)
    assert all({k:r[k] for k in ORIGINAL} == o for r,o in zip(real_export, original_records))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir/"reviews_synthetic.csv", synthetic, ORIGINAL+EXTRA)
    write_csv(args.output_dir/"reviews_real_and_synthetic.csv", real_export+synthetic, ORIGINAL+EXTRA)
    write_csv(args.output_dir/"listing_window_checks.csv", checks, list(checks[0]))
    baseline = [r for r in synthetic if r["synthetic_scenario"] == "empirical_reference"]
    synthetic_counts = Counter(int(r["rating"]) for r in baseline)
    comparison = [{"stars": star, "real_count": calibration["star_counts"][star],
        "real_share": calibration["star_counts"][star]/len(real),
        "empirical_reference_count": synthetic_counts[star],
        "empirical_reference_share": synthetic_counts[star]/len(baseline),
        "difference_pp": 100*(synthetic_counts[star]/len(baseline)-calibration["star_counts"][star]/len(real))}
        for star in range(1,6)]
    pattern_comparison = []
    for field in ["screen_low_star", "screen_any_wording", "screen_specific_wording"]:
        real_count = sum(r[field] for r in real_export)
        simulated_count = sum(r[field] for r in baseline)
        pattern_comparison.append({"metric": field, "real_count": real_count,
            "real_denominator": len(real_export), "real_share": real_count/len(real_export),
            "reference_count": simulated_count, "reference_denominator": len(baseline),
            "reference_share": simulated_count/len(baseline),
            "difference_pp": 100*(simulated_count/len(baseline)-real_count/len(real_export))})
    summary = {"generator_version": "1.0", "seed": args.seed, "primary_calibration": calibration,
        "scenario_count": len(SCENARIOS), "listings_per_scenario": args.listings_per_scenario,
        "synthetic_listings": len(checks), "synthetic_reviews": len(synthetic),
        "real_reviews_in_combined_export": len(real_export), "combined_review_records": len(real_export)+len(synthetic),
        "calibration_comparison_reference_scenario_only": comparison,
        "calibration_comparison_reference_patterns": pattern_comparison,
        "empirical_reference_rating_text_joint_counts": dict(Counter(
            f"{r['rating']}|{r['synthetic_intended_text_class']}" for r in baseline)),
        "assumptions": {"dense_reviews_per_phase": 60, "sparse_reviews_per_phase": 6,
            "window_days": 90, "stable_low_neutral_high_per_phase": [6,4,50],
            "surge_low_neutral_high_per_phase": [36,4,20], "surge_specific_texts": 24,
            "ratio_share_thresholds": [0.20,0.25,0.30], "ratio_min_non_neutral": 20, "temporal_min_per_window": 10,
            "temporal_increase_rule": "Direction-only descriptive check: specific-wording share rises and at least two distinct texts occur recently; no significance or validated magnitude threshold.",
            "date_sampling": "Uniform days within two historical windows; source-derived endpoint. Does not preserve observed seasonality, spacing or review volume.",
            "scenario_allocation": "Equal counts for software coverage, not estimated real prevalence.",
            "text_generation": "Finite templates with prefix/suffix variation; not a natural-language training corpus.",
            "reference_asin": "Historical endpoint/profile provenance only; synthetic experience is never attributed to that real product."},
        "validation": {"same_seed_reproduces_rows": True, "source_columns_preserved_in_real_rows": True,
            "all_dates_within_primary_source_range": True, "synthetic_real_ids_disjoint": True,
            "scenario_invariants_passed": True, "confirmed_fraud_labels_generated": False,
            "uses_constructed_labels_as_rule_inputs": False,
            "interpretation": "Passing checks demonstrates generator and prototype mechanics only, not real-world scam detection accuracy."},
        "scenario_checks": {scenario: {"listings": sum(c["scenario"] == scenario for c in checks),
            "reviews": sum(c["overall_n"] for c in checks if c["scenario"] == scenario),
            "ratio_25pct_flags": sum(c["negative_concentration_at_25pct"] is True for c in checks if c["scenario"] == scenario),
            "wording_increase_flags": sum(c["wording_increase_with_repetition"] is True for c in checks if c["scenario"] == scenario)} for scenario in SCENARIOS}}
    (args.output_dir/"calibration_and_validation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for p in inputs:
        assert sha(p) == before_hashes[str(p.relative_to(ROOT))], f"Input was changed: {p}"
    assert sha(CHECKPOINT) == "c8e8de906dce0d944430162dbaf47c35a7a434e1e3cb10c6cd8cda6f99fbb52c"
    produced = [args.output_dir/name for name in ["reviews_synthetic.csv", "reviews_real_and_synthetic.csv",
                "listing_window_checks.csv", "calibration_and_validation.json"]]
    manifest = {"primary_source": calibration["primary_source"], "seed": args.seed,
        "input_sha256": before_hashes, "output_sha256": {p.name: sha(p) for p in produced},
        "original_sources_and_checkpoint_unchanged": True,
        "do_not_pool_for_empirical_estimates": "Filter is_synthetic=0 for observed-data results. Synthetic scenario rates are designed, not estimated."}
    (args.output_dir/"manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k:summary[k] for k in ["seed", "synthetic_listings", "synthetic_reviews", "real_reviews_in_combined_export", "combined_review_records"]}, indent=2))
    print(json.dumps(summary["scenario_checks"], indent=2))
    print("Validation passed; real sources and frozen checkpoint unchanged.")


if __name__ == "__main__":
    main()
