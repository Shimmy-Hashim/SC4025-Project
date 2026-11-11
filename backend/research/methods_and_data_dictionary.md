# Methods and data dictionary

For the chronological development of the approach and a report-ready methodology paragraph, see [Methodology and Research Development](methodology_and_research_journey.md). This technical reference describes data preparation and interpretation; the chronological record preserves how the research questions and screening choices evolved.

## What is being measured

The current analysis measures **whether selected review text contains specified wording**. It does not measure verified fraud, the probability of receiving a counterfeit, or a seller's intent. The dictionary deliberately uses terms such as `term_flag` and `phrase_flag` rather than `is_scam`.

Three targets must remain separate:

1. **Review allegation:** a customer says an item may be counterfeit, wrong, or inconsistent with the listing. Humans can label this from the text.
2. **Verified product/order outcome:** an item is authenticated as counterfeit or an order is confirmed to contain a different product. This requires independent evidence.
3. **Intentional seller deception:** the seller deliberately misled the consumer. A delivery mistake or poor quality alone does not establish this.

## Cleaning and units of analysis

**Main dataset:** retain every raw record in the augmented export. For descriptive product comparisons, take the first source-order row for each `product_id`, producing 1,351 products from 1,465 rows. This is deterministic but does not identify the newest or most accurate snapshot. The `review_content` field combines multiple reviews, while `rating` and `rating_count` describe the listing. Do not split the text on commas: commas also appear inside reviews, so the original review boundaries cannot reliably be recovered. Do not align exploded reviewer/review IDs to text by position without independent validation.

**Supplemental dataset:** remove exact duplicates across all five original columns, producing 1,391 records from 2,782. Exclude three missing review bodies from text-rate denominators, leaving 1,388 reviews across the source's 145 ASINs. Dates range from 12 April 2015 to 6 October 2020. No reviewer ID, seller ID or verified-purchase indicator is supplied.

**Cross-source matching:** compare exact ASIN strings, `product_id` versus `asin`. There are zero overlapping IDs. Therefore, do not attach main-dataset prices/discounts to supplemental review rows. Similar product names, a shared category or Indian branding do not establish a product or seller identity.

**Repeated text:** report an additional sensitivity analysis retaining the first row per case-folded, whitespace-normalized text hash. It leaves 1,197 main review blobs and 1,133 supplemental nonempty texts. This is a sensitivity check, not a claim that identical short reviews are necessarily duplicate observations. Reviews may be repeated across related product variants; generic wording may also be independent.

**General-Amazon check:** take the first 20,000 source-order records each from Electronics and Cell_Phones_and_Accessories in the official Amazon Reviews 2023 repository. The download manifest pins the source revision and records SHA-256 hashes; no publisher-provided Python loading code is executed. Remove duplicates on ASIN, user ID, timestamp, body and rating across the pooled sample, then exclude empty bodies. This leaves 39,986 reviews. Category attribution follows the first retained record if a review occurs in both categories. No weighting to national or category populations is performed.

The general sample has 21 exact ASIN matches to India listing IDs, covering 39 review records, and four parent-ASIN matches. Only the exact variant-ASIN match is used in the exported join, validated as many review rows to one retained India listing row. India prices/ratings are labelled as India listing snapshot values; general review stars, text, purchase-verification and helpfulness describe the sampled general-Amazon review. The join does not assign an India marketplace, seller or fraud outcome to those reviews. None of the 39 matched bodies triggers a rule; this joined subset cannot estimate a complaint-versus-price relationship.

The general sample's individual body, star rating, `verified_purchase`, `helpful_vote` and timestamp fields are analysed separately. There are no unit-authentication or seller/order linkage fields. General candidate exports retain blank human and fraud labels. They are separate from the 315-row annotation queue prepared for the two smaller datasets.

## Appended columns

| Column | Meaning | How to interpret |
| --- | --- | --- |
| `source_row` | Original source-order row, starting at 1; main file only | Trace back to the raw CSV. |
| `scam_word_flag` | Word-boundary match for scam/scams/scammed/scammer/scamming | Very narrow wording indicator; both samples' matches also contain the exact standalone word scam. |
| `general_deception_flag` | Scam-family, fraud/fraudulent or cheat-family wording | May refer to pricing, service, reviews or another issue. |
| `counterfeit_term_flag` | Counterfeit, fake, duplicate, knockoff, not original/genuine or non-genuine wording | Broad screening indicator. Does not resolve negation, uncertainty, product context, or references to fake reviews. |
| `wrong_product_phrase_flag` | Wrong item/product/model/size/colour/variant/brand, specified received-different phrases, or not what I ordered | A phrase can describe a non-fraud fulfillment error or a hypothetical warning. |
| `not_as_advertised_phrase_flag` | Specified not-as-advertised/described/shown/pictured, mismatch, misleading-description or false-claim phrases | Narrow coverage; zero matches do not establish absence of listing mismatch. |
| `any_complaint_rule_flag` | At least one of the five rules fired | Candidate for review, not an adjudicated complaint label. |
| `matched_terms` | Unique matched terms/phrases | Helps inspect why the rule fired. |
| `review_text_missing` | Empty or absent review body | Such rows are excluded from text-rate denominators. |
| `review_text_char_count` | Original text length in characters | Helps detect differing opportunities for a keyword match. |
| `text_group_id` | First 20 hexadecimal characters of SHA-256 of normalized text | Groups identical text for sensitivity analysis and leakage checks. |
| `label_source` | `unvalidated_keyword_rules_v1` | Rule outputs have not been validated against human labels. |
| `source_dataset` | Original Kaggle dataset identifier | Provenance. |
| `is_synthetic` | Always 0 in these exports | Source observations and deterministic derived columns; no simulated values. |
| `human_complaint_label` | Blank | Reserved for independent human annotation. |
| `fraud_ground_truth` | Blank | No verified fraud labels are available. |
| `*_numeric` | Cleaned price, percentage, rating or count | Currency symbols, commas and percent symbols removed; invalid/missing values remain missing. Discount values are percentage points, e.g. 64 means 64%. |
| `top_category` | First level of the pipe-delimited category | Main file only; source taxonomy, not a standardized risk category. |
| `duplicate_product_id` | Product ID occurs more than once in the full main file | Do not treat repeated rows as independent products. |
| `review_year`, `review_record_id` | Derived year and hash of ASIN/date/rating/text | Supplemental file only. A record hash is not a verified customer/order identifier. |

