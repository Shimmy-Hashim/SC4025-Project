# 5. Tech stack and functional MVP (draft)

*Draft for the report. About 2 pages at font 11 with 1.5 spacing. Numbers come from `backend/reports/` and the test suite. Items marked [sign-off] need team agreement before submission.*

## a. Architecture and tech stack

The MVP is an **offline rule-based scoring pipeline** with a static frontend. A Python program reads the seller and review inputs, applies the scoring rules and writes one file, `data.json`. The web page reads that file and draws the buy box, the "Why this score" panel, compare offers and the cart. There is no live server or API, and no machine-learning model. Both choices follow the MoSCoW scope: live Amazon data and ML scoring are listed under "Won't have".

| Layer | Technology | Why |
| --- | --- | --- |
| Scoring | Python 3, standard library only | Deterministic, easy to audit, no install beyond Python |
| Data contract | One JSON file (`data.json`) | The frontend and backend can be built and tested separately |
| Frontend | HTML, CSS, vanilla JavaScript | Matches the Figma hi-fi frames and runs on any static host |
| Tests | pytest (228 tests) | Boundary and scenario coverage for every rule |

Keeping the rules in Python and the display in JavaScript means the scoring can change without touching the page. Every threshold and weight lives in a single file, `config.py`.

## b. MVP implementation

Each seller offer is assessed on five factors. Each factor reports *unknown*, *pass*, a *concern* or a *serious alert*, along with a plain-language explanation and its source (US3). Strength of evidence matters as well as direction: an offer 31% below other sellers and a ₹4,999 iPhone should not count the same.

- **Seller history:** positive feedback, number of ratings and order defect rate, against Amazon's published target of under 1%. Age only decides whether there is enough history to judge; it is never a warning by itself.
- **Brand authorisation:** the Reseller role a brand owner assigns in Brand Registry. "Not verified" counts as unknown, "confirmed not authorised" is a concern, and a seller claiming authorisation that the brand denies is a serious alert.
- **Price:** compared with the median of other offers, leaving out extreme outliers. A price more than 30% below is a concern (US4); more than 70% below is a serious alert ("Extreme price, verify this offer").
- **Review patterns:** 1-2★ reviews matching the research's frozen wording rules (stage 1), after removing phrases our context review found misleading, such as "fake reviews", "not fake" and "duplicate of" (stage 2). Two or more distinct allegations are a concern. Up to five supporting reviews are shown (US7).
- **Past complaints:** customer-service authenticity complaints, counted once per order and read against order volume. Missing complaints data counts as unknown, not as zero. A confirmed counterfeit finding is a serious alert.

The band is decided in a fixed order. Any serious alert gives Low, and the alert is shown even when the seller is too new to score. A concern on price, reviews, complaints or brand prevents High. Only then does a weighted score (0–100, not shown to shoppers, US2) choose the band, with unknown factors left out rather than counted as zero. The weights (reviews 29, complaints 26, price 17, brand 16, history 12) are team-derived through swing weighting, following UK government MCDA guidance: each factor is rated by how much moving it from a concern to a good state matters. They are judgements, not estimates. Equal weights were the documented fallback, and the two schemes disagree on 17 of the 112 possible factor combinations. [sign-off]

Sellers with under 90 days of history or fewer than 20 reviews receive "Not enough data", with a neutral one-line reason and no warning wording (US6). Following the updated US6, a serious alert stays visible even then. The demo listing has five synthetic sellers that cover every state: A is High, B is Medium, C is Low, D is Not enough data, and E is Not enough data with an extreme-price alert.

## c. Security and quality

- The page writes all data with `textContent`, never `innerHTML`, so backend text cannot inject markup.
- The backend runs the same checks on its output as the frontend's validator and refuses to write an invalid file.
- Raw review data with no redistribution grant is kept out of the public repository. Only code, synthetic data and aggregate results are committed (see 6d).
- The scoring is deterministic: the same inputs always give the same output, and the test suite checks this.

## d. Prototype testing and validation

| Test | What it shows | Result |
| --- | --- | --- |
| Real reviews (Indian Products on Amazon) | The backend's review screen reproduces our research exactly | 1,388 reviews, 145 products, 338 low-star, 77 any-wording, 42 authenticity/mismatch candidates |
| 100 synthetic scenario listings | The rules behave as designed in each situation | Flag counts match the research in all 10 scenarios, and every expected outcome holds |
| Unit and boundary tests | Edge cases such as exactly 30% and 70% below, exactly 20 reviews, complaints per order, and alerts on unscored sellers | 228 passing |
| Demo sellers A-D in the browser | User stories US1-US8 work end to end | [to confirm: run the US1-US8 checklist in the browser and add screenshots] |

These results show that the rules are **reproducible and behave as intended**. They do not measure how accurately the rules detect counterfeits in the real world. The public datasets do not record which seller sent each item, and no reviews have independently confirmed counterfeit outcomes. One limitation is known and documented: the keyword rules cannot read negation, so "this is not fake" is flagged. Our research's AI-assisted context review reduced the 42 candidates to 39 for this reason. Before any real use, a context step and testing against independently labelled reviews would be needed.

## e. Source code repository

<https://github.com/Shimmy-Hashim/SC4025-Project>. The frontend is in the repo root. The backend, tests and research scripts are in `backend/`. To regenerate the data, run `cd backend && python -m trust_score.cli build`.
