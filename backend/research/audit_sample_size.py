"""Count effective listing and dated-window coverage in the actual real samples.

The metadata recording date is not a time-analysis cutoff. Endpoint windows are
relative to each listing's last observed review date, within its source history.
"""
import json
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path

from analyse_listing_evidence import load_general, load_supplement
from analyse_listing_ratio_time import review_date

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"outputs"


def assess(rows,candidate_ids):
    groups=defaultdict(list)
    for r in rows:groups[r["asin"]].append(r)
    distribution=Counter(len(rs) for rs in groups.values())
    coverage={}
    for days in [30,90,180,365]:
        pairs={"at_least_5_each":[],"at_least_10_each":[]}
        for asin,rs in groups.items():
            anchor=max(review_date(r) for r in rs)
            recent=sum(anchor-timedelta(days=days)<review_date(r)<=anchor for r in rs)
            previous=sum(anchor-timedelta(days=2*days)<review_date(r)<=anchor-timedelta(days=days) for r in rs)
            for minimum,key in [(5,"at_least_5_each"),(10,"at_least_10_each")]:
                if recent>=minimum and previous>=minimum:
                    pairs[key].append({"asin":asin,"cutoff":anchor.isoformat(),"recent_n":recent,"previous_n":previous,
                        "is_specific_wording_candidate":asin in candidate_ids})
        coverage[str(days)]={key:{"listing_count":len(values),"candidate_listing_count":sum(r["is_specific_wording_candidate"] for r in values),
            "listings":values} for key,values in pairs.items()}
    dates=[review_date(r) for r in rows]
    return {"nonempty_review_records":len(rows),"distinct_asins":len(groups),
        "distinct_known_reviewer_ids":len({r["reviewer_id"] for r in rows if r["reviewer_id"]}) or None,
        "one_review_asins":distribution[1],"one_review_asin_fraction":distribution[1]/len(groups),
        "review_count_distribution":dict(sorted(distribution.items())),
        "asins_by_minimum_total_reviews":{str(n):sum(len(rs)>=n for rs in groups.values()) for n in [2,5,10,20,30,50]},
        "asins_with_at_least_20_non_neutral_reviews":sum(sum(r["stars"]!=3 for r in rs)>=20 for rs in groups.values()),
        "specific_wording_candidate_asins":len(candidate_ids),
        "candidate_asins_with_at_least_20_non_neutral_reviews":sum(asin in candidate_ids and sum(r["stars"]!=3 for r in rs)>=20 for asin,rs in groups.items()),
        "first_review_date":min(dates).isoformat(),"last_review_date":max(dates).isoformat(),
        "endpoint_window_coverage_by_days":coverage}


def main():
    audit=json.loads((OUT/"listing_evidence_audit.json").read_text(encoding="utf-8"))
    result={"recorded_on":"2026-10-31","unit_of_adequacy":"Review, listing and time-window coverage are assessed separately",
        "time_basis":"Each listing's last observed dataset review date; not the wall-clock recording date",
        "caution":"Coverage gates are exploratory choices, not formal power calculations; unknown sampling selection and missing confirmed fraud labels remain."}
    for name,loader,source in [("general_amazon",load_general,"general_exact_asin"),("indian_products_supplement",load_supplement,"supplement_exact_asin")]:
        ids={r["listing_id"] for r in audit[source]["candidate_listings"]}
        result[name]=assess(loader(),ids)
    assert result["general_amazon"]["nonempty_review_records"]==39986
    assert result["general_amazon"]["distinct_asins"]==33779
    assert result["general_amazon"]["one_review_asins"]==30305
    assert result["indian_products_supplement"]["distinct_asins"]==145
    for name in ["general_amazon","indian_products_supplement"]:
        assert result[name]["endpoint_window_coverage_by_days"]["90"]["at_least_10_each"]["listing_count"]==0
    (OUT/"sample_size_adequacy.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    for name in ["general_amazon","indian_products_supplement"]:
        ds=result[name]
        print(name,json.dumps({k:v for k,v in ds.items() if k not in ["endpoint_window_coverage_by_days","review_count_distribution"]},indent=2))
        print("Window coverage",json.dumps({days:{key:{k:v for k,v in values.items() if k!="listings"} for key,values in conditions.items()} for days,conditions in ds["endpoint_window_coverage_by_days"].items()}))


if __name__=="__main__":main()
