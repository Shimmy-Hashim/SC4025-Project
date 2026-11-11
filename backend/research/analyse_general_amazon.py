"""Apply the same wording rules to bounded Amazon Reviews'23 samples.

Run from the project root after sample_general_amazon.py. This performs descriptive
analysis only; no classifier or calibrated seller-risk estimate is fitted.
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

from analyse_reviews import PATTERNS, annotate

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
FOLDER = ROOT / "data/amazon-reviews-2023-sample"


def main():
    parts = []
    for category in ["Electronics", "Cell_Phones_and_Accessories"]:
        path = FOLDER / (category + "_first20000.jsonl")
        with path.open(encoding="utf-8") as source:
            part = pd.DataFrame(json.loads(line) for line in source)
        part["source_category"] = category
        part["source_category_row"] = range(1, len(part) + 1)
        parts.append(part)
    raw = pd.concat(parts, ignore_index=True)
    key = ["asin", "user_id", "timestamp", "text", "rating"]
    unique = raw.drop_duplicates(subset=key).copy()
    full = annotate(unique, "text", "McAuley-Lab/Amazon-Reviews-2023; file-order prefixes")
    valid = full.loc[full.review_text_missing.eq(0)].copy()
    valid["review_rating_numeric"] = pd.to_numeric(valid.rating, errors="coerce")
    valid["verified_purchase_numeric"] = valid.verified_purchase.astype(int)
    valid["helpful_vote_numeric"] = pd.to_numeric(valid.helpful_vote, errors="coerce")
    valid["has_helpful_vote"] = valid.helpful_vote_numeric.gt(0).astype(int)
    valid["review_year"] = pd.to_datetime(valid.timestamp, unit="ms", utc=True).dt.year
    valid["review_record_id"] = valid.apply(lambda row: hashlib.sha256(
        "\x1f".join(str(row[c]) for c in key).encode()
    ).hexdigest()[:20], axis=1)
    counts, associations = [], []
    for name, frame in [("pooled_deduplicated", valid), *list(valid.groupby("source_category", sort=True))]:
        for flag in [*PATTERNS, "any_complaint_rule_flag"]:
            counts.append({"sample": name, "indicator": flag, "positive_records": int(frame[flag].sum()),
                "total_records": len(frame), "sample_fraction": float(frame[flag].mean())})
        for flag in ["scam_word_flag", "counterfeit_term_flag", "any_complaint_rule_flag"]:
            for state in [0, 1]:
                part = frame.loc[frame[flag].eq(state)]
                associations.append({"sample": name, "indicator": flag, "flag_value": state,
                    "reviews": len(part), "one_or_two_star_reviews": int(part.review_rating_numeric.le(2).sum()),
                    "one_or_two_star_fraction": float(part.review_rating_numeric.le(2).mean()) if len(part) else None,
                    "mean_rating": float(part.review_rating_numeric.mean()) if len(part) else None,
                    "verified_purchase_fraction": float(part.verified_purchase_numeric.mean()) if len(part) else None,
                    "any_helpful_vote_fraction": float(part.has_helpful_vote.mean()) if len(part) else None,
                    "median_text_characters": float(part.review_text_char_count.median()) if len(part) else None})
    main = pd.read_csv(ROOT / "data/amazon-sales-dataset/amazon.csv")
    ids = set(main.product_id)
    matching_asins = sorted(ids & set(valid.asin))
    matching_parent_asins = sorted(ids & set(valid.parent_asin))
    # Review outcomes are kept separate from India listing outcomes even for shared ASINs.
    overlaps = valid.loc[valid.asin.isin(matching_asins)].groupby("asin").agg(
        sampled_reviews=("asin", "size"), wording_candidates=("any_complaint_rule_flag", "sum"),
        mean_sampled_review_rating=("review_rating_numeric", "mean"))
    overlaps = overlaps.reset_index()
    india_listing = pd.read_csv(OUT / "amazon_india_augmented.csv").drop_duplicates("product_id")
    listing_fields = ["product_id", "product_name", "top_category", "discounted_price_numeric",
        "discount_percentage_numeric", "rating_numeric", "rating_count_numeric"]
    listing_for_join = india_listing[listing_fields].rename(columns={
        c: ("asin" if c == "product_id" else "india_listing_" + c) for c in listing_fields})
    general_fields = ["asin", "parent_asin", "source_category", "source_category_row", "review_record_id",
        "timestamp", "review_rating_numeric", "verified_purchase", "helpful_vote", "text", "any_complaint_rule_flag"]
    general_for_join = valid[general_fields].rename(columns={
        c: (c if c == "asin" else "general_review_" + c) for c in general_fields})
    joined = general_for_join.merge(listing_for_join, on="asin", how="inner", validate="many_to_one")
    joined["link_limit"] = "Exact ASIN identity only; marketplace, seller and observation context differ or are unverified"
    sensitivity = valid.drop_duplicates("text_group_id")
    sensitivity_rows = []
    for state in [0, 1]:
        part = sensitivity.loc[sensitivity.counterfeit_term_flag.eq(state)]
        sensitivity_rows.append({"counterfeit_term_flag": state, "texts": len(part),
            "low_star_texts": int(part.review_rating_numeric.le(2).sum()),
            "low_star_fraction": float(part.review_rating_numeric.le(2).mean()) if len(part) else None})
    summary = {"analysis_date":"2026-10-31", "raw_sample_records":len(raw),
        "deduplicated_records":len(unique), "duplicate_records_removed":len(raw)-len(unique),
        "nonempty_review_records":len(valid), "empty_review_records":len(unique)-len(valid),
        "unique_reviewed_asins":int(valid.asin.nunique()),
        "first_review_date":str(pd.to_datetime(valid.timestamp,unit="ms",utc=True).min()),
        "last_review_date":str(pd.to_datetime(valid.timestamp,unit="ms",utc=True).max()),
        "sampling":"first 20000 records from each of Electronics and Cell_Phones_and_Accessories; convenience prefixes, not random or representative",
        "main_exact_asin_overlap_count":len(matching_asins), "main_exact_asin_overlap":matching_asins,
        "main_exact_asin_join_review_rows":len(joined),
        "main_exact_asin_join_candidate_reviews":int(joined.general_review_any_complaint_rule_flag.sum()),
        "main_parent_asin_overlap_count":len(matching_parent_asins),
        "main_parent_asin_overlap":matching_parent_asins,
        "keyword_counts":counts, "associations":associations,
        "unique_text_sensitivity":sensitivity_rows,
        "limitations":"Unvalidated wording flags; no India marketplace indicator, order-level seller ID or authenticated fraud outcome. No probability model."}
    pd.DataFrame(counts).to_csv(OUT / "general_amazon_keyword_counts.csv",index=False)
    pd.DataFrame(associations).to_csv(OUT / "general_amazon_associations.csv",index=False)
    overlaps.to_csv(OUT / "general_amazon_exact_asin_overlap.csv",index=False)
    joined.to_csv(OUT / "general_amazon_india_asin_join.csv",index=False,encoding="utf-8-sig")
    candidate_cols = ["source_category","source_category_row","review_record_id","asin","parent_asin",
        "timestamp","review_rating_numeric","verified_purchase","helpful_vote","text",
        *list(PATTERNS),"any_complaint_rule_flag","matched_terms","text_group_id","label_source",
        "is_synthetic","human_complaint_label","fraud_ground_truth"]
    candidates = valid.loc[valid.any_complaint_rule_flag.eq(1),candidate_cols]
    candidates.to_csv(OUT / "general_amazon_candidate_reviews.csv",index=False,encoding="utf-8-sig")
    (OUT / "general_amazon_summary.json").write_text(json.dumps(summary,indent=2,allow_nan=False),encoding="utf-8")
    assert len(raw)==40_000 and not unique.duplicated(key).any()
    assert candidates.fraud_ground_truth.eq("").all() and candidates.is_synthetic.eq(0).all()
    assert len(valid)+int(full.review_text_missing.sum())==len(unique)
    assert joined.asin.nunique()==len(matching_asins)
    print(json.dumps({k:v for k,v in summary.items() if k not in ["keyword_counts","associations"]},indent=2))
    print(pd.DataFrame(counts).query("sample == 'pooled_deduplicated'").to_string(index=False))
    print(pd.DataFrame(associations).query("sample == 'pooled_deduplicated'").to_string(index=False))
    print("General sample validation passed.")


if __name__ == "__main__":
    main()
