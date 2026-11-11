# Synthetic Data Methodology

Recorded 31 October 2026. Primary source: **Indian Products on Amazon**. This document records the completed real-data tests, the reason for introducing synthetic scenarios, the generation procedure and the limits of what the generated data can establish. It extends the [research journey](methodology_and_research_journey.md) without changing [Checkpoint 1](checkpoints/checkpoint_01_low_star_and_text.md).

## 1. Purpose and dataset hierarchy

The feature investigates listing-level evidence of suspected counterfeit goods and wrong/not-as-advertised products. The accepted starting screen is an **individual 1–2-star rating plus relevant review wording**, followed by listing concentration, repeated contextual allegations and historical time patterns.

**Indian Products on Amazon is the main dataset for this synthetic-data stage.** Its individual review stars, text, dates and ASINs provide the empirical reference. Amazon Reviews 2023 was a secondary dataset used earlier to exercise the screening and listing-assessment methodology. It is not an input to the synthetic generator and supplies none of its probabilities, dates or product identifiers.

| Dataset | Role in this stage |
| --- | --- |
| [Indian Products on Amazon, Neha Prabhavalkar](https://www.kaggle.com/datasets/nehaprabhavalkar/indian-products-on-amazon) | Primary real data used to measure rating/text screening states and select historical endpoints. |
| [Amazon Reviews 2023, McAuley Lab](https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023) | Secondary methodological exploration and comparison already performed. No records are pooled into generation. |
| [Amazon Sales Dataset, Karkavelraj Aj](https://www.kaggle.com/datasets/karkavelrajaj/amazon-sales-dataset) | Earlier India catalogue exploration only. Its combined text and aggregate ratings cannot supply the individual-review method. It is not the synthetic-data foundation. |

The primary source concerns Indian products on Amazon, but its fields do not prove that every review came from Amazon.in or an Indian resident. The generated data inherits this limitation in its empirical basis. It is not a representative simulation of Amazon India's population.

## 2. What we tried before generating data

We first applied the method to real downloaded data rather than assuming that the available fields would support it. We removed exact duplicate records, excluded missing review bodies from text denominators, inspected stars and text together, and grouped review records by exact ASIN. We preserved all rating groups when calculating listing denominators.

| Real-data test | General Amazon sample | Primary Indian-products sample | What the test established |
| --- | ---: | ---: | --- |
| Usable individual reviews | 39,986 | 1,388 | Both sources can exercise review-level screening. The general sample is a file-prefix convenience sample. |
| Individual 1–2-star reviews | 5,071 | 338 | The rating gate is available, unlike the combined-text India catalogue. |
| Low-star reviews with any selected wording | 309 | 77 | The proposed base can retrieve review candidates. |
| Low-star authenticity/mismatch wording candidates | 74 | 42 | More specific wording narrows the screen, but needs context review. |
| Context-relevant allegations in the assistant audit | 45 | 39 | Some keyword hits concern buyer mistakes, reviews or unrelated meanings. These are assistant judgments, not independent human gold labels. |
| Distinct ASINs in the source sample | 33,779 | 145 | General-Amazon volume is dispersed across many listings. |
| Candidate ASINs with at least 20 non-neutral reviews | 1 of 73 | 0 of 26 | The current samples provide little coverage for the proposed ratio gate. |
| ASINs with ten reviews in each of the latest two 90-day windows | 0 | 0 | The chosen historical endpoint comparison cannot be adequately exercised on these samples. |

Generic wording included waste of money, not good and poor/bad quality. Specific wording included fake/counterfeit/duplicate/not original, wrong item and not-as-described phrases. The actual regular expressions are preserved in `outputs/low_star_review_analysis.json`; the generator reuses them.

We then examined whether a wording match was about the purchased item, whether other sampled reviews supported a similar concern, and whether identical texts or entire collections inflated apparent repetition. In the Indian-products sample, 39 context-relevant low-star reviews comprised **38 authenticity concerns and one description mismatch**. Nine ASINs had at least two distinct relevant texts, representing eight distinct collection families. No independent authentication or confirmed fraud outcome was obtained.

We also applied the ratio and endpoint-window method to selected real cases. For example, general-Amazon ASIN `B01415QHYW` has ten low-star, one neutral and 27 high-star sampled reviews. Its bounded low-star share is 10/37 = 27.03%, passing the trial 25% concentration threshold, but only one of its two wording hits was judged a clear target allegation. Its latest historical 90-day window has three positive reviews and its preceding window has none. This illustrates both the distinction between concentration and corroboration and the need to report insufficient historical coverage.

**Why these tests matter:** they show that the procedure is implementable and reveal its failure modes. They do not show that the base, 25% threshold or temporal rule accurately classifies real scams. Applying a method successfully means obtaining reproducible measurements, not confirming the central fraud hypothesis.

## 3. Why introduce synthetic data now?

The primary source has 2,782 raw rows, 1,391 after exact deduplication and **1,388 nonempty reviews across 145 ASINs**. Of these ASINs, 132 have exactly ten usable reviews. None has 20 usable reviews. It provides real language and rating examples, but insufficient depth to explore a well-covered before/after transition for an individual listing.

Synthetic data is therefore introduced to **exercise the prototype under controlled listing histories**. It lets us test whether the implementation distinguishes isolated concerns, repeated allegations, generic dissatisfaction, copied complaints, recovery and inadequate coverage. It also makes a historical change scenario inspectable without fabricating observations about a real product.

The design has two components:

1. **An empirical reference scenario:** resample rating/text-state pairs measured from the primary data. This checks approximate preservation of those limited distributions.
2. **Controlled scenarios:** deliberately alter counts and text-state composition to create specific software tests. The change rates and history lengths are engineering assumptions, not estimated counterfeit rates.

The synthetic rows do not increase the empirical sample size. The real evidence remains 1,388 usable primary reviews. Real-data enrichment remains necessary for validating actual listing risk.

## 4. Division between AI design and scripted generation

AI assistance was used to reason about the method, interpret the existing context audit, choose test scenarios, draft reusable text templates and implement the generator. The earlier assistant context judgments remain provisional and are recorded as such.

**Bulk generation is ordinary Python, not an AI call for each row.** The script uses the standard library: `csv`, `json`, `random`, `datetime`, `collections`, `hashlib`, `re`, `pathlib` and `argparse`. The default random seed is **4025**. No language-model API, paid generation service or network request is made during generation.

The script expands a finite template bank using loops and short prefix/suffix variations. This is reproducible and avoids spending generation tokens on thousands of rows. The resulting templated text is suitable for prototype and edge-case tests; it is not intended to substitute for natural review-language diversity in model training.

## 5. Real-data preparation and calibration

The generator reads the prepared Indian-products file and the saved rules/context audit. It never overwrites the raw source, prepared empirical file or original checkpoint.

| Source rating | Real review count | Share of 1,388 |
| --- | ---: | ---: |
| 1 star | 273 | 19.67% |
| 2 stars | 65 | 4.68% |
| 3 stars | 99 | 7.13% |
| 4 stars | 230 | 16.57% |
| 5 stars | 721 | 51.95% |

The generator records a **joint state consisting of the actual star rating and a text screening class**, rather than drawing stars and issue wording independently. State assignment follows this precedence:

1. A low-star review judged context-relevant in the saved audit becomes an authenticity-concern or mismatch-concern state.
2. Other reviews with specific regex wording become an unresolved/ambiguous-specific-wording state. This includes the three excluded low-star matches and 13 above-two-star matches whose contexts were not independently reviewed.
3. Other selected wording becomes a generic-dissatisfaction screening state.
4. Remaining reviews are grouped as other negative, neutral or positive using their stars.

These are operational screening states, not a fully annotated sentiment corpus. In particular, the generator's ambiguous templates deliberately describe non-target meanings; this does not establish that every unreviewed real match was irrelevant.

The measured state counts are 38 authenticity concerns, one mismatch concern, 16 ambiguous-specific-wording states, 45 generic-dissatisfaction states, 261 other negatives, 92 neutral states and 935 positive states. The empirical reference resamples complete rating/state pairs with replacement. This preserves their empirical association in expectation; finite samples will differ.

For controlled scenarios, the split between one and two stars is drawn from the primary data's low-star ratings, and the split between four and five stars is drawn from its high-star ratings. The numbers of low, neutral and high reviews are deliberately assigned by the scenario.

### Collection duplication and profile selection

A new full-corpus check compared complete collections using sorted date, rating and normalized-text tuples. It identified **125 distinct collection families across 145 ASINs**, including 20 pairs with identical collections. This extends the earlier candidate-only duplication audit.

The pooled 1,388-review calibration retains these collections, so its frequencies describe the prepared source and must not be interpreted as independent population estimates. For selecting historical anchors, the generator uses one representative ASIN per identical collection family, giving each eligible family equal selection weight. The copied collections and representative-family rule are saved in the calibration output.

The referenced ASIN supplies a historical endpoint only. Rating/text states are pooled across the primary data; generated complaints do not describe that referenced product. Every generated listing has its own fictional identifier and name.

## 6. What is empirical and what is assumed?

| Element | Basis |
| --- | --- |
| Original five-column schema: ASIN, name, date, rating, review | Observed in the primary source. |
| Five-star rating distribution and joint rating/screening-state frequencies | Measured from the 1,388 prepared primary reviews. |
| Authenticity wording, general dissatisfaction and a description-mismatch example | Observed in the primary data, with the context limitations above. |
| Historical endpoint candidates and overall date bounds | Observed in the primary data: 12 April 2015 to 6 October 2020. |
| Ten scenario types and ten fictional listings per type | Chosen for test coverage; not inferred real scenario prevalence. |
| Sixty reviews per phase for dense histories | Chosen so coverage gates can be exercised. It is not a reconstruction of missing reviews. |
| Stable and surge rating allocations | Controlled assumptions, defined below. |
| Abrupt transition at the boundary between two windows | Constructed intervention. No real transition has been authenticated. |
| Wrong-product, wrong-brand and wrong-size surge examples | Deliberate extension of the project's mismatch scope. Only one relevant real mismatch was found, concerning description information; these subtype frequencies cannot be estimated from it. |
| Uniform day placement and prefix/suffix text variation | Scripted convenience assumptions, not learned seasonality or language models. |
| Synthetic users and intended text classes | Fictional test metadata. The real primary source supplies no reviewer identities. |

No seller history, purchase verification, helpful votes or authentication evidence is imputed. Those missing variables remain outside the generator's claim.

## 7. Scenario construction

The default run creates **100 fictional listings and 10,920 synthetic reviews**. Nine scenario types have ten listings with 120 reviews each. The sparse-history type has ten listings with 12 reviews each. Equal allocation makes each test visible; aggregate synthetic flag rates have no market interpretation.

For a dense controlled listing, a stable phase has **6 low-star, 4 neutral and 50 high-star reviews**. A surge phase has **36 low-star, 4 neutral and 20 high-star reviews**. A target surge assigns 24 of the low-star reviews to its specified wording class; the remaining 12 express generic dissatisfaction. A sparse listing has six reviews per phase.

| Scenario | Construction | Purpose |
| --- | --- | --- |
| Empirical reference | Independently resample 60 real rating/state pairs for each phase. | Check approximate rating-state preservation and expose variation without a constructed change. |
| Stable positive | Stable allocation in both phases; no target concerns. | Check that mostly positive histories do not automatically escalate. |
| Isolated concern | Stable allocation in both phases; one recent authenticity concern. | Retain a single concern without calling it repeated corroboration. |
| Authenticity surge | Stable earlier phase; recent surge with 24 authenticity-concern reviews. | Exercise the base, ratio and dated wording-increase mechanics. |
| Mismatch surge | Stable earlier phase; recent surge with 12 description and 12 wrong-item-type concerns. | Exercise the second project category. Its subtype mix is assumed. |
| Generic quality surge | Stable earlier phase; recent surge consisting of generic quality complaints. | Show that a high low-star share alone need not indicate counterfeits or mismatch. |
| Historical recovery | Earlier authenticity-concern surge; stable recent phase with no target concerns. | Distinguish a whole-history ratio from a more positive recent historical period. This is not an authenticity guarantee. |
| Sparse history | Earlier 1 low/5 high; recent 4 low/2 high, including three authenticity concerns. | Ensure insufficient counts remain unavailable despite concerning-looking proportions. |
| Copied complaint burst | Recent surge with 24 copies of the same authenticity text under one fictional account. | Show that many rows can represent only one distinct text/account. |
| Context-trap burst | Recent surge with 24 low-star keyword uses about fake reviews, negation, buyer selection or comparisons. | Expose false positives in literal wording rules. |

All text is generated for fictional products named `Synthetic product profile ...`. Identifiers begin `SYNTH_IPA_`. No fabricated negative experience is attached to a real ASIN or brand.

## 8. Historical time construction

Time always refers to the source's historical period. For a synthetic listing, choose T from the last observed review date of an eligible primary-source collection. Its earlier dates must fit inside the primary source's observed date range.

- Recent window: **(T − 90 days, T]**.
- Previous window: **(T − 180 days, T − 90 days]**.
- Recent offsets are uniformly sampled from 0–89 days; previous offsets from 90–179 days.
- One recent record is placed exactly on T, making the declared endpoint observable.

The first boundary is excluded and the last included, preventing overlap. Dense histories contain 60 records in each window; sparse histories contain six. The generator checks that all synthetic dates remain within **2015-04-12 to 2020-10-06**. The 2026 recording date is never a cutoff.

This design imposes two balanced windows and does not reproduce observed review spacing, seasonality, sales volume or the true beginning of a product's history. A future historical prediction test must use successive predetermined cutoffs and prevent later reviews from influencing earlier flags.

## 9. Applying the methodology to the generated records

The generated reviews are screened using the existing regex rules and their assigned stars. The listing checker calculates all-rating denominators, low/high counts, bounded low-star shares, specific-wording counts, distinct normalized wording texts and distinct fictional accounts.

Let L be 1–2-star reviews, H be 4–5-star reviews and N include all stars. The ratio threshold uses **L/(L+H)**, with 3-star reviews reported separately. Threshold sensitivity is reported at **20%, 25% and 30%**, with at least 20 non-neutral reviews required. These remain unvalidated prototype choices.

For time, calculate specific-wording matches divided by N in each historical window. Report the recent-minus-previous change in **percentage points** only when both windows contain at least ten reviews. A descriptive wording-increase indicator requires a positive change and at least two distinct recent specific-wording texts. It has no validated minimum effect size or significance claim. Unavailable comparisons are blank/null, never automatically safe.

**The checker uses observable stars and wording for these flags. It does not use the intended text class, scenario name or synthetic phase to decide a flag.** The intended class is retained separately to expose construction-based errors. Dates, rather than the supplied phase label, determine window membership.

This is a keyword-based implementation of the screening stage. It does not implement an independently validated contextual classifier. Consequently, context-trap cases can trigger the wording-increase indicator even though their constructed meaning is irrelevant. The copied-text case is suppressed by the distinct-text repetition requirement, but copying with small paraphrases would require stronger duplication handling.

## 10. Results of the default scripted run

The reproducible seed-4025 run produced:

| Result | Count |
| --- | ---: |
| Synthetic listings | 100 |
| Synthetic reviews | 10,920 |
| Preserved real reviews in the combined export | 1,388 |
| Total records in the combined export | 12,308 |
| Empirical reference reviews, included in the synthetic total | 1,200 |

In the empirical reference, the five star shares differ from the real source by at most **1.84 percentage points**. This is a descriptive marginal comparison, not proof of broad realism. The generator preserves only selected rating/state relationships and does not model the complete review distribution.

| Pattern, as a share of all review records | Real primary source, N=1,388 | Synthetic empirical reference, N=1,200 |
| --- | ---: | ---: |
| Individual 1–2-star review | 24.35% | 25.67% |
| Low-star plus any selected wording | 5.55% | 5.92% |
| Low-star plus specific authenticity/mismatch wording | 3.03% | 3.50% |

This comparison uses only the empirical reference. The complete synthetic set deliberately overrepresents constructed problems, so its aggregate proportions should not be expected to match the source. The generated dates in this default run span 31 May 2018 to 5 October 2020, within the wider observed source bounds.

The controlled checks behaved as designed: all ten authenticity-surge and all ten mismatch-surge listings show both elevated negative concentration and increased repeated specific wording. All ten generic-quality-surge listings pass the 25% ratio rule but have zero specific-wording matches. The isolated-concern cases have one specific match each and do not pass the ratio threshold. Sparse histories return unavailable ratio/time conclusions. The copied bursts contain 24 keyword-matching rows each but only one distinct matching text and one fictional account.

Two findings limit interpretation. First, **three of ten stationary empirical-reference listings** show a descriptive wording increase with repetition despite no constructed change. Random variation alone can trigger the direction-only test. Second, **all ten context-trap listings** trigger that keyword indicator while containing no constructed target allegation. These results motivate context validation, uncertainty assessment and stronger temporal criteria. They do not measure real false-positive rates.

Ten historical-recovery cases retain an elevated whole-history ratio but show a 40-percentage-point fall in specific wording between the two constructed windows. This illustrates why historical concentration and temporal direction should be reported separately.

## 11. Files, schema and how to use them

The [synthetic-only CSV](outputs/synthetic_indian_products/reviews_synthetic.csv) contains the generated records. The [combined CSV](outputs/synthetic_indian_products/reviews_real_and_synthetic.csv) appends them to the 1,388 usable real reviews in a new file. All five original column values are preserved for real rows. The original source and prior empirical outputs remain intact.

| Field or group | Meaning |
| --- | --- |
| `asin`, `name`, `date`, `rating`, `review` | Original schema retained. Synthetic rows use fictional identifiers, names and constructed values. |
| `is_synthetic` | 0 for a real source record; 1 for a generated record. Always filter this field before empirical analysis. |
| `source_dataset`, `review_record_id` | Provenance and record identity. |
| `screen_low_star`, `screen_any_wording`, `screen_specific_wording` | Derived screening indicators from stars/text. They are not fraud labels. |
| `synthetic_scenario`, `synthetic_phase` | Construction metadata. Exclude from model inputs and independent evaluation features. |
| `synthetic_intended_text_class` | Template meaning assigned by construction. It does not authenticate a product outcome. Blank for real rows. |
| `synthetic_reviewer_id` | Fictional account used for test independence/duplication cases. No identities are invented for real rows. |
| `synthetic_template_family` | Text-generation family. Useful for preventing template leakage. |
| `synthetic_reference_asin`, `synthetic_reference_collection_family` | Primary-source endpoint provenance. They do not transfer simulated complaints to a real product. |
| `synthetic_dataset_cutoff`, `synthetic_seed`, `synthetic_generation_method` | Historical endpoint and reproduction metadata. |
| `fraud_ground_truth` | Blank throughout. No confirmed-scam outcomes are generated. |

Supporting outputs are [listing/window checks](outputs/synthetic_indian_products/listing_window_checks.csv), [calibration and validation results](outputs/synthetic_indian_products/calibration_and_validation.json) and the [input/output checksum manifest](outputs/synthetic_indian_products/manifest.json).

For observed-data findings, select **`is_synthetic=0`**. For prototype scenario testing, select **`is_synthetic=1`**. Never calculate a market scam rate or confidence interval by pooling both groups. The combined file is a convenient test input, not an enlarged observational study.

## 12. Reproduction and validation

From the project root:

```powershell
python -X utf8 research/generate_synthetic_indian_products.py
```

The script uses the existing prepared source and saved audit outputs; these are already present in the project. It requires no third-party Python packages. Optional arguments are `--seed`, `--listings-per-scenario` and `--output-dir`. For example, `--listings-per-scenario 20` doubles scenario coverage, not real evidence.

The implementation checks identical-seed reproduction, unique synthetic record IDs, disjoint real/synthetic listing IDs, valid dates, preserved real values, correct window counts, unavailable sparse comparisons, constructed scenario expectations and blank fraud labels. It verifies that raw/prepared inputs and Checkpoint 1 retain their hashes. The manifest records SHA-256 values for inputs, generator code and outputs.

These checks establish reproducibility and intended software behaviour. They do not validate representativeness, review authenticity or a real-world scam probability.

## 13. Appropriate use and next empirical step

Use the generated histories for demonstration, integration tests, denominator/window checks, missing-data behaviour, duplicate handling and comparisons between generic dissatisfaction and target wording. Document any changes to assumptions and regenerate from a recorded seed.

Do not use this templated scenario set as the sole training or test corpus for a fraud classifier. A model could learn the templates, constructed rating rules, fictional identifiers or scenario metadata. Successful performance would then reflect the generator's design. The equal scenario frequencies and synthetic temporal changes cannot calibrate real risk.

If augmentation is later used in training, split independently labelled real data first, group related ASINs, copied collections and near-duplicate text, and keep generated rows in training only. Evaluate on untouched real examples, with later-time and India-specific evaluation where available. Complaint-allegation labels and authenticated outcomes must remain separate targets.

The next empirical priority is still denser real histories for selected Indian-product listings and comparison listings, preserving all stars and dates. Independent text annotation is needed to evaluate allegation screening; independent item/order evidence is additionally needed to substantiate counterfeit or mismatch outcomes. Seller-specific claims require seller/offer histories absent from the primary source.

## Report-ready methodology paragraph

We first applied the proposed review-screening methodology to real review data, using individual one- and two-star ratings followed by negative and issue-specific wording. Amazon Reviews 2023 supplied a secondary methodological check, while Indian Products on Amazon was selected as the primary source for synthetic-data construction. The latter yielded 1,388 usable reviews across 145 ASINs after cleaning. Context inspection separated generic dissatisfaction, relevant authenticity or description-mismatch allegations and ambiguous wording. Listing-ratio and historical-window audits showed that sparse per-listing histories limited the testing of temporal changes. We therefore created a separate, reproducible simulation using Python scripts. An empirical reference resampled observed rating/text-screening-state pairs, and controlled scenarios represented isolated concerns, authenticity and mismatch surges, generic quality deterioration, recovery, copied complaints, ambiguous wording and sparse coverage. Synthetic dates remained within the primary source's historical range, with explicit earlier and recent windows. AI assisted the design and template preparation; bulk generation used seeded code without per-record language-model calls. Generated listings used fictional identifiers, and provenance fields separated real observations from synthetic records. The default run produced 10,920 synthetic reviews across 100 fictional listings. These records tested prototype mechanics and revealed limitations of ratio-only and literal-wording rules. They did not increase the empirical evidence, establish real scam prevalence or provide independently verified fraud outcomes.
