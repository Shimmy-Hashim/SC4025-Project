# Backend: offline rule-based scoring pipeline

Python reads the synthetic seller inputs, applies the scoring rules and writes `data.json` at the repo root. The frontend reads that file unchanged. There is no server or live API, and no machine learning.

```
inputs/demo_listing.json ─┐
inputs/demo_reviews.csv  ─┴─▶ trust_score (rules) ──▶ ../data.json ──▶ index.html + app.js
```

## Run it

Python 3.10+ is needed. The pipeline itself uses only the standard library, and pytest is needed for the tests. From the repo root:

```bash
python3 -m venv .venv && .venv/bin/pip install pytest
cd backend
../.venv/bin/python generate_demo_listing.py          # regenerate inputs/ (seeded, deterministic)
../.venv/bin/python -m trust_score.cli build          # score sellers A-D, write ../data.json
../.venv/bin/python -m trust_score.cli validate ../data.json
../.venv/bin/python -m trust_score.cli check-synthetic  # rule behaviour on the research scenarios
../.venv/bin/python -m trust_score.cli screen         # real-data screen (needs the raw dataset, below)
../.venv/bin/python -m pytest
```

`build` checks its own output with the same rules as `validate()` in `app.js` and refuses to write an invalid file.

### Live demo: edit inputs and re-score

```bash
../.venv/bin/python -m trust_score.cli serve      # then open http://localhost:8000
```

`serve` serves the site the way `http.server` does and adds two local endpoints. `GET /api/inputs` returns each seller's editable inputs. `POST /api/score` applies edits and scores them with the same rules as `build`. An **Edit seller inputs** button then appears in the yellow demo bar. A tester can change a seller's price, days selling, feedback %, brand authorisation and recent complaints, or add 1★ "fake item" reviews, and watch the band change. Edits are scored in memory: `data.json` is never rewritten, and reloading the page resets everything. The server listens on 127.0.0.1 only. With a plain static server (or GitHub Pages) the button stays hidden and the page works as before.

## Layout

| Path | Purpose |
| --- | --- |
| `trust_score/config.py` | Every threshold, weight and regex. **Change rules here only.** |
| `trust_score/constants.py` | All shopper-facing wording |
| `trust_score/review_screen.py` | Allegation screen, low-star share, 90-day trend, copy handling |
| `trust_score/factors.py` | The five factors (abstract `Factor` base and one subclass each) |
| `trust_score/scoring.py` | Gates, score, band, cap, inline factors |
| `trust_score/export.py` | Builds `data.json`, and a Python copy of `validate()` from `app.js` |
| `trust_score/loaders.py`, `cli.py` | Input reading and commands |
| `generate_demo_listing.py` | Synthetic iPhone listing (sellers A-D) |
| `research/` | The team's research scripts, docs and outputs (Checkpoint 1, synthetic generator) |
| `reports/` | Outputs of `screen` and `check-synthetic`, for report section 5 |

## Scoring rules

Every factor separates **missing evidence** from a **concern** and a **serious alert**, so that stronger evidence counts for more. The rules are based on the team's research, the user stories and the [scoring basis review](https://claude.ai/code/artifact/83e35b29-ea38-4a5f-a6e7-8fc45710071f). Values marked **[provisional]** are documented assumptions that still need data.

### Decision order (`trust_score/scoring.py`)

1. **Check the evidence.** Exact duplicate reviews are removed, copied allegation texts count once, and complaints count once per affected order.
2. **Collect serious alerts.** They are shown prominently (`alert` in data.json) even when the offer isn't scored.
3. **Gate.** Under 90 days of history, under 20 reviews, or 2 or more unknown factors gives `Not enough data`. If an alert exists, the reason ends with "See the alert above." instead of "This is not a warning."
4. **Any serious alert gives Low**, whatever the other factors say.
5. **Weighted score**, with unknown (`na`) factors left out rather than counted as 0. High is 75 or more and Medium is 50 or more **[provisional]**. A **concern on price, reviews, complaints or brand** limits the band to Medium.

### Factors

