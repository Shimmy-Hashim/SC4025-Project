"""Inspect listing-level support for the saved low-star-plus-text checkpoint.

All stars supply sampled denominators. Candidate text review stays within 1-2
stars. No rule in this script confirms a scam or creates fraud ground truth.
"""
import csv
import hashlib
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
RULES = json.loads((OUT / "low_star_review_analysis.json").read_text())["patterns"]
SPECIFIC = {name: re.compile(RULES[name],re.I) for name in [
    "counterfeit_wording","wrong_product_wording","not_as_advertised_wording"]}


def norm(text):
    return re.sub(r"\s+"," ",text).strip().casefold()


def identify(ds, asin, timestamp, stars, text, reviewer=""):
    return hashlib.sha256("\x1f".join(map(str,[ds,asin,timestamp,stars,text,reviewer])).encode()).hexdigest()[:20]


def load_general():
    rows, seen = [], set()
    for category in ["Electronics","Cell_Phones_and_Accessories"]:
        path = ROOT / "data/amazon-reviews-2023-sample" / (category+"_first20000.jsonl")
        with path.open(encoding="utf-8") as source:
            for line in source:
                r=json.loads(line)
                key=tuple(r[k] for k in ["asin","user_id","timestamp","text","rating"])
                if key in seen or not r["text"].strip(): continue
                seen.add(key)
                rows.append({"dataset":"general_amazon","asin":r["asin"],"parent_asin":r["parent_asin"],
                    "reviewer_id":r["user_id"],"stars":float(r["rating"]),"text":r["text"],
                    "date_or_timestamp":r["timestamp"],"verified_purchase":r["verified_purchase"],
                    "helpful_votes":r["helpful_vote"],"source_category":category,
                    "record_id":identify("general",r["asin"],r["timestamp"],r["rating"],r["text"],r["user_id"])})
    return rows


def load_supplement():
    rows=[]
    with (OUT / "indian_reviews_deduplicated_flagged.csv").open(encoding="utf-8-sig",newline="") as source:
        for r in csv.DictReader(source):
            if not r["review"].strip(): continue
            rows.append({"dataset":"indian_products_supplement","asin":r["asin"],"parent_asin":None,
                "product_name":r["name"],"reviewer_id":None,"stars":float(r["rating"]),"text":r["review"],
                "date_or_timestamp":r["date"],"verified_purchase":None,"helpful_votes":None,
                "record_id":identify("supplement",r["asin"],r["date"],r["rating"],r["review"])})
    return rows


def analyse(rows, group_field="asin"):
    grouped=defaultdict(list)
    for r in rows:
        r["matched_issue_rules"]=[k for k,p in SPECIFIC.items() if 1<=r["stars"]<=2 and p.search(r["text"])]
        grouped[r[group_field]].append(r)
    candidates=[]
    for listing,reviews in grouped.items():
        hits=[r for r in reviews if r["matched_issue_rules"]]
        if not hits: continue
        low=[r for r in reviews if 1<=r["stars"]<=2]
        known_reviewers={r["reviewer_id"] for r in hits if r["reviewer_id"]}
        candidates.append({"listing_id":listing,"group_field":group_field,
            "sampled_reviews":len(reviews),"sampled_low_star_reviews":len(low),
            "sampled_low_star_fraction":len(low)/len(reviews),
            "specific_wording_reviews":len(hits),
            "distinct_specific_wording_texts":len({norm(r["text"]) for r in hits}),
            "distinct_known_wording_reviewers":len(known_reviewers) if known_reviewers else None,
            "keyword_rules":dict(Counter(k for r in hits for k in r["matched_issue_rules"])),
            "reviews":reviews})
    candidates.sort(key=lambda r:(-r["specific_wording_reviews"],-r["sampled_low_star_reviews"],-r["sampled_reviews"],r["listing_id"]))
    return {"sampled_reviews":len(rows),"sampled_listing_ids":len(grouped),
        "specific_wording_reviews":sum(r["specific_wording_reviews"] for r in candidates),
        "candidate_listing_ids":len(candidates),
        "candidate_listing_sample_size_distribution":dict(Counter(r["sampled_reviews"] for r in candidates)),
        "listings_with_multiple_wording_reviews":sum(r["specific_wording_reviews"]>=2 for r in candidates),
        "listings_with_multiple_distinct_wording_texts":sum(r["distinct_specific_wording_texts"]>=2 for r in candidates),
        "listings_with_at_least_five_sampled_reviews":sum(r["sampled_reviews"]>=5 for r in candidates),
        "candidate_listings":candidates}


def negative_checkpoint_summary(rows):
    all_patterns=[re.compile(pattern,re.I) for pattern in RULES.values()]
    grouped=defaultdict(list)
    for r in rows: grouped[r["asin"]].append(r)
    candidates=[]
    for asin,reviews in grouped.items():
        low=[r for r in reviews if 1<=r["stars"]<=2]
        matches=[r for r in low if any(pattern.search(r["text"]) for pattern in all_patterns)]
        if matches:
            candidates.append({"asin":asin,"sampled_reviews":len(reviews),"sampled_low_star_reviews":len(low),
                "negative_keyword_reviews":len(matches),
                "specific_wording_reviews":sum(bool(r["matched_issue_rules"]) for r in low)})
    return {"matching_low_star_reviews":sum(r["negative_keyword_reviews"] for r in candidates),
        "candidate_listing_ids":len(candidates),
        "listings_with_multiple_negative_keyword_reviews":sum(r["negative_keyword_reviews"]>=2 for r in candidates),
        "candidate_listings":sorted(candidates,key=lambda r:(-r["negative_keyword_reviews"],-r["sampled_reviews"],r["asin"]))}


def main():
    checkpoint_dir=ROOT/"checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    checkpoint=checkpoint_dir/"checkpoint_01_low_star_and_text.json"
    source=(OUT/"low_star_review_analysis.json").read_bytes()
    if not checkpoint.exists(): checkpoint.write_bytes(source)
    assert checkpoint.read_bytes()==source,"The checkpoint must remain unchanged"
    general=load_general()
    supplement=load_supplement()
    result={"checkpoint":"checkpoint_01_low_star_and_text.json",
        "checkpoint_sha256":hashlib.sha256(source).hexdigest(),
        "denominator":"All available sampled nonempty reviews for each listing; not the listing's complete review history",
        "general_exact_asin":analyse(general),
        "general_parent_asin":analyse(general,"parent_asin"),
        "supplement_exact_asin":analyse(supplement),
        "general_all_negative_keywords":negative_checkpoint_summary(general),
        "supplement_all_negative_keywords":negative_checkpoint_summary(supplement),
        "fraud_ground_truth":"Unavailable. Keyword matches and repeated allegations cannot independently confirm intentional seller deception."}
    (OUT/"listing_evidence_audit.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    for name in ["general_exact_asin","general_parent_asin","supplement_exact_asin"]:
        ds=result[name]
        print(name,json.dumps({k:v for k,v in ds.items() if k!="candidate_listings"}))
        for r in ds["candidate_listings"][:10]: print(json.dumps({k:v for k,v in r.items() if k!="reviews"}))


if __name__=="__main__":main()
