# Methodology and Research Development

Recorded through 31 October 2026 for the SC4025 Amazon India project. This document preserves how the approach developed, including the user's decisions, the work performed, and the limits of the resulting evidence. The frozen [Checkpoint 1](checkpoints/checkpoint_01_low_star_and_text.md) remains unchanged.

## Research question and scope

The project investigates whether existing reviews can help identify product listings associated with suspected counterfeit goods or wrong/not-as-advertised products. A further question is whether low ratings and relevant review wording identify genuinely suspicious listings, rather than listings that merely contain an isolated, irrelevant or ambiguous use of words such as scam or fake.

The user's initial approach was to search for relevant data beyond the supplied sources, examine relationships between available variables and review text, and use synthetic columns only if real data could not support the required exploratory work. General-Amazon data was acceptable when appropriate Amazon India data was unavailable, provided the search and geographic limitations were documented.

For the subsequent synthetic-data stage, the user selected **Indian Products on Amazon as the primary review dataset**, with general Amazon Reviews 2023 retained as a secondary methodological comparison. The [synthetic-data methodology](synthetic_data_methodology.md) documents the resulting scripted generation. This does not change which sources supplied the earlier measured results.

## Development of the method

| Stage | User direction and analytical decision | Work completed and reason |
| --- | --- | --- |
| 1 Establish the starting sources | Begin with the sources in task info.txt and look for additional relevant data. | Confirmed the Amazon India Sales Dataset and Amazon Reviews 2023 as the starting sources. Found the Indian Products on Amazon corpus and a Mendeley India-review source. |
| 2 Audit suitability and clean the data | Check what variables can actually be linked to review text. | Inspected fields, missing text, duplicate records and identifiers. Distinguished individual review stars from aggregate product ratings. Kept raw source data intact. |
| 3 Explore relationships | Use review wording as the exploratory outcome, initially including the keyword scam. Compare it with other variables. | Compared stars, purchase verification, helpful votes and text length in general reviews; compared prices, discounts, ratings, rating counts and categories in the India listing data. These were descriptive comparisons, not independent predictive effects or a fitted fraud model. |
| 4 Check keyword relevance | Establish whether matches really refer to the assigned counterfeit/mismatch problem. | Found sparse exact scam matches and contextual false matches, including installation-service complaints, scam telephone calls and references to fake reviews. Broader authenticity and mismatch wording was examined separately. |
| 5 Refine to two identifiers | The user proposed focusing on individual 1-2-star reviews and then examining negative review text, including waste of money, not good and fake. | Applied a star-first screen and grouped wording into general dissatisfaction, authenticity concerns and wrong/not-as-described concerns. This user-directed refinement is saved as Checkpoint 1. |
| 6 Move from reviews to listings | The user proposed checking whether those listings have substantial bad-review evidence and whether the evidence supports a scam-listing claim. | Grouped candidates by exact ASIN, checked parent ASIN separately, calculated sampled low-star shares and examined repeated relevant allegations. All sampled stars were used only as the denominator for listing proportions; the primary text screen remained focused on 1-2 stars. |
| 7 Test context and corroboration | Distinguish a suspicious listing from a listing containing scam-related wording. | Audited 116 specific-wording matches in context, separated buyer mistakes and ambiguous cases, checked copied review collections and recorded reviewer-reported brand/retailer checks. The audit was performed by the assistant and is not an independent human gold standard. |
| 8 Decide whether synthetic data is needed | Use synthetic columns only if the available real data does not support the intended exploratory stage. | At this stage, real text supported derived screening indicators and listing-level investigation, so no synthetic observations or fraud-confirmation labels were created. Independent fraud outcomes remain unavailable. |
| 9 Make listing ratios explicit | The user requested a threshold comparing 1-2-star with 4-5-star reviews. | Defined low/high ratio, bounded low-star share, a 25% trial threshold, a 20-review trial coverage gate and sensitivity alternatives. These choices have not been validated as scam cutoffs. |
| 10 Add time within the dataset | The user clarified that recent and earlier refer to the dataset's historical period, not real time. | Historical windows are anchored to each listing's last observed dataset date. Wall-clock comparisons were removed. A later rolling experiment would use only data available at each historical cutoff. |
| 11 Assess sample size and the synthetic option | Check whether the quantity is sufficient for the expanded method and whether synthetic data would help. | Counted review depth, candidate-listing coverage and paired time-window coverage. The current sample supports screening exploration but is sparse for listing/time validation. Real enrichment is preferred; synthetic fixtures are an optional separate tool for prototype tests. |
| 12 Generate separate real-informed scenarios | The user chose Indian Products on Amazon as the primary source and requested AI-assisted design with ordinary scripted bulk generation. | Implemented a seeded Python generator and a separate synthetic-data methodology. The default run creates 10,920 reviews at 100 fictional listings, plus a new combined export retaining the 1,388 real reviews with provenance flags. Prototype checks expose generic-quality, copied-text, context and sparse-history failure modes; no real fraud outcomes are inferred. |