| Factor | Unknown (`na`) | Pass | Concern | Serious alert |
| --- | --- | --- | --- | --- |
| Price (against the median of other offers, leaving out offers more than 70% below the listing median) | Fewer than 2 comparable offers | Within the threshold | More than 30% below **[US4]** | More than 70% below **[provisional]** |
| Seller history | Under 90 days, no feedback, or **under 20 ratings** **[provisional]** | 90%+ positive and order defect rate under 1% | Under 90% positive **[provisional]**, or order defect rate of 1% or more (Amazon's published target) | None in the MVP |
| Brand (Brand Registry Reseller role, assigned by the brand owner) | **Not verified**: no record | Verified | **Confirmed** not authorised | The seller claims authorisation and the brand denies it |
| Reviews (stage 2 interpreted allegations) | Fewer than 20 reviews | No allegation, or one isolated allegation | 2+ distinct allegations within 365 days **[provisional]**, or a low-star share of 25% or more with an allegation | None: reviews are reports, not findings |
| Complaints (customer service, separate from reviews) | **No complaints data** (not the same as zero), or under 90 days | 0–1 affected orders, or 2+ at under 0.5% of orders **[provisional]** | 2+ affected orders | A confirmed counterfeit finding within 365 days |

Seller age only decides whether there is enough evidence. It never warns by itself.

### Review screen in two stages

- **Stage 1 (frozen):** the Checkpoint 1 regexes on 1–2★ reviews. `screen` and `check-synthetic` use this stage to reproduce the research exactly: 42 candidates on the real data.
- **Stage 2 (context):** phrases the research context review rejected ("fake reviews", "not fake", "duplicate of", "I ordered the wrong") are removed, and the specific rules run again on what is left. On the real data, 42 candidates become 39. Against the AI assistant's context labels, which are **not independent** and are the same source the phrases came from, precision rises from 39 of 42 to 38 of 39 for Indian products and from 45 of 74 to 45 of 70 for the general sample. One real allegation is lost ("felt like duplicate of titan"). The patterns were deliberately not tuned further on these labels.

### Weights

The proposed swing weights are reviews 29, complaints 26, price 17, brand 16 and history 12, awaiting the team lead's decision. See [docs/weights.md](docs/weights.md) for the method, the reasoning and the effect on bands. Equal weights are the documented fallback.

| Seller | history | brand | price | reviews | complaints | Score | Band | Alert |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A NovaMobile | pass | pass | pass | pass | pass | 100 | High | – |
| B Metro Phone Hub | pass | concern | pass | concern | pass | 55 | Medium | – |
| C QuickDeal | concern | concern | concern | concern | concern (3 of 38 orders) | 0 | Low | – |
| D FreshTech | na | na | pass | na | na | null | Not enough data | – |
| E MegaSteal (₹4,999) | na | na | **alert** | na | na | null | Not enough data | Extreme price: 99% below |

## What the checks show and do not show

| Check | Result | What it does not show |
| --- | --- | --- |
| `screen` on Indian Products on Amazon | Stage 1 reproduces the research exactly: 1,388 reviews, 145 ASINs, 338 low-star, 77 any-wording, 42 specific-wording. Stage 2 keeps 39 | Which seller sold each item; the real accuracy of either stage |
| `check-synthetic` on 100 scenario listings | Stage 1 flag counts match the research in all 10 scenarios; outcomes behave as designed | Real-world accuracy. `context_trap_burst` now passes only because its templates use the phrases stage 2 was written for |
| Demo sellers A–E | Exercise every state, including an alert on an unscored seller | Anything empirical: all seller data is fictional |

None of these measures how accurately the rules detect counterfeits. The score is guidance, not a guarantee.

### Known limitations

- **Wording:** stage 2 handles only known phrasings. "Wrong size" complaints where the buyer may be at fault still match.
- **Old allegations:** they stay eligible for 365 days, so a recovered seller still warns **[provisional]**.
- **Thresholds:** the 70% alert boundary and the complaint-rate threshold need data on legitimate discounts and real complaint rates.
- **Mock data:** brand status, order defect rate, order counts and complaints are all mock.
- **Not handled:** promotions, instalment or trade-in prices, account takeover, and the region or expiry scope of an authorisation are documented as future work.

## Data and licensing

`research/data/` (the raw datasets) and every research output that contains real review text are gitignored. Indian Products on Amazon is marked "Data files © Original Authors" with no redistribution grant. To run `screen`, download the dataset from the Kaggle link in `research/README.md` into `research/data/indian-products-on-amazon/` and check its SHA-256 against `research/data/download_manifest.json`. `check-synthetic` needs only the committed synthetic CSV.
