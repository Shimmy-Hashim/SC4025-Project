"""Explore the proposed 1-2-star filter plus review-wording screen.

Only individual review stars are used. India's aggregate listing rating cannot
substitute for an individual review rating. All text flags remain unvalidated.
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE_RULES = json.loads((ROOT / "outputs/analysis_summary.json").read_text())["rule_patterns"]
RULES = {
    "waste_of_money": r"\bwaste\s+of\s+(?:my\s+)?money\b",
    "not_good": r"\b(?:not\s+(?:at\s+all\s+)?good|no\s+good)\b",
    "poor_or_bad_quality": r"\b(?:poor|bad|low)\s+quality\b",
    "fake_word": r"\bfake\b",
    "counterfeit_wording": BASE_RULES["counterfeit_term_flag"],
    "wrong_product_wording": BASE_RULES["wrong_product_phrase_flag"],
    "not_as_advertised_wording": BASE_RULES["not_as_advertised_phrase_flag"],
    "deception_wording": BASE_RULES["general_deception_flag"],
}
COMPILED = {name: re.compile(pattern, re.I) for name, pattern in RULES.items()}


def summarise(records):
    valid = [r for r in records if str(r["text"]).strip()]
    low = [r for r in valid if 1 <= float(r["rating"]) <= 2]
    counts = {name: 0 for name in RULES}
    categories = {"counterfeit_wording_only":0, "mismatch_wording_only":0,
        "both_counterfeit_and_mismatch_wording":0,
        "general_dissatisfaction_or_deception_wording_only":0, "no_selected_keyword":0}
    specific_total = specific_low = any_selected_low = 0
    for row in valid:
        text = str(row["text"])
        flags = {name: bool(pattern.search(text)) for name, pattern in COMPILED.items()}
        authenticity = flags["counterfeit_wording"]
        mismatch = flags["wrong_product_wording"] or flags["not_as_advertised_wording"]
        specific_total += int(authenticity or mismatch)
        if not 1 <= float(row["rating"]) <= 2:
            continue
        for name, value in flags.items():
            counts[name] += int(value)
        specific_low += int(authenticity or mismatch)
        any_selected_low += int(any(flags.values()))
        if authenticity and mismatch:
            category = "both_counterfeit_and_mismatch_wording"
        elif authenticity:
            category = "counterfeit_wording_only"
        elif mismatch:
            category = "mismatch_wording_only"
        elif any(flags.values()):
            category = "general_dissatisfaction_or_deception_wording_only"
        else:
            category = "no_selected_keyword"
        categories[category] += 1
    assert sum(categories.values()) == len(low)
    return {"nonempty_reviews":len(valid), "one_or_two_star_reviews":len(low),
        "low_star_keyword_counts":counts,
        "low_star_review_categories":categories,
        "low_star_with_any_selected_wording":any_selected_low,
        "low_star_with_authenticity_or_mismatch_wording":specific_low,
        "all_star_authenticity_or_mismatch_wording":specific_total,
        "above_two_star_authenticity_or_mismatch_wording":specific_total-specific_low,
        "interpretation":"Counts describe regex wording, not confirmed complaints, counterfeits or model accuracy."}


def main():
    general, seen = [], set()
    for category in ["Electronics", "Cell_Phones_and_Accessories"]:
        with (ROOT / "data/amazon-reviews-2023-sample" / (category+"_first20000.jsonl")).open(encoding="utf-8") as source:
            for line in source:
                row = json.loads(line)
                key = tuple(row[k] for k in ["asin","user_id","timestamp","text","rating"])
                if key not in seen:
                    seen.add(key)
                    general.append({"rating":row["rating"],"text":row["text"]})
    supplemental, seen = [], set()
    # Reuse the audited preparation, including its missing-text normalization.
    with (ROOT / "outputs/indian_reviews_deduplicated_flagged.csv").open(encoding="utf-8-sig",newline="") as source:
        for row in csv.DictReader(source):
            key = tuple(row[k] for k in ["asin","name","date","rating","review"])
            if key not in seen:
                seen.add(key)
                supplemental.append({"rating":row["rating"],"text":row["review"]})
    result = {"analysis_date":"2026-10-31", "proposed_rule":"Individual review rating in {1,2}, followed by context-aware review-text screening",
        "general_amazon":summarise(general), "indian_products_supplement":summarise(supplemental),
        "main_amazon_india_dataset":"Cannot apply the star gate to individual reviews: rating is a listing aggregate and review text is combined.",
        "synthetic_data":"No synthetic observations or outcome labels generated.", "patterns":RULES}
    assert result["general_amazon"]["nonempty_reviews"] == 39986
    assert result["general_amazon"]["one_or_two_star_reviews"] == 5071
    assert result["indian_products_supplement"]["nonempty_reviews"] == 1388
    assert result["indian_products_supplement"]["one_or_two_star_reviews"] == 338
    (ROOT / "outputs/low_star_review_analysis.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "patterns"},indent=2))


if __name__ == "__main__":
    main()
