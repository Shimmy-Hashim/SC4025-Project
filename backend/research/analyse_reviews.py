"""Reproduce the exploratory audit; flags identify wording, never fraud ground truth.

Run from the project root: python -X utf8 research/analyse_reviews.py
Dependencies: pandas, numpy. Original downloaded files are never overwritten.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
PATTERNS = {
    "scam_word_flag": r"\bscam(?:s|med|mer|mers|ming)?\b",
    "general_deception_flag": r"\b(?:scam(?:s|med|mer|mers|ming)?|fraud(?:ulent)?|cheat(?:ed|ing|s)?)\b",
    "counterfeit_term_flag": r"\b(?:counterfeits?|fake|duplicates?|knock[ -]?offs?|not\s+(?:an?\s+)?(?:original|genuine)|non[ -]?genuine)\b",
    "wrong_product_phrase_flag": (
        r"\bwrong\s+(?:item|product|model|size|colou?r|variant|brand)\b"
        r"|\b(?:received|delivered|sent)\s+(?:(?:a|the|completely|totally)\s+){0,3}different\s+(?:item|product|model|size|colou?r|variant|brand)\b"
        r"|\bnot\s+what\s+i\s+(?:had\s+)?ordered\b"
    ),
    "not_as_advertised_phrase_flag": (
        r"\bnot\s+as\s+(?:advertised|described|shown|pictured)\b"
        r"|\b(?:does\s+not|doesn't|did\s+not|didn't)\s+match\s+(?:the\s+)?(?:description|picture|image|advertisement)\b"
        r"|\b(?:misleading|false)\s+(?:description|advertis(?:ement|ing)|claims?)\b"
    ),
}
COMPILED = {k: re.compile(v, re.I) for k, v in PATTERNS.items()}


def normalise(value: object) -> str:
    return re.sub(r"\s+", " ", str(value)).strip().casefold() if pd.notna(value) else ""


def annotate(frame: pd.DataFrame, text_col: str, source_name: str) -> pd.DataFrame:
    result = frame.copy()
    texts = result[text_col].fillna("").astype(str)
    for name, pattern in COMPILED.items():
        result[name] = texts.map(lambda s: bool(pattern.search(s))).astype(int)
    flag_cols = list(PATTERNS)
    result["any_complaint_rule_flag"] = result[flag_cols].any(axis=1).astype(int)
    result["matched_terms"] = texts.map(lambda s: " | ".join(sorted({
        m.group(0).casefold() for pattern in COMPILED.values() for m in pattern.finditer(s)
    })))
    result["review_text_missing"] = texts.str.strip().eq("").astype(int)
    result["review_text_char_count"] = texts.str.len()
    result["text_group_id"] = texts.map(lambda s: hashlib.sha256(normalise(s).encode()).hexdigest()[:20])
    result["label_source"] = "unvalidated_keyword_rules_v1"
    result["source_dataset"] = source_name
    result["is_synthetic"] = 0
    result["human_complaint_label"] = ""
    result["fraud_ground_truth"] = ""
    return result


def number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(r"[^0-9.\-]", "", regex=True), errors="coerce")


def groups(frame: pd.DataFrame, flag: str, variables: list[str], dataset: str) -> list[dict]:
    rows = []
    for state in [0, 1]:
        part = frame.loc[frame[flag].eq(state)]
        for variable in variables:
            values = pd.to_numeric(part[variable], errors="coerce").dropna()
            rows.append({"dataset": dataset, "flag": flag, "flag_value": state,
                         "variable": variable, "group_records": len(part), "valid_values": len(values),
                         "mean": float(values.mean()) if len(values) else None,
                         "median": float(values.median()) if len(values) else None})
    return rows


def main() -> None:
    OUT.mkdir(exist_ok=True)
    main_raw = pd.read_csv(ROOT / "data/amazon-sales-dataset/amazon.csv")
    india_raw = pd.read_csv(ROOT / "data/indian-products-on-amazon/amazon_vfl_reviews.csv")
    # Preserve source order and every original value/column in the full augmented dataset.
    main_full = annotate(main_raw, "review_content", "karkavelrajaj/amazon-sales-dataset")
    main_full.insert(0, "source_row", np.arange(1, len(main_full) + 1))
    for col in ["discounted_price", "actual_price", "discount_percentage", "rating", "rating_count"]:
        main_full[col + "_numeric"] = number(main_full[col])
    main_full["top_category"] = main_full["category"].str.split("|").str[0]
    main_full["duplicate_product_id"] = main_full.duplicated("product_id", keep=False).astype(int)
    main_unique = main_full.drop_duplicates("product_id", keep="first").copy()

    # Exact duplicate records only: repeated generic text across different products is not removed.
    india_unique = india_raw.drop_duplicates(keep="first").copy()
    india = annotate(india_unique, "review", "nehaprabhavalkar/indian-products-on-amazon")
    india["review_rating_numeric"] = pd.to_numeric(india["rating"], errors="coerce")
    india["review_year"] = pd.to_datetime(india["date"], errors="coerce").dt.year
    india["review_record_id"] = india.apply(lambda r: hashlib.sha256(
        "\x1f".join(str(r[c]) for c in ["asin", "date", "rating", "review"]).encode()
    ).hexdigest()[:20], axis=1)

    # A missing review is not a negative; flag=0 means only "rule did not fire".
    india_valid = india.loc[india.review_text_missing.eq(0)].copy()
    counts = []
    for name, frame in [("main_unique_products", main_unique), ("india_unique_nonempty_reviews", india_valid)]:
        for flag in [*PATTERNS, "any_complaint_rule_flag"]:
            counts.append({"dataset": name, "indicator": flag, "positive_records": int(frame[flag].sum()),
                           "total_records": len(frame), "sample_fraction": float(frame[flag].mean())})
    associations = []
    for flag in ["scam_word_flag", "counterfeit_term_flag", "any_complaint_rule_flag"]:
        associations += groups(main_unique, flag, ["rating_numeric", "discounted_price_numeric",
            "discount_percentage_numeric", "rating_count_numeric", "review_text_char_count"], "main_unique_products")
        associations += groups(india_valid, flag, ["review_rating_numeric", "review_text_char_count"], "india_unique_nonempty_reviews")

    lowstar = []
    for flag in ["scam_word_flag", "counterfeit_term_flag", "any_complaint_rule_flag"]:
        for state in [0, 1]:
            part = india_valid.loc[india_valid[flag].eq(state)]
            lowstar.append({"indicator": flag, "flag_value": state, "reviews": len(part),
                            "one_or_two_star_reviews": int(part.review_rating_numeric.le(2).sum()),
                            "one_or_two_star_fraction": float(part.review_rating_numeric.le(2).mean()) if len(part) else None})

    category_rows = []
    for category, part in main_unique.groupby("top_category", sort=True):
        category_rows.append({"category": category, "products": len(part),
                              "candidate_products": int(part.any_complaint_rule_flag.sum()),
                              "candidate_fraction": float(part.any_complaint_rule_flag.mean())})

    # Review queue: all candidates plus 100 deterministic sampled non-candidates per source.
    queue = []
    for frame, key, col, ds in [(main_unique, "product_id", "review_content", "main"),
                                (india_valid, "review_record_id", "review", "india")]:
        selected = pd.concat([frame.loc[frame.any_complaint_rule_flag.eq(1)],
                              frame.loc[frame.any_complaint_rule_flag.eq(0)].sample(
                                  n=min(100, int(frame.any_complaint_rule_flag.eq(0).sum())), random_state=4025)])
        for _, row in selected.iterrows():
            queue.append({"source_dataset": ds, "record_id": row[key],
                          "product_id": row.get("product_id", row.get("asin")),
                          "text_group_id": row["text_group_id"], "review_text": row[col],
                          "rule_candidate": row.any_complaint_rule_flag, "matched_terms": row.matched_terms,
                          "annotator_1_label": "", "annotator_2_label": "", "adjudicated_label": "",
                          "adjudicated_evidence": "", "notes": ""})

    # Descriptive sensitivity only: repeated concatenated text may occur across ASINs.
    unique_blobs = main_unique.drop_duplicates("text_group_id")
    india_unique_text = india_valid.drop_duplicates("text_group_id")
    summary = {
        "analysis_date": "2026-10-31",
        "main": {"raw_rows": len(main_raw), "raw_columns": len(main_raw.columns),
                 "unique_product_ids": int(main_raw.product_id.nunique()),
                 "extra_rows_with_repeated_product_id": int(main_raw.product_id.duplicated().sum()),
                 "unique_review_blobs_in_product_sample": len(unique_blobs),
                 "candidate_unique_review_blobs": int(unique_blobs.any_complaint_rule_flag.sum()),
                 "missing_numeric_rating": int(main_unique.rating_numeric.isna().sum()),
                 "missing_numeric_rating_count": int(main_unique.rating_count_numeric.isna().sum()),
                 "source_scope": "product listings, with concatenated review blobs; no individual review ratings/dates or seller IDs"},
        "india": {"raw_rows": len(india_raw), "raw_columns": len(india_raw.columns),
                  "exact_duplicates_removed": len(india_raw) - len(india_unique),
                  "deduplicated_rows": len(india), "nonempty_review_rows": len(india_valid),
                  "missing_review_rows": int(india.review_text_missing.sum()),
                  "unique_product_ids": int(india.asin.nunique()),
                  "earliest_date": str(india.date.min()), "latest_date": str(india.date.max()),
                  "star_counts_nonempty": {str(k): int(v) for k,v in india_valid.rating.value_counts().sort_index().items()}},
        "identical_text_sensitivity": {
            "main_unique_texts": len(unique_blobs),
            "main_candidate_texts": int(unique_blobs.any_complaint_rule_flag.sum()),
            "india_unique_texts": len(india_unique_text),
            "india_candidate_texts": int(india_unique_text.any_complaint_rule_flag.sum()),
            "india_counterfeit_term_texts": int(india_unique_text.counterfeit_term_flag.sum()),
            "india_low_star_fraction_with_counterfeit_terms": float(india_unique_text.loc[
                india_unique_text.counterfeit_term_flag.eq(1), "review_rating_numeric"].le(2).mean()),
            "india_low_star_fraction_without_counterfeit_terms": float(india_unique_text.loc[
                india_unique_text.counterfeit_term_flag.eq(0), "review_rating_numeric"].le(2).mean()),
            "note": "Sensitivity only; identical generic wording can also occur in independent legitimate reviews."
        },
        "exact_product_id_overlap": len(set(main_raw.product_id) & set(india_raw.asin)),
        "label_definition": "Unvalidated wording flags. No rule match is not evidence of authenticity. No measured fraud probability.",
        "keyword_counts": counts,
        "low_star_associations": lowstar,
        "descriptive_associations": associations,
        "category_associations": category_rows,
        "rule_patterns": PATTERNS,
    }
    main_full.to_csv(OUT / "amazon_india_augmented.csv", index=False, encoding="utf-8-sig")
    india.to_csv(OUT / "indian_reviews_deduplicated_flagged.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(queue).to_csv(OUT / "manual_annotation_queue.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(counts).to_csv(OUT / "keyword_counts.csv", index=False)
    pd.DataFrame(associations).to_csv(OUT / "variable_associations.csv", index=False)
    (OUT / "analysis_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False), encoding="utf-8")

    # Material checks: preservation, exact duplication, absence of invented labels, overlap.
    exported = pd.read_csv(OUT / "amazon_india_augmented.csv", keep_default_na=False)
    pd.testing.assert_frame_equal(exported[list(main_raw.columns)].astype(str), main_raw.fillna("").astype(str))
    assert len(main_full) == len(main_raw)
    assert len(india) == len(india_raw.drop_duplicates())
    assert main_full.fraud_ground_truth.eq("").all() and india.fraud_ground_truth.eq("").all()
    assert main_full.is_synthetic.eq(0).all() and india.is_synthetic.eq(0).all()
    assert len(set(main_raw.product_id) & set(india_raw.asin)) == summary["exact_product_id_overlap"]
    print(json.dumps({k: v for k,v in summary.items() if k not in ["descriptive_associations", "rule_patterns"]}, indent=2))
    print("Validation passed: original columns preserved; deduplication reconciled; no invented fraud labels.")


if __name__ == "__main__":
    main()
