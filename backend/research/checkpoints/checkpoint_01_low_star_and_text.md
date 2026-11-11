# Checkpoint 1 Low star ratings and review wording

Accepted working approach on 31 October 2026:

1. Screen **individual reviews rated 1 or 2 stars**.
2. Inspect their wording, including waste-of-money, not-good, poor-quality, authenticity and item/description-mismatch terms.
3. Keep generic dissatisfaction separate from counterfeit and wrong/not-as-described allegations.

The frozen JSON snapshot is `checkpoint_01_low_star_and_text.json`. It contains exact rules and the computed sample counts: 5,071 low-star general-Amazon reviews; 309 selected-wording matches, including 74 authenticity/mismatch wording candidates. The supplemental Indian-products corpus has 338 low-star reviews, 77 selected-wording matches and 42 authenticity/mismatch candidates.

These figures are keyword-screen results, not validated complaint labels or verified scam outcomes. The India Kaggle listing aggregate rating cannot substitute for an individual review rating. No synthetic data was generated.

The next step is separate: aggregate evidence by listing and inspect the context, repetition, sample coverage and strength of each allegation. Context review may reject a match without changing this historical checkpoint. It must not silently relabel the original keyword counts as confirmed cases.
