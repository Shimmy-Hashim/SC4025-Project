"""Descriptive ratio and dataset-relative dated-window audit.

Threshold values are explicit prototype hypotheses, not validated classifiers.
The existing historical checkpoint and original observations are not modified.
"""
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"outputs"
RECORDED_ON=date(2026,10,31)
WINDOW_DAYS=90
TRIAL_THRESHOLD=0.25
MIN_POLAR_REVIEWS=20
MIN_REVIEWS_PER_TIME_WINDOW=10


def review_date(row):
    value=row["date_or_timestamp"]
    if isinstance(value,(int,float)):
        return datetime.fromtimestamp(value/1000,timezone.utc).date()
    return date.fromisoformat(value[:10])


def metrics(reviews,annotations):
    low=sum(1<=r["stars"]<=2 for r in reviews)
    high=sum(4<=r["stars"]<=5 for r in reviews)
    target=[r for r in reviews if annotations.get(r["record_id"],{}).get("target_relevant_allegation",False)]
    texts={" ".join(r["text"].strip().casefold().split()) for r in target}
    known_reviewers={r["reviewer_id"] for r in reviews if r["reviewer_id"]}
    relevant_reviewers={r["reviewer_id"] for r in target if r["reviewer_id"]}
    polar=low+high
    return {"sampled_reviews":len(reviews),"low_1_2":low,"neutral_3":sum(r["stars"]==3 for r in reviews),
        "high_4_5":high,"polar_reviews":polar,"low_to_high_ratio":low/high if high else None,
        "low_to_high_ratio_note":"No high-star reviews; ratio undefined" if not high else None,
        "low_share_of_polar_reviews":low/polar if polar else None,
        "low_share_of_all_reviews":low/len(reviews) if reviews else None,
        "context_relevant_low_star_allegations":len(target),"distinct_relevant_texts":len(texts),
        "distinct_known_reviewer_ids":len(known_reviewers) if known_reviewers else None,
        "distinct_relevant_known_reviewer_ids":len(relevant_reviewers) if known_reviewers else None,
        "relevant_reviews_without_reviewer_id":sum(not r["reviewer_id"] for r in target),
        "target_allegation_share_of_sampled_reviews":len(target)/len(reviews) if reviews else None}


def windows(reviews,anchor,annotations):
    recent=[r for r in reviews if anchor-timedelta(days=WINDOW_DAYS)<review_date(r)<=anchor]
    previous=[r for r in reviews if anchor-timedelta(days=2*WINDOW_DAYS)<review_date(r)<=anchor-timedelta(days=WINDOW_DAYS)]
    now=metrics(recent,annotations)
    before=metrics(previous,annotations)
    enough=now["sampled_reviews"]>=MIN_REVIEWS_PER_TIME_WINDOW and before["sampled_reviews"]>=MIN_REVIEWS_PER_TIME_WINDOW
    return {"dataset_cutoff":anchor.isoformat(),"window_days":WINDOW_DAYS,"recent":now,"previous":before,
        "sample_count_gate_met":enough,
        "interpretation":"Sample counts meet the trial gate; sampling and outcome validity still require checking" if enough else "Insufficient sampled reviews for a meaningful window comparison",
        "recent_repeated_allegations_observed":now["distinct_relevant_texts"]>=2,
        "new_repeated_allegation_indicator":(now["distinct_relevant_texts"]>=2 and before["context_relevant_low_star_allegations"]==0) if enough else None,
        "low_share_change_pp":100*(now["low_share_of_polar_reviews"]-before["low_share_of_polar_reviews"]) if enough and now["polar_reviews"] and before["polar_reviews"] else None,
        "target_allegation_share_change_pp":100*(now["target_allegation_share_of_sampled_reviews"]-before["target_allegation_share_of_sampled_reviews"]) if enough else None,
        "verified_seller_or_product_change":None}


def main():
    audit=json.loads((OUT/"listing_evidence_audit.json").read_text(encoding="utf-8"))
    context=json.loads((OUT/"listing_context_audit.json").read_text(encoding="utf-8"))
    annotations={r["record_id"]:r for r in context["annotations"]}
    result={"recorded_on":RECORDED_ON.isoformat(),"observations":"Historical published review records, not generated examples. Their claims are not independently authenticated.",
        "time_reference":{"basis":"Within-dataset listing history; endpoint T is each listing's last observed review date", "recording_date_used_as_cutoff":False,
            "future_rolling_analysis":"Use successive historical cutoffs T and only records dated at or before T; do not use later records to generate earlier flags."},
        "ratio_definition":"L/H, plus bounded threshold metric L/(L+H); 3-star reviews reported separately",
        "trial_choices_not_validated":{"elevated_negative_share":TRIAL_THRESHOLD,"minimum_polar_reviews":MIN_POLAR_REVIEWS,
            "minimum_sampled_reviews_per_time_window":MIN_REVIEWS_PER_TIME_WINDOW,"window_days":WINDOW_DAYS,
            "thresholds_to_compare":[0.20,0.25,0.30]},
        "listings":[],"sampling_limit":"Available records are incomplete convenience samples; counts and time coverage do not establish population prevalence or the cause of a historical change."}
    selections={"general_exact_asin":{"B01415QHYW","B005WUHAX8"},
        "supplement_exact_asin":{"B0758LVKLL","B008YD57OO"}}
    for ds,ids in selections.items():
        for listing in audit[ds]["candidate_listings"]:
            if listing["listing_id"] not in ids:continue
            reviews=listing["reviews"]
            first=min(map(review_date,reviews))
            last=max(map(review_date,reviews))
            overall=metrics(reviews,annotations)
            share=overall["low_share_of_polar_reviews"]
            passes={str(value):share is not None and share>=value for value in [0.20,0.25,0.30]}
            result["listings"].append({"dataset":ds,"asin":listing["listing_id"],"first_sampled_review_date":first.isoformat(),
                "last_sampled_review_date":last.isoformat(),"overall_sample":overall,"ratio_threshold_sensitivity":passes,
                "trial_elevated_negative_share_flag":overall["polar_reviews"]>=MIN_POLAR_REVIEWS and share is not None and share>=TRIAL_THRESHOLD,
                "has_multiple_distinct_target_allegations":overall["distinct_relevant_texts"]>=2,
                "historical_windows_at_last_observation":windows(reviews,last,annotations),
                "confirmed_scam_listing":None})
    target=next(r for r in result["listings"] if r["asin"]=="B01415QHYW")
    assert target["overall_sample"]["low_1_2"]==10 and target["overall_sample"]["high_4_5"]==27
    assert target["overall_sample"]["neutral_3"]==1
    assert target["ratio_threshold_sensitivity"]=={"0.2":True,"0.25":True,"0.3":False}
    assert target["historical_windows_at_last_observation"]["recent"]["high_4_5"]==3
    assert target["historical_windows_at_last_observation"]["recent"]["low_1_2"]==0
    assert not target["historical_windows_at_last_observation"]["sample_count_gate_met"]
    assert target["historical_windows_at_last_observation"]["new_repeated_allegation_indicator"] is None
    assert "windows_at_analysis_date" not in target
    (OUT/"listing_ratio_time_analysis.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    checkpoint=ROOT/"checkpoints/checkpoint_01_low_star_and_text.json"
    assert checkpoint.read_bytes()==(OUT/"low_star_review_analysis.json").read_bytes()
    print(json.dumps(target,indent=2))
    print("Historical ratios and window counts checked. Checkpoint 1 unchanged:",hashlib.sha256(checkpoint.read_bytes()).hexdigest())


if __name__=="__main__":main()