Exact regular expressions are in `analyse_reviews.py` and `outputs/analysis_summary.json`. Rules are case-insensitive and run only on `review_content` or `review`, not listing descriptions. All computed statistics are deterministic; no model has been fitted.

The focused `audit_scam_keyword.py` check distinguishes the exact word scam from its word family. In the general sample there are eight exact-word matches versus 12 family matches. The main India sample has five matched ASINs but only one matching normalized text blob, with an installation-service context. Two general-Amazon matches concern scam telephone calls rather than a scam allegation about the purchased product. These checks demonstrate why occurrence flags must remain distinct from context-validated complaint labels. Results are recorded in `outputs/scam_keyword_audit.json`.

## Interpreting the associations

The outcome in the exploratory tables is a rule match in text. Comparing prices, discounts, category, aggregate listing ratings and available text length describes this selected corpus. It does not establish causal predictors of counterfeiting. The supplemental comparison between a review's star rating and its own wording describes how people express dissatisfaction; that same order's review is unavailable before purchase.

The strongest observed relationship is between counterfeit-related wording and low review stars. The literal scam-only sample is too small for a meaningful model. Main-listing aggregate ratings are nearly identical between candidate and non-candidate groups, and the candidate group has longer text. Treat text exposure, category mix, repeated text and the source's selection process as possible explanations for differences.

No significance tests or population estimates are reported. These are old, selected convenience samples with unknown selection probabilities and dependent observations. The reported percentages are sample descriptions, not estimates of Amazon India's current incident rate.

## Annotation and evaluation plan

Use multi-label annotation for **counterfeit allegation**, **wrong-item allegation**, **not-as-described allegation**, **other dissatisfaction**, and **no relevant allegation**, plus a separate **unclear** status. Counterfeit and mismatch labels may co-occur. Annotators should record whether the reviewer reports their own received item, speculates, negates a concern, discusses fake reviews, describes a replacement, or only warns about other sellers.

Have two annotators independently read the text, ideally blinded to star rating and the rule flag. Resolve disagreements using a written guideline; retain the evidence span. Agreement measures and per-class counts should accompany the labelled corpus. A human label of an allegation remains distinct from physical authentication or a confirmed order mismatch.

The 315-row queue contains all 115 current rule candidates and 100 random non-candidates from each sample, using seed 4025. This oversamples candidates. It is useful for rule-error discovery; it is not a representative test set. Estimating corpus-level recall/prevalence from it requires accounting for different sampling fractions. A separate representative, independently labelled holdout is preferable. With only 1,388 supplemental texts, fully annotating that corpus is also feasible.

Before training, group by product identity and identical/near-identical text, inspect related variants, and prevent text or product leakage across splits. For a future India deployment, reserve India-specific data and a later time period for final evaluation. The main dataset has no review dates and therefore cannot establish a historical pre-purchase forecast test. Do not include the target review, future reviews, later aggregate ratings, or post-order returns in features available at the prediction cutoff.

Compare a literal-keyword baseline, a text classifier and a text-plus-metadata classifier on the same independent labels. A TF-IDF/logistic-regression baseline is a reasonable proposed starting point; none has been trained here. Report per-class precision/recall/F1, PR-AUC where suitable, class counts and false-positive examples. Add probability calibration metrics only when the output's target and ground truth are well defined. Accuracy alone is misleading for rare complaints.

For a genuine seller-offer risk model, request at least ASIN/variant, seller/offer ID, order/review linkage, timestamps, marketplace, a validated complaint outcome and features known before purchase. Review signals from a pooled listing cannot identify the currently selected seller. Without that linkage, scope the MVP to product-listing complaint evidence.

## Synthetic data decision

The detailed [methodology record](methodology_and_research_journey.md) distinguishes empirical sample-size limitations from real-informed synthetic fixtures. Following the user's subsequent request, the [synthetic-data methodology](synthetic_data_methodology.md) documents 10,920 generated reviews across 100 fictional listings, calibrated from Indian Products on Amazon. These remain separate from empirical evidence. The new combined export uses `is_synthetic` to distinguish the preserved 1,388 real rows from generated rows. Earlier empirical CSVs described above retain `is_synthetic=0` throughout. Dataset-relative time and ratio gates are described in that record and the [ratio/time extension](ratio_and_time_extension.md).

Synthetic data is not required to demonstrate the relationships found here. Appended keyword indicators are derived data, not synthetic data. Do not fill unknown fraud outcomes or seller histories with invented values in the empirical dataset.

If the team later needs an interface demo with missing seller/offer fields, create a separate fixture file. Prefix simulated columns with `synthetic_`, use IDs such as `SYNTH_SELLER_001`, record the generating assumptions and random seed, and include `is_synthetic=1`. Keep it out of the real evaluation set and out of market-prevalence calculations. A score generated from assumed relationships can demonstrate software behavior, but cannot validate those relationships or a claimed scam probability.
