# Listing level validation after Checkpoint 1

Prepared 31 October 2026. The accepted star-plus-text screen is preserved in [Checkpoint 1](checkpoints/checkpoint_01_low_star_and_text.md) and its frozen JSON snapshot. This stage examines what the matching text supports about a listing.

## Finding

The two identifiers identify candidate review evidence. They do **not**, by themselves, establish a confirmed scam listing. The inspected data contains repeated authenticity allegations and a review reproducing a purported brand confirmation, but no independently authenticated counterfeit outcome or seller-fraud label. This is not evidence that the datasets contain no real counterfeits; it is a limit on what can be confirmed from these records.

The original Amazon India catalogue also contains accounts of an allegedly counterfeit delivery followed by an allegedly genuine replacement. These are useful examples of why a listing containing a scam-related review is not equivalent to every offer or delivered unit from that listing being fraudulent.

## Method

1. Preserve the original 1-2-star and wording screen unchanged.
2. Group reviews by exact ASIN. Check parent ASIN separately rather than silently pooling variants.
3. Use all available review stars as the sampled denominator, while keeping the text audit focused on the screened 1-2-star reviews.
4. Read the 74 general-Amazon and 42 supplemental authenticity/mismatch wording matches in context. Separate actual allegations, suspicion, buyer mistakes, irrelevant uses and ambiguous cases.
5. Count repeated distinct allegation texts. Use distinct reviewer IDs where supplied; the supplemental data supplies none, so distinct texts cannot be assumed to represent independent buyers.
6. Check whether entire review collections repeat across different product IDs. Keep reported brand/retailer checks separate from independently verified outcomes.

Context annotations are an assistant's research judgements, not an independently annotated gold standard. Borderline cases are retained as unclear or as suspicion. No classifier accuracy, marketplace prevalence or causal seller-intent claim follows from these labels.

## Listing coverage and repetition

| Measure | General Amazon convenience sample | Indian products supplemental corpus |
| --- | ---: | ---: |
| Nonempty reviews in analysed source | 39,986 | 1,388 |
| Low-star reviews matching any checkpoint wording | 309 | 77 |
| Exact listing IDs represented by those matches | 308 | 49 |
| Low-star authenticity/mismatch wording matches | 74 | 42 |
| Listing IDs represented by those specific matches | 73 | 26 |
| Context-relevant authenticity/mismatch allegations or suspicions | 45 | 39 |
| Listing IDs with those context-relevant texts | 45 | 23 |
| Listing IDs with at least two distinct relevant texts | 0 | 9 |

Of the 73 general-Amazon specific-wording candidate listings, **60 have only one sampled review**. The sample is therefore particularly weak for estimating a listing-wide negative-review share. One ASIN initially had two wording hits, but only one establishes a clear target-related allegation after context review.

In the supplemental corpus, nine ASINs have repeated relevant allegation texts. Six of those have a majority of 1-2-star reviews among the available source reviews. However, `B01LNA2MQK` and `B07YSHDZY1` contain the same ten review records, so the nine IDs represent **eight distinct review-collection groups** with repetition. Three other pairs of candidate IDs also reuse entire review collections. These copies must not be counted as independent corroboration across products.

All listing fractions below use **downloaded sample records**, not a complete Amazon review history. The supplemental dataset's selected groups of roughly ten reviews do not establish its sampling method, current prevalence, or reviewer independence.

## Cases that explain the evidence levels