This was an **exploratory process refined through inspection and discussion**. The keyword definitions and star filter were not independently validated on a separate test set. The saved chronology should not be presented as a preregistered confirmatory experiment.

## Data used and preparation

| Source | Analysed records | Role and limitation |
| --- | --- | --- |
| [Amazon Sales Dataset](https://www.kaggle.com/datasets/karkavelrajaj/amazon-sales-dataset) | 1,465 original rows; 1,351 distinct product IDs for product comparisons. | India listing metadata and combined review text. The rating is a listing aggregate; individual review stars and seller-offer linkage are unavailable. |
| [Amazon Reviews 2023](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023) | First 20,000 records each from Electronics and Cell Phones/Accessories. After four duplicates and ten empty bodies were removed, 39,986 nonempty reviews remained. | General-Amazon individual review stars, text, dates, verification and helpful votes. This is a file-order convenience sample, not a random or India-only sample of the full dataset. |
| [Indian Products on Amazon](https://www.kaggle.com/datasets/nehaprabhavalkar/indian-products-on-amazon) | 2,782 raw rows became 1,391 after exact deduplication; excluding three missing bodies left 1,388 usable reviews across 145 ASINs. | Initially additional review-level evidence; now the primary calibration source for the synthetic stage. Country/marketplace and reviewer identity are not supplied, and the reviews are historical. |

The [Mendeley source](https://data.mendeley.com/datasets/2pv6d8fz7y/2) was considered but not analysed because its publisher describes only 3-5-star reviews. It cannot support the adopted 1-2-star screen.

Original source columns were preserved. Numeric fields and text-rule indicators were appended separately. Combined review text was not split on commas because commas do not reliably identify review boundaries.

Exact ASIN matching found no overlap between the main India catalogue and the Indian-products supplement. The general sample shared 21 exact ASINs with the India catalogue, covering 39 reviews; none triggered the specific complaint screen. Category or product-name similarity was not used to invent links between unrelated records.

## Operational definition of the checkpoint

The two identifiers are:

1. **Rating identifier:** the individual review has one or two stars.
2. **Text identifier:** its body contains selected negative or issue-related wording.

Generic negative wording identifies dissatisfaction. Authenticity or item/description-mismatch wording identifies a candidate for closer examination. A keyword match alone is not the final target label.

The checkpoint produced 309 selected-wording matches among 5,071 low-star general reviews, including 74 authenticity/mismatch wording candidates. The supplemental corpus produced 77 selected-wording matches among 338 low-star reviews, including 42 specific-wording candidates. These are historical screening counts, preserved independently of later context decisions.

For the original India catalogue, the individual-star gate cannot be applied to the combined review field using its aggregate rating. A highly rated product can still contain individual low-star complaints. That dataset was used for metadata exploration and a separate contextual check, not falsely treated as individually rated review data.

## Listing level validation

For each candidate ASIN, the analysis records the number of available reviews, the number and proportion rated 1-2 stars, the number of relevant complaint texts and any available distinct reviewer IDs. Counts of matching words are not substituted for counts of reviewers or orders.

Context review distinguishes authenticity allegations, authenticity suspicion, item/description mismatch, general dissatisfaction, buyer selection errors, irrelevant keyword uses and unclear cases. A review describing two orders still represents one reviewer account. A reported serial-number, barcode or retailer check is recorded as supporting detail, not independently authenticated evidence.

Repeated distinct texts are an exploratory descriptor. At least two distinct relevant texts were used to describe repetition; this is not a validated fraud threshold. Entire copied review collections under multiple ASINs were identified so they were not treated as independent corroboration. Listing proportions use the downloaded source sample, not a complete review history or a population estimate.

The resulting evidence levels are: keyword candidate; relevant listing concern; repeated concern in the sample; reviewer-reported external check; and independently confirmed outcome. The current work found examples of the first four, but did not obtain the fifth. Allegations about a delivered unit, a listing and intentional seller deception remain separate.

## Relationship to the market research role

Academic work on trust, perceived risk, review analysis, weak supervision and calibration was reviewed alongside Bain and PwC consulting research and relevant platform documentation. These sources informed the customer problem, competitor benchmark, SWOT, proposed product scope and assumption-based market sizing. No new customer interviews or representative consumer survey were conducted by this project analysis.

The literature supports investigating the feature. It does not independently confirm that a particular dataset listing is fraudulent. Market estimates were kept separate from review-flag rates and synthetic assumptions.

## Listing ratios and provisional thresholds

For one listing in a defined historical period, let L be the number of individual 1-2-star reviews, H the number of 4-5-star reviews, M the number of 3-star reviews, N=L+H+M, and C the number of low-star reviews with context-relevant authenticity or mismatch allegations. Record counts as well as ratios.

| Measure | Definition | Interpretation |
| --- | --- | --- |
| Low-to-high ratio | L/H | Directly compares negative and positive star groups. If H=0, keep the ratio undefined and show the counts. |
| Bounded low-star share | L/(L+H) | Proposed threshold measure. Excludes the neutral 3-star group; it is unavailable if L+H=0. |
| Low-star share of all sampled reviews | L/N | Includes 3-star reviews in the denominator. Must not be confused with the preceding share. |
| Target-specific allegation share | C/N | Describes relevant low-star complaints among sampled reviews, not actual counterfeit incidence. |

The current **trial**, not validated, operating choices are a 25% bounded low-star share, at least 20 non-neutral reviews for applying that concentration rule, and at least two distinct relevant texts for describing repeated concerns. Compare 20%, 25% and 30% ratio-share thresholds in sensitivity analysis. Twenty reviews is an operational gate intended to avoid interpreting tiny denominators; it is not a formal statistical sufficiency result.

A base match can still be shown as an initial concern even if the concentration rule cannot be evaluated. Insufficient coverage is not equivalent to a safe listing. A single reviewer-reported external check should be displayed separately rather than discarded simply because it lacks repetition. Use the following evidence descriptions instead of a single unsupported binary scam label: initial text concern; elevated negative-review concentration; repeated target concern; reviewer-reported external check; independently confirmed outcome.

For `B01415QHYW`, the actual sample has L=10, H=27 and M=1. Therefore L/H=0.3704, L/(L+H)=27.03%, and L/N=26.32%. Context review found C=1 among the two original wording hits, giving C/N=2.63%. The listing passes the trial 25% concentration rule but does not establish repeated clear target allegations. A potential-concern/watchlist category can be tested; these percentages are not scam probabilities.

A positive-review majority does not independently disprove a problematic delivery, and a negative majority does not establish deception. Reviews may concern different batches, sellers, variants or buyer errors. Systematic comparison of positive and negative text remains a next step. Thresholds should ultimately be assessed using independent labels and separate evaluation data rather than being selected to fit this single example.

## Dataset relative temporal analysis

**All references to time in this methodology mean time within the dataset. They do not mean real-time monitoring or comparison with the date this project was written.** The historical age of the dataset does not by itself prevent a historical analysis.

For the initial endpoint check, define T as the last observed review date for an ASIN in the downloaded source. With window width W=90 days, the recent historical window is (T-W,T] and the preceding window is (T-2W,T-W]. The first date boundary is excluded and the last included, so records are not counted in both windows. General-Amazon timestamps are converted to UTC calendar dates; supplemental dates retain their supplied calendar-day precision. Do not infer precision or location absent from the source.

For each window, calculate N, L, H, M and C; the bounded low-star share; the target-specific allegation share; and distinct relevant reviewer/text counts. Compare changes in shares in **percentage points**, as well as changes in the actual complaint counts. An increase in review volume alone is not an increase in complaint concentration. General quality complaints and authenticity/mismatch allegations must remain separate.

The trial temporal coverage gate is at least ten sampled reviews in **each** window. This is an exploratory gate, not a power calculation. If either window is empty or below the gate, return **insufficient temporal coverage** and leave a change conclusion unavailable. A missing earlier period must not become a zero complaint rate, and a listing must not be called safe merely because a sample lacks records. If either window contains no non-neutral stars, its low/high share is unavailable even when N is nonzero.

A future temporal escalation rule would look for a rise in target-specific allegations, repeated concrete descriptions and adequate baseline/recent coverage. No magnitude-of-change threshold has been validated. A temporal change can support a possible deterioration category; attributing it specifically to counterfeit inventory, a seller switch or deliberate fraud requires offer, variant and historical listing evidence.

After obtaining denser histories, extend the endpoint check to successive predetermined historical cutoffs, such as month ends. At each cutoff, use only records dated at or before it. Later reviews must not influence earlier flags. For comparisons between listings at the same historical moment, use a common cutoff. Listing-specific endpoints are suitable for within-listing descriptive checks but represent different historical dates across listings.

For the actual example `B01415QHYW`, T is **29 May 2021**, not the project recording date. Its recent historical 90-day window has three sampled 4-5-star reviews and no low-star reviews; the preceding window has no sampled records. This result is **insufficient historical window coverage**, not evidence of deterioration, recovery or safety. No comparison against a 2026 window is part of the clarified method.

## Sample size adequacy

Adequacy must be judged separately for review-language exploration, listing-level concentration, temporal change and confirmed-fraud evaluation. A large number of reviews spread thinly across many ASINs does not supply long histories for any one ASIN.

| Coverage measure from the real samples | General Amazon sample | Indian-products supplement |
| --- | ---: | ---: |
| Usable review records | 39,986 | 1,388 |
| Distinct ASINs | 33,779 | 145 |
| ASINs with exactly one sampled review | 30,305 (89.7%) | 2 |
| ASINs with at least 10 sampled reviews | 60 | 132 |
| ASINs with at least 20 sampled reviews | 13 | 0 |
| ASINs with at least 20 non-neutral reviews | 11 | 0 |
| Specific-wording candidate ASINs meeting the 20 non-neutral-review trial gate | 1 of 73 | 0 of 26 |
| ASINs with at least 10 reviews in both latest consecutive 90-day dataset-relative windows | 0 | 0 |

The general corpus has 6,734 known reviewer IDs, so review records are not 39,986 independent people. The supplement supplies no reviewer IDs. These facts, along with copied text/collections and selection effects, limit how raw counts can be interpreted as independent evidence.

Window sensitivity checks at each listing's endpoint considered widths of 30, 90, 180 and 365 days. At 365 days, only two general-sample ASINs meet ten reviews in each window, and neither is among the 73 specific-wording candidates. No supplemental ASIN meets that ten-per-window gate. If the gate is reduced to five per window and the window widened to a year, one general candidate and three supplemental candidates qualify. That permits a few coarse descriptive comparisons, not validation of abrupt changes. These checks concern the last two windows per ASIN, not every possible earlier cutoff.

**Assessment:** there is enough real text to demonstrate and investigate the base screen. The present extraction is too thin to validate the listing-ratio threshold broadly, and it does not support the proposed 90-day change test at the chosen coverage gate. Confirmed-fraud evaluation also lacks independent outcome labels, irrespective of review count. The main India catalogue's 1,351 products do not solve the problem because its source lacks individual review-star and timestamp linkage.

The preferred next data step is to change extraction from broad file prefixes to **denser real review histories for fewer selected ASINs**, including all rating groups and historical dates. Include candidate listings and comparison listings, preserve exact variant and reviewer information where supplied, and document the collection method. Do not select only low-star reviews when estimating listing-level shares. The full general-Amazon source contains far more records than the small subset used here, so real enrichment should be attempted before treating the current sample as the maximum available data.

There is no universal number of reviews that makes a scam label valid. Future sample planning should specify the intended target, acceptable uncertainty, expected number of relevant cases, dependence between records and evaluation design. The current 20-review and ten-per-window gates are transparent prototype choices, not substitutes for that planning.

## Whether to create synthetic data from real data

**Recommendation:** do not expand the empirical dataset with generated reviews just to increase N or make a ratio/time gate pass. First seek denser real histories. Synthetic records cannot establish that a real listing is fraudulent or repair the absence of independently verified outcomes.

Three different operations should not be confused:

| Operation | Status and appropriate purpose |
| --- | --- |
| Derive a keyword flag, ratio, date bin or complaint count from actual records | Recommended and already used. These are calculated features, not synthetic observations. |
| Duplicate or resample reviews to inflate listing/time counts | Does not add independent evidence. Do not use it to calculate empirical complaint prevalence, support a claim of corroboration or meet coverage gates. |
| Generate a separate real-informed synthetic listing history | Optional for testing whether the MVP handles known scenarios and edge cases. It is a simulation, not evidence about actual listings. |

If a prototype needs a sudden-change scenario that the sample cannot support, use real data only to inform plausible structure and broad distributions, then create separate synthetic ASINs and fictional review histories. Useful scenarios include stable mostly positive feedback; a rise in specific authenticity allegations; a rise in generic quality dissatisfaction without authenticity claims; one isolated complaint amid positive feedback; a historical problem followed by more positive feedback; sparse histories; and copied/repeated reviews that should not count as independent corroboration. Dates must follow the same dataset-relative cutoff/window rules.

Keep synthetic cases in a separate fixture file with `is_synthetic=1`, synthetic IDs, a scenario label, a fixed random seed, documented generation assumptions and links to the real summaries used for realism. Do not attach invented counterfeit outcomes or seller histories to real ASINs. A synthetic transition label means the transition was constructed for a test; it does not mean a real counterfeit event was authenticated.

If synthetic text augmentation is later considered for a learned classifier, split the real data first, prevent related ASIN/text leakage, keep augmentation in training only, and evaluate against independently labelled real held-out data. State whether the prediction target is a complaint allegation or an authenticated outcome. Increasing generated examples must not be reported as increasing independently observed fraud cases.

At the earlier checkpoint, no synthetic observations had been generated. Following the user's subsequent request, **10,920 synthetic reviews across 100 fictional listings** have now been generated in a separate fixture set. A new combined export preserves the 1,388 real records and distinguishes both groups with `is_synthetic`. The [synthetic-data methodology](synthetic_data_methodology.md) records calibration from Indian Products on Amazon, controlled assumptions, generation code and checks. No fraud labels were created. This stage does not change the real-data findings or Checkpoint 1; it tests **prototype behaviour** rather than validating the central scam hypothesis.

## Current completion boundary and next tests

Completed work comprises source discovery, preparation, descriptive variable comparisons, the frozen base screen, listing-level context/duplication checks, selected endpoint ratio/time audits, sample-depth/window-coverage checks and the separate scripted synthetic scenario tests. A systematic semantic comparison of all positive texts, a broad real historical change-detection evaluation, independent human annotation and outcome authentication remain incomplete.

The next tests are to obtain denser histories; compare positive/negative contexts for the same variant; examine distinct reviewers' repeated concrete allegations; test historical window changes; inspect supporting serial/package/measurement evidence; and compare reviews with time-matched listing claims. Purchase verification, helpful votes and available images can supply supporting information, without being treated as authenticity proof. Seller-change attribution requires additional seller/offer histories.

Details of the ratio and time implementation are in the [extension record](ratio_and_time_extension.md). Counts and coverage checks are in `outputs/sample_size_adequacy.json`. Changes in this methodology are recorded separately from the original checkpoint.

## Report ready methodology paragraph

We used an exploratory secondary-data approach to investigate whether customer reviews could identify product listings associated with suspected counterfeit goods or wrong/not-as-advertised products. We assessed an Amazon India listing dataset and additional review-level sources, using a bounded general-Amazon sample where India-specific fields were unavailable and documenting its sampling limitations. After removing duplicate records and missing review text, we compared available variables with complaint-related wording. We refined the method to two screening identifiers: an individual review rating of one or two stars and relevant negative wording. General dissatisfaction was separated from authenticity and mismatch concerns, and this screen was preserved as a checkpoint. We then grouped candidates by ASIN, examined contextual relevance, repeated distinct allegations, sampled rating distributions and reviewer-reported supporting checks. Listing concentration was expressed as the proportion of low-star reviews among 1-2- and 4-5-star reviews, with neutral ratings reported separately. A 25% threshold and minimum-count gates were specified as trial choices requiring validation. Time was measured relative to historical dataset cutoffs, not the project date, using equal-length preceding and recent windows. Selected endpoint checks and a coverage audit showed that the current sample contains ample review text for exploratory screening but sparse histories for listing-level and temporal validation. Copied review collections, buyer-selection errors and unavailable reviewer identities were recorded. Context review was assistant-supported and was not an independent gold-standard annotation exercise. The work identified suspected concerns but did not authenticate scam outcomes. No synthetic observations were added to increase the apparent evidence. Real-data enrichment was prioritized; separate synthetic fixtures may be used to test prototype behaviour in deliberately constructed scenarios. Neither generated records nor text-derived indicators substitute for independent validation of real listing outcomes.

## Supporting records

For the subsequent implemented synthetic stage and its report-ready paragraph, use the [synthetic-data methodology](synthetic_data_methodology.md). That stage uses Indian Products on Amazon as its primary source, seeded Python generation and separate empirical-reference/controlled scenarios. Its generated records remain outside the real-data findings summarized above.

- [Technical methods and data dictionary](methods_and_data_dictionary.md).
- [Exploratory research and variable comparisons](research_report.md).
- [Frozen Checkpoint 1](checkpoints/checkpoint_01_low_star_and_text.md).
- [Listing-level validation and case evidence](listing_level_validation.md).
- [Market research and literature review section](market_research_literature_review.md).

The raw download manifests, sample revision and hashes, checkpoint snapshot, analysis scripts and output JSON files provide the corresponding reproducibility records. Later methodological changes should be recorded as a new stage or checkpoint rather than silently rewriting Checkpoint 1.
