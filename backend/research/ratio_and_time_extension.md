# Proposed ratio and time extension after Checkpoint 1

Recorded 31 October 2026. This refines the listing-assessment stage; the accepted star-plus-text base and its original checkpoint remain unchanged. Review records are real downloaded observations, not synthetic examples. Thresholds below are explicitly proposed research choices.

## Ratios and the example listing

Let L be the number of individual 1-2-star reviews and H the number of 4-5-star reviews in a defined listing, period and sample. Keep 3-star reviews separate.

- Raw low-to-high ratio: L/H. If H is zero, show the counts and an undefined ratio rather than dividing by zero or treating a single review as conclusive.
- Bounded share for threshold testing: L/(L+H).
- Low-star share of all reviews: L/N, including 3-star reviews in N. This is a different denominator and must not be mixed with the preceding measure.
- Target-specific concern share: context-relevant low-star authenticity/mismatch allegations divided by all sampled reviews. Generic dissatisfaction is not automatically an authenticity allegation.

For general-Amazon ASIN `B01415QHYW`, the actual sample contains L=10, H=27 and one 3-star review. The raw ratio is 10/27=0.3704; the bounded low-star share is 10/37=27.03%; the all-review low-star share is 10/38=26.32%. Context review found one clear description-mismatch allegation among the two original wording hits, giving 1/38=2.63% context-relevant target allegations in the sampled reviews. These are descriptions of this sample, not fraud probabilities.

## Trial thresholds and evidence categories

A **25% bounded low-star share** can be tested as a prototype threshold for elevated negative-review concentration, with a trial minimum of **20 non-neutral reviews**. Compare alternatives of 20%, 25% and 30% instead of claiming that 25% is established by this example. The current listing passes the 20% and 25% ratio tests and fails the 30% test.

The threshold is not a validated scam cutoff. An initial concern can be highlighted when the base yields a relevant allegation. Repeated target concerns should be recorded separately, using at least two distinct relevant texts as an exploratory descriptor and reviewer IDs where available. One strong reported external check can also be displayed separately; it should not be suppressed solely because a sample-size threshold is unmet. Independent confirmation remains a different evidence level.

For the example listing, the trial ratio rule identifies elevated historical negative-review concentration, but the sampled text does not establish multiple clear target allegations. A possible-concern/watchlist category is a testable prototype output; a confirmed-scam or current-counterfeit label is not established.

Threshold performance must be evaluated on a separate independently labelled sample. Complaint annotations can validate a complaint-detection target; confirmed scam classifications require suitable independent outcome evidence. The trial values are not empirical sensitivity, specificity or calibrated probabilities.

## Dataset relative time after the base

The proposed sequence is **base screen, listing ratio, dated complaint pattern, contextual evidence assessment**. Time analysis should retain all sampled stars as denominators, while using the accepted low-star screen for target complaint text.

**Time is relative to the historical dataset, not to today's date.** For the initial endpoint audit, let T be the last observed review date for the listing. Compare records in (T - 90 days, T] with records in (T - 180 days, T - 90 days]. The date this report was written is metadata only and is never used as the comparison cutoff. A listing whose records end in 2021 can therefore be analysed relative to its 2021 endpoint.

Record both window review counts, the low-star share, the target-specific allegation share, and the number of distinct relevant reviewers/texts. Look for an increase in repeated concrete allegations, not simply an increase in all review volume. Report differences in percentage points, keeping the denominator consistent between windows.

For a later historical change-detection experiment, evaluate successive predetermined cutoffs T, such as month ends. Each result may use only records dated at or before its cutoff. Do not use later reviews to generate an earlier flag or choose the best-looking cutoff and present it as independent validation. If comparing different listings at the same historical moment, use a shared cutoff rather than their different individual endpoints.

The prototype audit uses a trial minimum of ten sampled reviews in each window. This is a coverage gate, not proof that ten observations are statistically sufficient or that the sample is representative. Missing periods must remain insufficient evidence rather than being scored as safe. Higher-volume histories should be used to assess sensitivity to window length, sample size and uncertainty.

## Actual dated check for the example

The 38 reviews for `B01415QHYW` span **2 November 2015 to 29 May 2021**. Its latest historical 90-day window contains **three sampled 4-5-star reviews and no 1-2-star reviews**. The preceding 90-day window contains no sampled records. This does not establish a sudden deterioration or a statistically supported recovery.

The correct conclusion is **insufficient coverage for this historical two-window comparison**. It is not a finding that the data is unusable merely because the listing's endpoint precedes the date of this project. Another supplemental listing has a concentration of low-star reviews during its historical 2020 records, but its window counts are also too small to validate a transition.

An observed change in complaints would indicate a possible change in customer experience. Attributing it to a seller switch, counterfeit inventory or listing replacement would require seller/offer, variant and historical listing information. A review timestamp alone does not identify the cause.

## Reproducibility

`analyse_listing_ratio_time.py` writes `outputs/listing_ratio_time_analysis.json`, containing real sample counts, ratios, trial threshold sensitivity and dataset-relative historical-window checks. The former wall-clock comparison has been removed in accordance with the clarified methodology. It does not generate observations, alter Checkpoint 1 or assign confirmed fraud labels.

`audit_sample_size.py` writes `outputs/sample_size_adequacy.json`. It measures per-listing sample depth and endpoint-window coverage for 30, 90, 180 and 365 days. These are coverage checks, not a complete scan of all possible historical cutoffs or a formal power calculation.