| Dataset and ASIN | Available review evidence | Supported interpretation |
| --- | --- | --- |
| General Amazon `B005WUHAX8` | Two sampled reviews, one low-star review. The negative reviewer reproduces a purported brand-support reply rejecting supplied serial numbers as counterfeit and declining warranty. | A reported brand confirmation is stronger than a bare keyword. The email's authenticity, the unit and the seller/order linkage were not independently checked. It does not establish a majority of bad reviews or deliberate listing-wide fraud. |
| Supplemental `B0758LVKLL` | 7/10 sampled reviews are 1-2 stars. Four distinct matching texts report or suspect inauthentic/adulterated goods, mentioning product behaviour, smell, taste or packaging. | Repeated authenticity concerns with a high sampled low-star share. A stronger candidate for investigation, not an authenticated counterfeit listing. |
| Supplemental `B008YD57OO` | 6/10 sampled reviews are 1-2 stars. Four distinct matching texts report or suspect inauthentic contents, differences from a store-bought product, opened packaging or missing quantity. | Repeated authenticity concerns. Independent authentication and independent reviewer identity are unavailable. |
| Supplemental `B07DQN5B3G` | 3/10 sampled reviews are 1-2 stars. Two distinct reviews allege a copied watch and report a branded-store or shopkeeper check; one mentions serial-number inconsistency. | More specific supporting accounts, but the checks are reported by reviewers, not independently obtained. A low-star majority is not necessary for a serious allegation to exist. |
| General Amazon `B00KWR8ME2` | 1/5 sampled reviews is low-star and triggers the wrong-product phrase rule. The reviewer acknowledges selecting an incompatible product and praises its quality. | Buyer selection error. This does not support a seller-side wrong-item allegation despite satisfying the initial two identifiers. |
| General Amazon `B01415QHYW` | Of 38 sampled reviews, ten are 1-2 stars, one is three stars, and 27 are 4-5 stars. Two reviews trigger wording rules; one is an unclear size complaint and one explicitly alleges a description mismatch. Other low-star reviews concern fit, damage, durability or an empty delivery. | General dissatisfaction and one clear mismatch allegation. The two keyword hits are not sufficient to label this a scam listing. The positive-review texts have not all undergone a systematic semantic comparison. |

## Separate check in the original Amazon India dataset

This check supplies context only: its combined review text does not provide the individual star ratings needed to test the checkpoint rule.

- **`B09MT84WV5` and `B09MT6XSFW`:** both have aggregate listing ratings of 4.3 and reuse one combined review blob. A reviewer reports two allegedly fake memory-card deliveries, followed by a genuine replacement on the third purchase. The same account appears under different capacity variants. It is one reused account of historical delivery problems, not two independently confirmed scam listings.
- **`B0BCYQY9X5`:** aggregate rating 4.3. One review account says a barcode check identified the initial delivery as duplicate and that a later replacement was original; it also describes subsequent service and recommends checking genuineness. This is a reported counterfeit incident followed by a resolution, not independent proof that the listing or its current seller is fraudulent.

The strongest repeated cases in the supplemental corpus do not overlap the main India catalogue's ASINs. The general sample's 21-ASIN overlap with the catalogue contained no keyword-screen candidates. Do not transfer the external cases' allegation labels to unrelated India products.

## Can the two identifiers confirm a scam listing

**No independent confirmation can be assigned from the two identifiers alone.** A low rating can arise from quality, compatibility, delivery or buyer error. A keyword can refer to another review, a deliberately simulated product, another seller or a replacement. Repetition strengthens an allegation only after context and duplicate checks, and even repeated allegations remain distinct from authenticated outcomes.

For this project, retain separate outcomes:

| Output | Required evidence |
| --- | --- |
| Keyword-screen candidate | Individual 1-2-star review plus the selected wording. |
| Relevant listing concern | Context identifies an authenticity or seller-side item/description-mismatch allegation. |
| Repeated listing concern in the sample | At least two distinct relevant texts, with reviewer identity and duplication limits disclosed. This is an exploratory descriptor, not a validated risk threshold. |
| Reviewer-reported external check | Review describes or reproduces a claimed brand/retailer check. |
| Independently confirmed outcome | Separate authenticated brand, unit, order or enforcement evidence matched to the relevant item/offer and time. This evidence has not been obtained here. |

The current data supports the first four evidence descriptions in particular cases. It does not supply independently verified scam labels for training or validating a confirmed-fraud model. No synthetic confirmation labels were created.

## Reproduce and inspect

- `analyse_listing_evidence.py` preserves Checkpoint 1, groups available reviews and writes `outputs/listing_evidence_audit.json`.
- `review_listing_context.py` records the fixed context audit and writes `outputs/listing_context_audit.json`. A review-ID fingerprint prevents silently reusing positional annotations if candidate order changes.
- The general sample manifest records source revision and hashes. The public dataset viewer returned an unsupported-dataset response when a targeted query route was checked; a complete listing review history was not retrieved or claimed.
- Original source observations and the checkpoint remain unchanged. Context classifications can be independently reviewed and revised as a subsequent annotation exercise.
