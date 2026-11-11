# Amazon India review-risk research

Updated 1 November 2026 for SC4025 Digital Product Management.

Start with [the research report](research_report.md). It covers dataset discovery, measured relationships, the literature review, competitor benchmarking, SWOT and market sizing. [The methods and data dictionary](methods_and_data_dictionary.md) explain the generated columns and evaluation limits.

For the report section dedicated to the market research role, use [Making Amazon India purchases safer](market_research_literature_review_revised.md), with the PDF at `../output/pdf/amazon_india_market_research_literature_review_revised.pdf`. This revised report uses connected prose in the team's voice, links the literature to product choices, aligns the primary dataset with Indian Products on Amazon and includes the implemented synthetic stage. It covers the market need, academic evidence, competitor benchmark, SWOT and a rounded, assumption-based market-size range.

The [original report filename](market_research_literature_review.md) and its PDF at `../output/pdf/amazon_india_market_research_literature_review.pdf` now contain the same plain-English market report, so opening that file also shows the updated wording. The previous versions are saved in `archive/reports_before_plain_english_2026-11-01/`.

For a standalone academic literature-review section, use [Customer reviews and purchase risk](literature_review_purchase_risk.md), with the PDF at `../output/pdf/amazon_india_literature_review.pdf`. This version explains nine academic studies and two consulting reports in plain English, then connects their findings to our feature. References [1]-[11] follow their first appearance in the text. It includes a study of historical rating changes and separates literature findings from the project's proposed rules. The broader revised market-research report remains the source for the competitor benchmark, SWOT and market-sizing scenario.

The agreed star-plus-text method is saved as [Checkpoint 1](checkpoints/checkpoint_01_low_star_and_text.md). The subsequent [listing-level validation](listing_level_validation.md) tests repetition, sampled negative-review shares, context and strength of supporting claims. It distinguishes alleged incidents from independently confirmed scam listings.

The full [methodology and research development record](methodology_and_research_journey.md) documents the approach from the initial dataset search onward, separates user-directed decisions from findings, and includes a report-ready methodology paragraph.

The [ratio and time extension](ratio_and_time_extension.md) defines the low/high-star ratio, proposes trial thresholds and checks dated sample coverage. Time means **within the dataset's historical period**, anchored to each listing's observed endpoint or a chosen historical cutoff, not today's date. Its numeric choices are unvalidated prototype hypotheses; the historical reviews are real source data. Run `python -X utf8 research/analyse_listing_ratio_time.py` to reproduce the JSON audit.

The [synthetic-data methodology](synthetic_data_methodology.md) makes **Indian Products on Amazon the primary source for the synthetic stage**. It records the completed real-data tests, measured calibration patterns, explicit scenario assumptions and Python generation. The default run creates 10,920 reviews across 100 fictional listings for prototype tests. General Amazon Reviews 2023 is a secondary methodological comparison and is not a generation input. Reproduce with `python -X utf8 research/generate_synthetic_indian_products.py`.

## Confirmed starting sources

The user’s `task info.txt` was empty on disk, but its unsaved VS Code editor buffer was subsequently inspected. It confirms **Karkavelraj Aj’s Amazon Sales Dataset** and **McAuley Lab’s Amazon Reviews 2023** as the two starting sources. The Kaggle dataset analysed here is therefore the team’s intended baseline. The additional Indian-products and Mendeley sources were found beyond those starting sources. No original project files or unsaved editor contents have been changed.

## Files to use

