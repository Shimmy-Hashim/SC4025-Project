# Amazon India purchase-risk feature: market research and literature review

Prepared for SC4025 Digital Product Management, 31 October 2026.

## Main conclusion

There is enough real data to build an **exploratory product-listing complaint detector** and demonstrate relationships between review wording and other variables. There is not enough evidence in the inspected datasets to estimate the probability that a particular seller will deliver a counterfeit or intentionally misrepresent an item.

Use two separate complaint types: **suspected counterfeit** and **wrong/not-as-described item**. Keep generic dissatisfaction separate. An allegation in a review, an independently confirmed counterfeit and deliberate seller fraud are different outcomes.

The project's two starting sources are the **Amazon Sales Dataset** and **Amazon Reviews 2023**. This review evaluates both and identifies additional data. The project brief requires literature to justify product choices; the evidence-to-decision links below connect the research to the proposed feature.

## 1. Dataset discovery and suitability

| Dataset and source | What is available | Decision for this project |
| --- | --- | --- |
| [Amazon Sales Dataset — Karkavelraj Aj](https://www.kaggle.com/datasets/karkavelrajaj/amazon-sales-dataset) | Download inspected: 1,465 rows, 16 columns, 1,351 distinct product IDs. Prices, discounts, listing rating/count, categories and combined review text. All 1,465 product links use Amazon.in. | Confirmed starting source. Use for listing-level text and metadata exploration. No seller IDs, individual review stars/dates or verified fraud labels. The title does not imply transaction-level sales data. |
| [Indian Products on Amazon — Neha Prabhavalkar](https://www.kaggle.com/datasets/nehaprabhavalkar/indian-products-on-amazon) | Download inspected: ASIN, product name, review date, star rating and review text. 2,782 rows reduce to 1,391 after exact deduplication; 1,388 contain text. Source contains 145 ASINs. | Useful additional corpus linking individual review wording to stars. Dates span April 2015–October 2020. Indian-product scope does not prove all reviews originate from Amazon.in or Indian residents; marketplace/country fields are absent. |
| [Amazon Reviews'23 — McAuley Lab](https://amazon-reviews-2023.github.io/) | Publisher documents 571.54 million reviews, review stars/text, timestamps, purchase verification, helpfulness and product metadata. Product metadata joins use `parent_asin`; listed prices are in USD. | Confirmed starting source. A bounded 40,000-record review sample was downloaded and analysed separately; see section 2.5. Do not present it as India-only or assume `store` identifies the seller responsible for an order. |
| [Amazon extraction dataset — Mendeley Data, version 2](https://data.mendeley.com/datasets/2pv6d8fz7y/2) | Publisher describes 5,035 Amazon India reviews, with text, stars, helpful votes, date/country, and explicitly only 3–5-star reviews. Published 6 September 2026; CC BY 4.0. | Additional India lead, but unsuitable as the primary complaint corpus because 1–2-star reviews are excluded. Publisher description reviewed; file contents not independently audited. No counterfeit truth label is documented. |

The two Kaggle datasets were downloaded through their public API. Raw files, publisher metadata and checksums are retained locally. **New sources beyond the task file are Indian Products on Amazon and the Mendeley dataset.** Amazon Sales and Amazon Reviews 2023 were already provided and are not counted as new discoveries.

**Matching result:** exact comparison of the main dataset's `product_id` with the supplemental dataset's `asin` found **zero overlapping product IDs**. Analyse the two datasets separately. Category similarity can motivate a transfer experiment; it cannot justify attaching one product's price, seller or label to another product.

## 2. What the actual data shows

### 2.1 Cleaning and the meaning of a row

The main export retains all 1,465 original rows. Product comparisons use the first source-order row for each of 1,351 ASINs, removing 114 extra records with repeated product IDs. This choice is deterministic, not evidence that the first row is the latest observation.

Main-dataset `review_content` combines several reviews in one field. Its rating is a **listing aggregate**, not a rating for each piece of text. Splitting on commas would corrupt review boundaries. The supplemental file supplies individual review stars, so it supports a different and more direct text–rating comparison.

The supplemental source has 1,391 exact duplicate rows: half its raw records. Removing those duplicates and excluding three empty review bodies leaves 1,388 texts for analysis. This correction prevents obvious double counting; it does not establish independence between reviewers or variants.

### 2.2 Keyword screening

Case-insensitive rules searched only review bodies. Indicators measure wording, including ambiguous or negated references; **they are unvalidated candidates, not confirmed complaint or fraud labels**. Each row can trigger multiple rules.

| Wording indicator | Main: distinct products, n=1,351 | Supplemental: nonempty reviews, n=1,388 |
| --- | ---: | ---: |
| Scam word family | 5 (0.37%) | 2 (0.14%) |
| General deception: scam/fraud/cheat families | 13 (0.96%) | 15 (1.08%) |
| Counterfeit-related terms: fake, duplicate, counterfeit, not original/genuine, etc. | 27 (2.00%) | 54 (3.89%) |
| Specified wrong-product phrases | 7 (0.52%) | 0 (0.00%) |
| Specified not-as-advertised phrases | 0 (0.00%) | 1 (0.07%) |
| Any rule fired | 46 (3.40%) | 69 (4.97%) |

Both samples' scam-family matches also contain the exact standalone word scam. A scam-only target is therefore extremely sparse. The narrow phrase rules miss paraphrases, spelling errors and multilingual complaints; zero matches do not mean no wrong-item incidents.

A subsequent scam-only context audit found that the main dataset's five matched product IDs reuse **one normalized review blob**, whose scam reference concerns an installation service. These are not five independent counterfeit or wrong-product allegations. The supplemental sample's two matches remain separate from this main-dataset finding. In the general-Amazon sample, the scam family produces 12 matches but the exact standalone word scam produces eight; two family matches discuss scam telephone calls in reviews of call-blocking products. Keyword occurrence therefore needs a separate relevance label.

Inspection found broad terms used in discussions of other sellers, uncertainty, fake reviews, and reassurance about authenticity. Context annotation must therefore precede claims about detection accuracy. No rule precision or recall has been measured.

### 2.3 Link between review text and individual stars

| Supplemental review group | Reviews | 1–2-star reviews | Share rated 1–2 stars |
| --- | ---: | ---: | ---: |
| Contains counterfeit-related terms | 54 | 41 | 75.9% |
| Does not contain those terms | 1,334 | 297 | 22.3% |
| Any complaint rule fired | 69 | 53 | 76.8% |
| No complaint rule fired | 1,319 | 285 | 21.6% |

Mean review rating is **1.68/5** for the 69 rule candidates versus **3.87/5** for the other 1,319 reviews. The candidates span 43 source ASINs. This supports the limited finding that specified complaint wording is associated with lower review stars in this corpus.

As a sensitivity check, retaining one record per normalized text leaves 1,133 texts. Of 45 texts containing counterfeit-related terms, 77.8% are rated 1–2 stars; the corresponding proportion among the other 1,088 texts is 23.3%. The relationship persists under this treatment of repeated text. Neither calculation proves counterfeiting or establishes a current India-wide rate.

The review and its stars describe the same completed experience. A pre-purchase tool must use **earlier customers' reviews**, not the future target customer's review. This analysis establishes an exploratory association, not forecast performance.

### 2.4 Link between text and listing metadata

These comparisons use the main dataset's 1,351 distinct products. The outcome is any rule firing in the available combined review text.

| Variable | Rule candidates, n=46 | Other products, n=1,305 | Interpretation |
| --- | ---: | ---: | --- |
| Mean aggregate listing rating | 4.06 | 4.09 | Very similar; averages may conceal individual complaints. One non-candidate rating is invalid/missing. |
| Median discounted price | INR 599 | INR 899 | A descriptive difference, not a validated risk threshold. Mean prices reverse the ordering because of expensive outliers. |
| Median discount | 48% | 49% | Little separation; the evidence does not support a large-discount-equals-scam rule. |
| Median listing rating count | 7,330.5 | 4,736 | More popular listings may provide more opportunity for complaints; two non-candidate counts are missing. |
| Median available text length | 1,266.5 characters | 800 characters | Longer text has more opportunities to contain a keyword. |

Candidate proportions differ by source category: electronics 25/490 (5.10%), computers/accessories 14/375 (3.73%), and home/kitchen 6/448 (1.34%). This is selected-sample description; do not rank tiny categories or call these counterfeit rates. Reused text also matters: collapsing identical main review blobs leaves 1,197 texts, of which 38 trigger a rule.

**Answer to the variable-link task:** a clear descriptive text–individual-star relationship exists in the supplemental source. Main-dataset ratings and discounts show little separation under the current rules. Price, popularity and category differences require better labels and controls for text availability before becoming predictive claims. No multivariable fraud model has been fitted.

### 2.5 General-Amazon check using the source already in the task file

Downloaded the first **20,000 records each** from the official Electronics and Cell_Phones_and_Accessories review files in Amazon Reviews 2023. This is a bounded **file-order convenience sample**, not a random sample or an analysis of all 571 million reviews. Four duplicate records and ten empty review bodies leave **39,986 nonempty reviews**, covering 33,779 ASINs. Sample dates range from August 2001 to March 2023. No India-only geography is inferred. The source revision and hashes are recorded in the sample manifest.

The same rules find **12 scam-family matches**, **98 counterfeit-term matches**, **58 wrong-product phrase matches**, **25 not-as-advertised phrase matches**, and **198 candidates under any rule**. Categories overlap between rules; do not sum these counts.

| General-Amazon comparison | With counterfeit-related terms, n=98 | Without those terms, n=39,888 |
| --- | ---: | ---: |
| Reviews rated 1–2 stars | 30/98 (30.6%) | 5,041/39,888 (12.6%) |
| Mean review stars | 3.56 | 4.25 |
| Verified-purchase share | 73.5% | 78.2% |
| At least one helpful vote | 39.8% | 22.7% |
| Median body length | 413 characters | 162 characters |

The low-star association is directionally consistent with the additional Indian-products corpus, but its magnitude differs substantially. Within categories it is 20.9% versus 11.0% in Electronics and 38.2% versus 14.3% in Cell Phones/Accessories. Removing repeated normalized text yields 30.9% versus 13.3% overall. Broad keyword context and source selection matter; these are not estimates of counterfeit incidence. Helpfulness differences could reflect text length, exposure, age or complaint salience rather than authenticity. Verified purchase does not establish physical authenticity: 72 of the 98 term-matching reviews have that indicator.

**Actual cross-dataset join:** the sampled general reviews share **21 exact `asin` values** with India `product_id` values, yielding **39 review rows**. Four India IDs also match a sampled `parent_asin`; variant and parent joins are distinct. The exact-ASIN join is exported with separately prefixed India-listing and general-review fields. All 39 matched review bodies have `any_complaint_rule_flag=0`, so this tiny overlap has no positive rule events with which to estimate a price/discount–complaint relationship. It establishes a technical catalogue link, not seller identity, a shared transaction, India-specific review provenance or verified fraud.

**Transfer conclusion:** both corpora show a text–rating association worth investigating. The current samples do not validate transport of a fraud model, numerical prevalence or seller-risk estimate into India. Expanding the bounded sample may increase overlap, but human complaint labels and offer/country/time linkage remain necessary.

### 2.6 Focused screen using one and two star reviews

Following the proposed star-first approach, use each **individual review's** 1-2-star rating as an initial filter, then inspect its body for relevant wording. This is a defined screening scope, not evidence that higher-star reviews contain no relevant complaints. The main India dataset's aggregate listing rating cannot implement this gate for its combined review text.

The general-Amazon sample contains **5,071** nonempty 1-2-star reviews. Within this group, the tested rules find 109 waste-of-money matches, 40 not-good matches, 83 poor/bad/low-quality matches, 12 exact fake matches, 30 broader counterfeit-term matches, 22 wrong-product phrase matches and 22 not-as-advertised phrase matches. Counts overlap across rules; the exact fake matches are included in the broader counterfeit-term group.

In total, **309** low-star reviews match at least one selected wording rule. Of these, **74** contain authenticity or mismatch wording: 30 authenticity and 44 mismatch candidates. The other 235 match only general dissatisfaction/deception wording. These categories describe regex matches, not independently validated complaints. The supplemental Indian-products corpus contains 338 low-star reviews, with 77 selected wording matches and 42 authenticity/mismatch candidates.

The proposed output separates general dissatisfaction from counterfeit concerns and wrong/not-as-described concerns. Low stars plus waste-of-money wording alone should not become a counterfeit label. No selected-word match means the screen did not find its chosen phrases; it does not mean the review is positive. Results and exact regex definitions are in `outputs/low_star_review_analysis.json`, reproduced by `analyse_low_star_reviews.py`. No synthetic outcomes were added.

## 3. Literature review and the product decisions it supports

| Research | Relevant evidence and limitation | Product decision supported |
| --- | --- | --- |
| **Wimmer & Yoon (2017), Decision Support Systems, 104**, [Counterfeit product detection](https://doi.org/10.1016/j.dss.2017.09.005); [author-university abstract](https://scholars.georgiasouthern.edu/en/publications/counterfeit-product-detection-bridging-the-gap-between-design-sci-3/) | OnCDS uses review text, lexicon sentiment, TF-IDF and topic analysis to produce a counterfeit score. The study links the score to perceived risk/trust and purchase attitude. Abstract-level evidence supports the concept; it is not an accuracy estimate for today's Amazon India. | Build an explainable review-evidence baseline and evaluate user understanding/trust as well as classification quality. |
| **Cao (2023), University of California, Irvine dissertation**, [An Empirical Examination of Deceptive Counterfeiting Activities in Electronic Markets](https://escholarship.org/uc/item/5v85s1fm) | Develops review-based listing counterfeit estimates and a separate identification approach involving an Amazon anti-counterfeit intervention, focusing on fragrances and wireless chargers. Dissertation evidence and narrow categories limit generalization. Repository abstract reviewed; not an independent replication. | Prioritize relevant categories and distinguish review-derived proxies from externally supported outcomes. |
| **Pontiki et al. (2014), SemEval**, [Aspect Based Sentiment Analysis](https://aclanthology.org/S14-2004/) | Establishes aspect-focused analysis rather than collapsing all opinions into a single sentiment. It is not a counterfeit benchmark. | Label authenticity, item identity and description mismatch separately; generic negative sentiment should not become a scam label. |
| **Ratner et al. (2017), Proceedings of the VLDB Endowment**, [Snorkel: Rapid Training Data Creation with Weak Supervision](https://arxiv.org/abs/1711.10160) | Describes noisy heuristic labelling functions and modelling their accuracies/dependencies. It does not imply that any keyword rule creates ground truth. | Store rule provenance, allow uncertain labels and validate against independent annotations. The supplied script uses simple rules; it does not implement Snorkel's learned label model. |
| **He et al. (2022), PNAS 119(47)**, [Detecting fake-review buyers using network structure](https://doi.org/10.1073/pnas.2211932119); [author manuscript](https://arxiv.org/abs/2410.17507) | Uses directly observed review-buying and reviewer–product network structure. Its journal year is 2022 despite the 2024 arXiv deposit. The target is review manipulation, not counterfeit physical goods. | Treat review credibility as a separate signal. Do not substitute fake-review labels for counterfeit labels; network features require data these CSVs do not provide. |
| **Guo et al. (2017), ICML**, [On Calibration of Modern Neural Networks](https://proceedings.mlr.press/v70/guo17a.html) | Shows that classifier confidence can be miscalibrated and evaluates post-processing calibration. These are general classification results, not marketplace fraud validation. | Do not display an arbitrary model score as a measured scam probability. Calibrate against the actual target on held-out data; calibration on allegation labels still estimates allegations. |

The synthesis is a staged approach: extract complaint aspects, check review credibility separately, validate labels, and only then consider probability outputs. The papers support a research direction, not a claim that the present datasets already support reliable seller-specific fraud prediction.

## 4. Industry and consulting evidence

**Market context.** Bain and Flipkart's *How India Shops Online 2026* estimates India's 2025 e-retail GMV at **USD 65–66 billion** and its shopper base at **290–300 million**, with **USD 170–180 billion** GMV projected for 2030. These are all-India e-retail figures and a forecast, respectively; they are not Amazon India's GMV or the fraud-prevention feature's revenue. The report draws on Bain analysis and marketplace inputs, including Flipkart, rather than a neutral census. [Bain–Flipkart report, executive summary, printed page 1](https://storage.googleapis.com/flipkart-stories-media/How_India_Shops_Online_2026_060094273e/How_India_Shops_Online_2026_060094273e.pdf).

**Counterfeit context.** OECD/EUIPO's 2025 report estimates counterfeit goods at **USD 467 billion, or 2.3% of global imports, in 2021**. This concerns international trade in counterfeit goods, not Amazon transactions, all domestic counterfeiting, or wrong-product delivery. It supports the problem's economic relevance but supplies no valid Amazon India fraud baseline. [OECD/EUIPO, Mapping Global Trade in Fakes 2025](https://www.oecd.org/en/publications/mapping-global-trade-in-fakes-2025_94d3b29f-en.html).

**Platform context.** Amazon reports identifying, seizing and disposing of more than 15 million counterfeit products worldwide in 2025. This is Amazon's own reporting and is not a count of completed Amazon India orders or an independently measured incident rate. The company already invests in counterfeit prevention; the proposal should show how its customer-facing evidence adds value to existing controls. [Amazon, 2025 Trustworthy Shopping Experience Report](https://trustworthyshopping.aboutamazon.com/2025-trustworthy-shopping-experience-report).

## 5. Competitor and substitute benchmark

Public feature descriptions were checked as of 31 October 2026. This is a desk benchmark, not a hands-on accuracy comparison.

| Offering | Publicly documented capability | Implication for the proposed feature |
| --- | --- | --- |
| **Amazon India AI Review Highlights** | Summarizes common review themes using verified-purchase reviews; Amazon announced India availability in December 2023. [Amazon India announcement](https://press.aboutamazon.com/in/2023/12/amazon-in-improves-customer-reviews-experience-with-generative-ai). | A generic review summary already exists. Differentiate through explicit complaint subtypes, traceable evidence and uncertainty; do not claim to introduce review summarization. |
| **Amazon Transparency** | Available in India; unit codes support authenticity checks and protection against incorrect versions. Enrolled-product scope applies, and the India page specifies Amazon-issued codes. [Amazon India product page](https://sell.amazon.in/brand-registry/transparency). | A direct authenticity mechanism already exists for enrolled products. Review-derived evidence is complementary and weaker than unit authentication. |
| **Flipkart Open Box Delivery** | Buyers can inspect selected products before accepting delivery and reject wrong/damaged items, according to Flipkart's description. [Flipkart guide](https://stories.flipkart.com/open-box-delivery-flipkart-customer-trust). | Addresses visible fulfillment mismatch at delivery. A proposed Amazon feature would operate earlier, while a physical check can reveal issues text prediction cannot. Eligibility is limited; no comparative effectiveness is established. |
| **ReviewMeta** | Public documentation describes review analysis, adjusted ratings and explanations for adjustments. [ReviewMeta's documented approach](https://reviewmeta.com/blog/fakespot-vs-reviewmeta-for-analyzing-reviews/). | Relevant review-credibility comparator, not proof of physical authenticity. Its live report generation and current Amazon.in coverage were not verified; direct page requests returned access errors. |
| **Fakespot by Mozilla — historical comparator** | Mozilla announced closure of its extension/apps/website on **1 July 2025**, and Firefox Review Checker on **10 June 2025**. [Mozilla announcement](https://blog.mozilla.org/en/mozilla/building-whats-next/). | Useful historical design precedent; do not list it as an active competitor in 2026. |

**Positioning inference:** an evidence panel separating authenticity allegations from wrong/not-as-described complaints is a plausible product direction. This is a proposed distinction, not a verified claim of market novelty. Seller-specific attribution would require additional platform data.

## 6. SWOT

| Strengths | Weaknesses |
| --- | --- |
| Reviews already contain relevant wording; text–star association is observable; evidence snippets can explain a flag; complaint subtypes fit the assigned problem. | Sparse relevant examples; no verified fraud labels or seller linkage; old, selected datasets; combined and repeated review text; weak current-India and multilingual coverage. |

| Opportunities | Threats |
| --- | --- |
| Combine future validated outcomes with seller/offer histories inside Amazon; complement Transparency; help users find specific complaints; evaluate whether clearer evidence reduces poor purchases and complaint handling. | Review manipulation, seller/variant changes and language drift; false accusations against legitimate sellers; overconfident scores; existing Amazon features may already address part of the need. |

The practical response is to begin with listing-level evidence and an insufficient-evidence state. Validate comprehension and complaint classification before extending the feature to seller risk.

## 7. Market sizing without inventing Amazon's share or fraud prevalence

For an internal Amazon feature, India's full e-retail GMV is **market context**, not software revenue TAM. Public sources reviewed here do not establish Amazon India's current eligible GMV, the relevant verified incident rate or willingness to pay for this feature. A defensible report should therefore present the sourced national market above and a clearly labelled scenario model below.

Use:

`Potential annual avoided loss = India e-retail GMV × assumed Amazon GMV share × eligible-category share × incident frequency × loss fraction per affected value × relative incident reduction`.

Incident frequency here is a value-weighted affected share, not the review-flag rate. The following values are **illustrative assumptions**, not measurements or forecasts. Base national GMV is the midpoint, USD 65.5 billion.

| Input/output | Low illustration | Middle illustration | High illustration |
| --- | ---: | ---: | ---: |
| Assumed Amazon GMV share | 20% | 25% | 30% |
| Assumed eligible-category share | 20% | 30% | 40% |
| Implied eligible GMV | USD 2.620bn | USD 4.9125bn | USD 7.860bn |
| Assumed affected share of eligible GMV | 0.5% | 1.0% | 2.0% |
| Assumed net loss fraction of affected value | 25% | 50% | 75% |
| Assumed relative reduction | 5% | 10% | 20% |
| Calculated annual avoided loss | **USD 0.164m** | **USD 2.456m** | **USD 23.580m** |

These outputs are sensitivity illustrations, not proven savings or addressable revenue. Refunds, customer losses and platform costs can overlap; choose whose net loss is counted before estimating business value. Cost, false-positive impact, displaced purchases and repeat-customer effects are not included. Do not insert the OECD global trade percentage or the CSV keyword rates as Amazon India incident prevalence.

To replace assumptions, obtain eligible Amazon India order/GMV counts by category, independently validated incident outcomes, economic losses net of recoveries, and a controlled pilot's incremental reduction. For a reach-based sizing, use Amazon-specific active shoppers and eligible traffic; do not multiply national shopper counts by a GMV share as if those units were interchangeable.

## 8. Recommended MVP and synthetic-data decision

**Now:** present a listing-level panel identifying authenticity allegations and wrong/not-as-described complaints, with evidence context and an insufficient-evidence state. The present data can demonstrate text processing and evidence display. It cannot substantiate a numeric scam likelihood or a judgement about the currently selected seller.

**Next:** annotate real text with independent complaint labels; obtain current India reviews with seller/offer and timestamp linkage; compare a keyword baseline with text-only and text-plus-metadata models on independent labels. Use only information available before the target purchase. Evaluate per-class errors and, for probability claims, calibration against the actual verified outcome. The detailed procedure is in [methods and data dictionary](methods_and_data_dictionary.md).

**Synthetic data:** not needed to establish the observed relationships. The main dataset has already been augmented with deterministic text indicators and numeric fields. The added columns are **derived, not synthetic**, and unknown fraud outcomes remain blank. If missing seller fields are required for an interface demonstration, use a separate, explicitly synthetic fixture; it must not validate fraud performance or market prevalence.

Suggested contribution description for the team's report: **“Dataset discovery and audit; exploratory review-text/metadata analysis; academic and industry literature synthesis; competitor benchmark; SWOT; assumption-based market sizing.”** This describes completed work without claiming a validated fraud model.

## Reproducible handoff

Use [README](README.md) for file locations, attribution and the run commands. `outputs/analysis_summary.json`, `outputs/general_amazon_summary.json` and their summary CSVs contain the exact counts behind this report. `outputs/amazon_india_augmented.csv` preserves every original main-dataset record and column. The 315-row annotation queue has blank human-label fields and is ready for independent annotation; 198 additional general-Amazon candidates are exported separately. No synthetic observations or verified-fraud labels were created.
