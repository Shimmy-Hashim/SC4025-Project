"""Audit literal scam versus scam-family wording without inventing outcome labels."""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent


def describe(part):
    return {"reviews":len(part), "mean_stars":float(part.rating.mean()),
        "low_star_reviews":int(part.rating.le(2).sum()),
        "low_star_fraction":float(part.rating.le(2).mean()),
        "verified_purchase_fraction":float(part.verified_purchase.mean()),
        "any_helpful_vote_fraction":float(part.helpful_vote.gt(0).mean()),
        "median_body_characters":float(part.text.str.len().median())}


def main():
    records = []
    for category in ["Electronics", "Cell_Phones_and_Accessories"]:
        with (ROOT / "data/amazon-reviews-2023-sample" / (category + "_first20000.jsonl")).open(encoding="utf-8") as source:
            records.extend(json.loads(line) for line in source)
    general = pd.DataFrame(records).drop_duplicates(["asin","user_id","timestamp","text","rating"])
    general = general.loc[general.text.fillna("").str.strip().ne("")].copy()
    patterns = {"literal_scam":r"\bscam\b", "scam_family":r"\bscam(?:s|med|mer|mers|ming)?\b"}
    result = {"definition":"Text mention only; no confirmed fraud or intent labels", "general_amazon":{}}
    for name, pattern in patterns.items():
        mask = general.text.str.contains(pattern, flags=re.I, regex=True)
        result["general_amazon"][name] = {"with_keyword":describe(general.loc[mask]),
                                                       "without_keyword":describe(general.loc[~mask])}
    main = pd.read_csv(ROOT / "outputs/amazon_india_augmented.csv").drop_duplicates("product_id")
    india_hits = main.loc[main.scam_word_flag.eq(1)]
    result["main_india_scam_family_audit"] = {
        "matched_product_ids":len(india_hits),
        "distinct_normalized_review_blobs":int(india_hits.text_group_id.nunique()),
        "context_inspection":"The repeated text's scam reference concerns an installation service, not a counterfeit or wrong-item allegation.",
        "interpretation":"Five product matches are not five independent relevant product-scam examples."}
    result["general_context_inspection"] = {
        "scam_call_mentions":2,
        "interpretation":"Two keyword matches discuss scam telephone calls in call-blocker reviews; the keyword alone is not a complaint about the purchased product."}
    result["synthetic_column_decision"] = "Observed text supports derived keyword indicators. No synthetic fraud outcomes were generated."
    assert result["general_amazon"]["literal_scam"]["with_keyword"]["reviews"] == 8
    assert result["general_amazon"]["scam_family"]["with_keyword"]["reviews"] == 12
    assert len(india_hits) == 5 and india_hits.text_group_id.nunique() == 1
    (ROOT / "outputs/scam_keyword_audit.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
