"""Scoring rules, thresholds and weights in one place.

Items marked [team sign-off] are proposals awaiting team agreement; change them here only.
"""

# Checkpoint 1 wording rules, copied verbatim from
# research/outputs/low_star_review_analysis.json ["patterns"] (test_config checks they still match).
WORDING_PATTERNS = {
    "waste_of_money": r"\bwaste\s+of\s+(?:my\s+)?money\b",
    "not_good": r"\b(?:not\s+(?:at\s+all\s+)?good|no\s+good)\b",
    "poor_or_bad_quality": r"\b(?:poor|bad|low)\s+quality\b",
    "fake_word": r"\bfake\b",
    "counterfeit_wording": r"\b(?:counterfeits?|fake|duplicates?|knock[ -]?offs?|not\s+(?:an?\s+)?(?:original|genuine)|non[ -]?genuine)\b",
    "wrong_product_wording": r"\bwrong\s+(?:item|product|model|size|colou?r|variant|brand)\b|\b(?:received|delivered|sent)\s+(?:(?:a|the|completely|totally)\s+){0,3}different\s+(?:item|product|model|size|colou?r|variant|brand)\b|\bnot\s+what\s+i\s+(?:had\s+)?ordered\b",
    "not_as_advertised_wording": r"\bnot\s+as\s+(?:advertised|described|shown|pictured)\b|\b(?:does\s+not|doesn't|did\s+not|didn't)\s+match\s+(?:the\s+)?(?:description|picture|image|advertisement)\b|\b(?:misleading|false)\s+(?:description|advertis(?:ement|ing)|claims?)\b",
    "deception_wording": r"\b(?:scam(?:s|med|mer|mers|ming)?|fraud(?:ulent)?|cheat(?:ed|ing|s)?)\b",
}

# Stage 2 of the review screen: phrases that the research context review found to cause false
# matches. Each matched phrase is removed and the specific rules are re-run on what is left, so
# "fake reviews, and this phone is fake too" still counts. Derived from research/outputs/
# listing_context_audit.json rejections; documented, not validated on independent labels.
CONTEXT_EXCLUSION_PATTERNS = {
    "about_other_reviews": r"\bfake\s+(?:reviews?|ratings?|comments?)\b|\b(?:reviews?|ratings?|comments?)\s+(?:are|were|seem|seemed|look|looked)\s+fake\b",
    "negated": r"\b(?:not|never|isn't|wasn't|isnt|wasnt|is\s+not|was\s+not|no)\s+(?:an?\s+)?(?:fake|counterfeit|duplicate|knock[ -]?off)\b",
    "comparison": r"\b(?:duplicate|copy|knock[ -]?off)\s+of\b",
    "buyer_error": r"\bi\s+(?:accidentally\s+|mistakenly\s+)?(?:ordered|selected|chose|picked)\s+the\s+wrong\b|\b(?:my|our)\s+(?:own\s+)?mistake\b",
}

# Specific (authenticity / mismatch) rules -> frontend tag, in priority order when several match.
SPECIFIC_RULE_TAGS = {
    "counterfeit_wording": "Authenticity",
    "wrong_product_wording": "Wrong item",
    "not_as_advertised_wording": "Description mismatch",
}

LOW_STARS = (1, 2)
HIGH_STARS = (4, 5)

# Gates
MIN_REVIEWS = 20
MIN_HISTORY_DAYS = 90
MIN_POLAR_REVIEWS = 20
MIN_WINDOW_REVIEWS = 10
WINDOW_DAYS = 90

# Reviews factor
LOW_STAR_SHARE_THRESHOLD = 0.25
SHARE_SENSITIVITY_THRESHOLDS = (0.20, 0.25, 0.30)
MIN_DISTINCT_ALLEGATIONS = 2
ALLEGATION_LOOKBACK_DAYS = 365  # [team sign-off]
MAX_FLAGGED_REVIEWS = 5

# History factor. Age gives evidence, not trust: 90+ days and 20+ ratings are needed to judge.
HISTORY_MIN_RATINGS = 20                # [provisional]
HISTORY_MIN_POSITIVE_PCT = 90.0         # [provisional]
ODR_MAX_PCT = 1.0                       # Amazon's published order defect rate target (<1%, 60 days)

# Price factor
PRICE_WARN_FRACTION_BELOW = 0.30        # [stakeholder: US4]
PRICE_ALERT_FRACTION_BELOW = 0.70       # [provisional demo boundary; needs legitimate-price data]
MIN_OTHER_SELLERS_FOR_PRICE = 2

# Brand factor: Brand Registry reseller authorisation as recorded by the brand owner
BRAND_VERIFIED = "verified"
BRAND_NOT_AUTHORISED = "not_authorised"
BRAND_UNVERIFIED = "unverified"
BRAND_CONTRADICTED = "contradicted"
BRAND_STATUSES = (BRAND_VERIFIED, BRAND_NOT_AUTHORISED, BRAND_UNVERIFIED, BRAND_CONTRADICTED)

# Complaints factor (customer-service records, counted once per affected order)
COMPLAINT_WINDOW_DAYS = 90
MIN_AFFECTED_ORDERS_FOR_WARN = 2        # [provisional]
MIN_COMPLAINT_RATE_FOR_WARN = 0.005     # [provisional] used only when order volume is known
CONFIRMED_FINDING_LOOKBACK_DAYS = 365   # [provisional]

# Severity within a warn status
SEVERITY_CONCERN = "concern"
SEVERITY_ALERT = "alert"

# Score and band
FACTOR_ORDER = ("history", "brand", "price", "reviews", "complaints")
INLINE_FALLBACK_ORDER = ("price", "history", "brand", "reviews", "complaints")
INLINE_COUNT = 3
# [team-derived; accepted by the team lead 11 Nov 2026] Swing weights: see backend/docs/weights.md.
FACTOR_WEIGHTS = {"history": 12, "brand": 16, "price": 17, "reviews": 29, "complaints": 26}
HIGH_MIN_SCORE = 75                     # [provisional]
MEDIUM_MIN_SCORE = 50                   # [provisional]
# A concern on any of these prevents High; any serious alert forces Low.
CAPPING_FACTORS = ("reviews", "complaints", "price", "brand")
MAX_NA_FACTORS = 1

BAND_HIGH = "High"
BAND_MEDIUM = "Medium"
BAND_LOW = "Low"
BAND_NOT_ENOUGH_DATA = "Not enough data"

PASS = "pass"
WARN = "warn"
NA = "na"

# pandas' default missing-value strings. The research loaded the CSV with pandas, which reads
# reviews such as "NA" and "None" as missing; matching this reproduces its 1,388 review count.
PANDAS_NA_STRINGS = frozenset({
    "", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan", "1.#IND", "1.#QNAN",
    "<NA>", "N/A", "NA", "NULL", "NaN", "None", "n/a", "nan", "null",
})
