# Factor weights: swing-weighting record

**Status:** accepted by the team lead (Arshad, M6) on 11 Nov 2026. These weights are **team-derived**. They are not expert-validated, not estimated from outcome data, and not representative of Amazon shoppers.

**Method:** swing weighting, as described in the UK Government Analysis Function's [introductory guide to MCDA](https://analysisfunction.civilservice.gov.uk/policy-store/an-introductory-guide-to-mcda) and the [DCLG multi-criteria analysis manual](https://www.researchgate.net/publication/30529921_Multi-Criteria_Analysis_A_Manual). Each factor is rated by how much its **swing** from a concrete bad state to a concrete good state matters, not by how important its name sounds. HM Treasury's MCDA guidance makes the same distinction.

## Where the weights apply

The weights only decide the band when nothing more serious does. The decision order (`trust_score/scoring.py`) is:

1. A **serious alert** (an extreme price, a contradicted authorisation claim or a confirmed counterfeit) gives **Low**, whatever the weights.
2. **Not enough data** comes from the gates, not from weights.
3. A **concern** on price, reviews, complaints or brand prevents **High**.
4. Only then does the weighted score choose between High, Medium and Low.

So each swing below runs from the **concern** state to the good state. Alert states are excluded on purpose, because they already override everything.

## Swings and ratings

The most valuable swing is rated 100, and each of the others is rated relative to it.

| Factor | Bad state (concern) | Good state | Rating | Reasoning and evidence |
|---|---|---|---|---|
| Reviews | 2+ distinct recent 1–2★ reviews alleging a fake, wrong or mismatched item | No such allegations | **100** | This is the most direct evidence available: buyers describing the problem the feature exists for. Review text has been used to estimate counterfeit risk (Wimmer & Yoon, 2017; Cao, Dewan & Lin). Reviews can be manipulated (Mayzlin et al., 2014; He et al., 2022), which is why copies count once. |
| Complaints | 2+ orders with authenticity complaints in 90 days, at 0.5% of orders or more | None | **90** | Direct and separate from reviews: a buyer took formal action. Complaints in reputation systems predict fraud and far outnumber official reports (Gregg & Scott, 2006). Rated a little below reviews because the counts are small and our data is mock. |
| Price | 30–70% below the typical price | In line | **60** | A documented warning cue (USPTO; Wadleigh et al., 2015), but an indirect one: legitimate sales happen, and counterfeiters often price close to the genuine product (BBB). Extreme prices are already handled by the alert. |
| Brand | Confirmed not authorised by the brand | Verified authorised reseller | **55** | Authorised resellers source from the brand, but an unauthorised seller may still sell genuine grey-market stock. It doesn't show the item is fake. A contradicted claim is an alert, not this swing. |
| History | Feedback under 90%, or order defect rate of 1% or more | Good feedback and service | **40** | Negative feedback is associated with seller misconduct (Gregg & Scott, 2006; Cabral & Hortaçsu, 2010), but feedback and order defect rate mostly measure service, not authenticity. |

**Normalised weights** (rating ÷ 345 × 100, rounded to total 100): reviews **29**, complaints **26**, price **17**, brand **16**, history **12**.

The ratings are judgements. The evidence column explains the order, but no source supplies these numbers.

## What changes compared with equal weights (20 each)

All 243 combinations of pass, concern and na were checked under the new decision order. 112 of them are scorable.

- **17 of 112** combinations get a different band, always Medium versus Low.
- The clearest case: a concern on **reviews and complaints together** gives **Low** (score 45), against **Medium** with equal weights. Both direct customer channels reporting authenticity problems is the strongest non-alert evidence, so Low is the intended result.
- Every other two-concern combination is **Medium** under both schemes.
- A single concern never gives Low. History is the only factor that can warn while the band stays High (score 88).
- Demo sellers A–E get the same bands under both schemes.

## Decision

The weights are shown to shoppers, with one-line reasons, in the "How the authenticity check works" panel. The page reads them from `data.json` (`weights`), so `config.py` stays the only source.


- [x] **Accept** the proposed weights (29 / 26 / 17 / 16 / 12) as team-derived.
- [ ] **Use equal weights** (20 each) as the documented fallback.
- [ ] **Change** the ratings (edit the table above, then update `FACTOR_WEIGHTS` in `trust_score/config.py`).

Decided by: Arshad (team lead)   Date: 11 Nov 2026

To strengthen the basis later: have each team member rate the swings independently, report the spread between them, and use the median. Shopper ratings from a short study would be stronger again. Only outcome data, meaning confirmed counterfeit orders, could support *estimated* weights.