- `outputs/amazon_india_augmented.csv`: all 1,465 original listing records and 16 original columns, with separately appended numeric fields, text-rule indicators and provenance. No synthetic records or invented fraud outcomes.
- `outputs/indian_reviews_deduplicated_flagged.csv`: 1,391 distinct source records after exact deduplication; 1,388 have nonempty review text.
- `outputs/manual_annotation_queue.csv`: all 115 rule candidates across the two analysis samples, plus 200 reproducibly sampled non-candidates. Annotation fields are blank; this is a queue, not a labelled test set.
- `outputs/keyword_counts.csv`, `outputs/variable_associations.csv`, `outputs/analysis_summary.json`: computed evidence for the report.
- `outputs/general_amazon_summary.json`, `outputs/general_amazon_keyword_counts.csv`, `outputs/general_amazon_associations.csv`: the separate analysis of bounded Amazon Reviews 2023 samples.
- `outputs/general_amazon_candidate_reviews.csv`: general-Amazon rule candidates with source category/row and blank human/fraud labels. This is not part of the 315-row supplemental/main annotation queue.
- `outputs/general_amazon_exact_asin_overlap.csv`: exact shared ASINs with the India listing dataset, without transferring general-Amazon outcomes into India fraud labels.
- `outputs/general_amazon_india_asin_join.csv`: 39 sampled reviews joined to 21 India listing IDs. Column prefixes preserve which source each variable describes. No joined review triggers a complaint rule, so this overlap cannot support a price-versus-complaint model.
- `outputs/low_star_review_analysis.json`: the proposed 1-2-star-first screen, with separate counts for generic negative wording, authenticity wording and product-mismatch phrases. Reproduce with `python -X utf8 research/analyse_low_star_reviews.py` after preparing the smaller datasets.
- `outputs/listing_evidence_audit.json`: listing-level counts and sampled review context following the frozen checkpoint.
- `outputs/listing_context_audit.json`: an assistant's context review of 116 specific-wording matches, including ambiguity, buyer errors, reported external checks and repeated review collections. No independently confirmed scam labels are assigned.
- `outputs/listing_ratio_time_analysis.json`: selected historical ratio and endpoint-window checks, with the recording date excluded from window definitions.
- `outputs/sample_size_adequacy.json`: review depth by ASIN, ratio-gate coverage and paired historical-window coverage. Reproduce with `python -X utf8 research/audit_sample_size.py`.
- `outputs/synthetic_indian_products/reviews_synthetic.csv`: 10,920 scripted synthetic records at 100 fictional listings, with provenance and scenario metadata.
- `outputs/synthetic_indian_products/reviews_real_and_synthetic.csv`: new combined test file with 1,388 preserved real reviews and 10,920 synthetic reviews. Filter `is_synthetic=0` for empirical findings; pooling both groups does not increase real evidence.
- `outputs/synthetic_indian_products/listing_window_checks.csv`, `calibration_and_validation.json`, `manifest.json`: prototype checks, measured/assumed inputs and input/output hashes. These do not establish real scam-detection accuracy.
- `data/download_manifest.json`: original download endpoints and SHA-256 checksums. Dataset subfolders contain unmodified raw data and publisher metadata.

## Reproduce

From the project root, with Python, pandas and numpy installed:

```powershell
python -X utf8 research/analyse_reviews.py
python -X utf8 research/sample_general_amazon.py
python -X utf8 research/analyse_general_amazon.py
```

The analysis scripts are deterministic and check preservation of original columns, duplicate counts and absence of invented truth labels. They regenerate CSV/JSON outputs from downloaded raw files and do not train a fraud model. Sampling also requires `requests`. The general-Amazon sample takes the first 20,000 records in each of two category files; it is not random. Its manifest records the publisher repository revision and sample hashes. The download script reuses cached complete samples on rerun; a fresh online download may resolve a later publisher revision.

The two raw downloads were obtained from these public Kaggle API endpoints:

- https://www.kaggle.com/api/v1/datasets/download/karkavelrajaj/amazon-sales-dataset
- https://www.kaggle.com/api/v1/datasets/download/nehaprabhavalkar/indian-products-on-amazon

These endpoints return ZIP archives. For a fresh download, save each archive, extract its CSV into its corresponding `data/` subfolder, and compare the file hash to the manifest before expecting identical results.

## Attribution and reuse

The Amazon Sales Dataset is credited to **Karkavelraj Aj**; Kaggle's metadata reports **CC BY-NC-SA 4.0**. Its augmented version remains attributed to that source and is provided for this noncommercial course project under those source terms. The Indian Products on Amazon dataset is credited to **Neha Prabhavalkar**; Kaggle's metadata reports **Data files © Original Authors**, without a clear open reuse grant. This affects redistribution of that raw text; publishing the analysis code does not require publishing the downloaded dataset. The metadata files record these publisher statements. No separate commercial data-use entitlement has been established.

The supplemental dataset is about Indian products on Amazon; its CSV contains no marketplace/country field proving that every review comes from Amazon.in or an Indian resident.
