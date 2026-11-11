"""Record an assistant context audit of the fixed checkpoint's 116 specific hits.

Annotations are judgement calls for research, not independent human gold labels,
physical authentication, or proof of deliberate seller deception.
"""
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"outputs"
RELEVANT={"authenticity_allegation","authenticity_suspicion","mismatch_allegation"}


def norm(text):return re.sub(r"\s+"," ",text).strip().casefold()


def main():
    audit=json.loads((OUT/"listing_evidence_audit.json").read_text(encoding="utf-8"))
    general=[r for l in audit["general_exact_asin"]["candidate_listings"] for r in l["reviews"] if r["matched_issue_rules"]]
    order_hash=hashlib.sha256("\n".join(r["record_id"] for r in general).encode()).hexdigest()
    assert order_hash=="d7eeca4e185d47572e6d6aaee1d365196e4d6727fa274840092edc5fbc61299f","Review order changed; re-audit instead of reusing positional decisions"
    groups={
        "mismatch_allegation":[1,6,8,15,17,19,24,25,27,31,32,35,40,41,42,45,46,49,50,51,52,53,57,59,60,63,65,68,72],
        "authenticity_allegation":[2,4,9,10,22,34,38,62],
        "authenticity_suspicion":[3,11,12,16,21,30,33,67],
        "irrelevant_keyword_or_buyer_selection_error":[5,7,13,14,20,23,26,28,29,39,43,55,56,61,69,73],
        "unclear_responsibility_or_claim":[0,36,37,44,47,48,54,58,64,66,70,71],
        "service_plan_mismatch":[18],
    }
    indexes=[i for values in groups.values() for i in values]
    assert sorted(indexes)==list(range(74)) and len(set(indexes))==74
    decisions={i:label for label,values in groups.items() for i in values}
    special_notes={
        0:"Wrong size is reported, but seller dispatch versus buyer selection is unspecified.",
        7:"Reviewer explicitly acknowledges choosing an incompatible product; not a wrong-item allegation.",
        9:"Reviewer reproduces a purported brand-support email rejecting serial numbers as counterfeit and denying warranty. The reply is not independently authenticated.",
        20:"Counterfeit is negated; the review instead concerns a defective drive.",
        23:"Fake refers to other reviews, not the purchased product's authenticity.",
        32:"Knockoff refers to a replacement product; the reviewed item still receives a compatibility/marketing allegation.",
        39:"Fake describes how convincing a simulated security product looks, not a brand-authentication allegation.",
        43:"Reviewer says they ordered the wrong size.",
        49:"Reviewer reports two wrong-item deliveries; this remains one reviewer and one review, not two independent complaints.",
        53:"Reviewer reports measuring 42 inches against an advertised 54 inches; no independent measurement or historical listing is available.",
        55:"Reviewer explicitly calls the size choice their own mistake.",
        56:"Fake-looking appearance of a security product does not establish counterfeit branding.",
        60:"Fake refers to cosmetic chrome appearance; the review alleges a colour mismatch, not counterfeit branding.",
        61:"Fake refers to other reviews, not product authenticity.",
        65:"Reviewer reports both smaller dimensions than advertised and receiving one item instead of a two-pack.",
        66:"Review cites gaming-related search results; the actual listing's promise is not established.",
        67:"Reviewer reports contacting the brand about an unrecognized model, then suspects a fake; no brand response is supplied for independent verification.",
        69:"Reviewer says they ordered the wrong size.",
        73:"Fake describes an ornamental ring; explicit counterfeit branding or a concrete listing discrepancy is not established.",
    }
    annotations={}
    for i,r in enumerate(general):
        label=decisions[i]
        annotations[r["record_id"]]={"record_id":r["record_id"],"dataset":r["dataset"],"asin":r["asin"],
            "context_class":label,"target_relevant_allegation":label in RELEVANT,
            "support_type":"reviewer_reported_brand_confirmation" if i==9 else "reviewer_reported_brand_contact" if i==67 else "customer_text_only",
            "note":special_notes.get(i,"Context supports this allegation category; product outcome and seller intent remain unverified." if label in RELEVANT else "Context does not establish a clear allegation about counterfeit goods or seller-side item/description mismatch."),
            "annotation_source":"assistant_context_review_v1","verified_fraud":None}

    excluded_supp={
        "2d2d7772387f35285f17":"Duplicate refers to similarity to a competing soap, not an allegation that the received item falsely bears its stated brand.",
        "381976e1a4b0821acba0":"Duplicate refers to similarity to a competing soap; identical text also appears under another ASIN.",
        "6b1359f3fb86bc83b065":"Fake refers to YouTube/customer reviews, not the product's physical authenticity.",
    }
    retail_checks={"c2fba88ed69f7f7332b6","756b70fb2a9ec3d367ed"}
    for listing in audit["supplement_exact_asin"]["candidate_listings"]:
        for r in listing["reviews"]:
            if not r["matched_issue_rules"]:continue
            if r["record_id"] in excluded_supp:
                label="irrelevant_keyword_or_comparative_language"
                note=excluded_supp[r["record_id"]]
            elif "not_as_advertised_wording" in r["matched_issue_rules"]:
                label="mismatch_allegation"
                note="Reviewer reports a discrepancy between online nutrition information and the received package; underlying listing and package not independently checked."
            else:
                tentative=bool(re.search(r"\b(?:seems?|may|might|doubt|fear|could|think|suspect|either|felt\s+like|looks?\s+like)\b",r["text"],re.I))
                label="authenticity_suspicion" if tentative else "authenticity_allegation"
                note="Reviewer reports or suspects inauthentic goods, often from sensory, packaging or performance differences; authentication is unavailable."
            annotations[r["record_id"]]={"record_id":r["record_id"],"dataset":r["dataset"],"asin":r["asin"],
                "context_class":label,"target_relevant_allegation":label in RELEVANT,
                "support_type":"reviewer_reported_retailer_check" if r["record_id"] in retail_checks else "customer_text_only",
                "note":note,"annotation_source":"assistant_context_review_v1","verified_fraud":None}

    result={"annotation_method":"Assistant context audit of 74 general and 42 supplemental keyword hits; no independent human annotation agreement or fraud verification.",
        "general_review_id_order_sha256":order_hash,"datasets":{},"annotations":list(annotations.values()),
        "independently_confirmed_scam_listings":None,
        "conclusion":"No independent fraud ground truth exists here. Relevant allegations, repetition and reported external checks are distinct evidence levels."}
    for name in ["general_exact_asin","supplement_exact_asin"]:
        listings=[]
        evidence_families=defaultdict(list)
        for listing in audit[name]["candidate_listings"]:
            matches=[r for r in listing["reviews"] if r["matched_issue_rules"]]
            relevant=[r for r in matches if annotations[r["record_id"]]["target_relevant_allegation"]]
            family=hashlib.sha256(json.dumps(sorted((str(r["date_or_timestamp"]),r["stars"],norm(r["text"])) for r in listing["reviews"])).encode()).hexdigest()[:20]
            evidence_families[family].append(listing["listing_id"])
            listings.append({"listing_id":listing["listing_id"],"sampled_reviews":listing["sampled_reviews"],
                "sampled_low_star_reviews":listing["sampled_low_star_reviews"],
                "keyword_candidate_reviews":len(matches),"context_relevant_allegations":len(relevant),
                "distinct_relevant_texts":len({norm(r["text"]) for r in relevant}),
                "distinct_known_relevant_reviewers":len({r["reviewer_id"] for r in relevant if r["reviewer_id"]}) if name=="general_exact_asin" else None,
                "reported_external_check_reviews":sum(annotations[r["record_id"]]["support_type"]!="customer_text_only" for r in relevant),
                "sampled_low_star_fraction":listing["sampled_low_star_fraction"],
                "context_counts":dict(Counter(annotations[r["record_id"]]["context_class"] for r in matches)),
                "evidence_family_id":family})
        ds_annotations=[annotations[r["record_id"]] for listing in audit[name]["candidate_listings"] for r in listing["reviews"] if r["matched_issue_rules"]]
        repeated=[l for l in listings if l["distinct_relevant_texts"]>=2]
        result["datasets"][name]={"review_context_counts":dict(Counter(r["context_class"] for r in ds_annotations)),
            "keyword_candidate_reviews":len(ds_annotations),"context_relevant_review_allegations":sum(r["target_relevant_allegation"] for r in ds_annotations),
            "listing_ids_with_relevant_allegations":sum(l["context_relevant_allegations"]>0 for l in listings),
            "listings_with_multiple_distinct_relevant_texts":len(repeated),
            "distinct_review_collection_families_with_repeated_allegations":len({l["evidence_family_id"] for l in repeated}),
            "identical_sampled_review_collections_under_multiple_ids":[v for v in evidence_families.values() if len(v)>1],
            "listings":sorted(listings,key=lambda l:(-l["context_relevant_allegations"],-l["sampled_low_star_reviews"],-l["sampled_reviews"],l["listing_id"]))}
    assert len(annotations)==116
    assert all(r["verified_fraud"] is None for r in annotations.values())
    (OUT/"listing_context_audit.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    for name,ds in result["datasets"].items():
        print(name,json.dumps({k:v for k,v in ds.items() if k!="listings"},indent=2))
        for l in ds["listings"][:4]:print(json.dumps(l))


if __name__=="__main__":main()
