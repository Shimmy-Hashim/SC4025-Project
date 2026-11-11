"""Shopper-facing explanation templates written into data.json."""

SOURCE_HISTORY = "Seller performance data"
SOURCE_BRAND = "Brand Registry reseller authorisation"
SOURCE_PRICE = "Prices from other sellers on this listing"
SOURCE_REVIEWS = "Review analysis"
SOURCE_COMPLAINTS = "Customer complaints"

HISTORY_PASS_SHORT = "{duration} selling · {pct}% positive feedback"
HISTORY_WARN_FEEDBACK_SHORT = "{pct}% positive feedback"
HISTORY_WARN_ODR_SHORT = "Order defect rate {odr}% (target under 1%)"
HISTORY_TEXT = "{duration} selling, {pct}% positive feedback from {count} ratings."
HISTORY_ODR_TEXT = " Order defect rate {odr}% over 60 days (Amazon's target is under 1%)."
HISTORY_NA_SHORT = "Seller history: not enough yet"
HISTORY_NA_TEXT = "Joined {duration} ago. Sellers need 90 days of history to be scored."
HISTORY_LIMITED_SHORT = "Limited history: {count} ratings"
HISTORY_LIMITED_TEXT = (
    "{duration} selling with only {count} ratings, too few to judge feedback. This is not a warning."
)

BRAND_PASS_SHORT = "Authorised {brand} reseller"
BRAND_PASS_TEXT = "The brand lists this seller as an authorised reseller."
BRAND_WARN_SHORT = "Not authorised by the brand"
BRAND_WARN_TEXT = (
    "The brand has confirmed this seller is not an authorised reseller. "
    "This does not mean the item is counterfeit."
)
BRAND_ALERT_SHORT = "Claims authorisation the brand denies"
BRAND_ALERT_TEXT = "The seller claims to be an authorised reseller, but the brand says it is not."
BRAND_NA_SHORT = "Brand authorisation: not verified"
BRAND_NA_TEXT = "No reseller authorisation from the brand was found. This is not a warning."

PRICE_PASS_SHORT = "Price in line with other sellers"
PRICE_PASS_TEXT = "{price} is in line with the typical price of {typical} (median of the other {n} sellers)."
PRICE_WARN_SHORT = "Price {pct}% below other sellers"
PRICE_WARN_TEXT = "{price} is {pct}% below the typical price of {typical} (median of the other {n} sellers)."
PRICE_ALERT_SHORT = "Extreme price: {pct}% below other sellers"
PRICE_ALERT_TEXT = (
    "{price} is {pct}% below the typical price of {typical} (median of the other {n} sellers). Check the full price, "
    "condition and what is included before buying."
)
PRICE_NA_SHORT = "Price comparison: not available"
PRICE_NA_TEXT = "Too few other sellers on this listing to compare prices."

REVIEWS_PASS_SHORT = "No unusual review patterns"
REVIEWS_PASS_TEXT = "No 1-2 star reviews mention a fake, wrong or mismatched item."
REVIEWS_ISOLATED_SHORT = "1 review mentions a possible issue"
REVIEWS_ISOLATED_TEXT = (
    "1 of {n} reviews mentions {concern}. A single report is not treated as a pattern."
)
REVIEWS_REPEATED_SHORT = "Reviews mention {concern_short}"
REVIEWS_REPEATED_TEXT = "{k} of {n} reviews mention {concern}."
REVIEWS_CONCENTRATION_SHORT = "Many low ratings, with {concern_short}"
REVIEWS_CONCENTRATION_TEXT = (
    "{pct}% of this seller's 1-2 and 4-5 star reviews are 1-2 stars, "
    "and {k} of {n} reviews mention {concern}."
)
REVIEWS_TREND_RISING = " These mentions rose in the last 90 days."
REVIEWS_TREND_NOT_RISING = " These mentions did not rise in the last 90 days."
REVIEWS_TREND_UNAVAILABLE = " Too few reviews to check the trend over time."
REVIEWS_DUPLICATES = " {k} copied reviews were counted once."
REVIEWS_NA_SHORT = "Reviews: only {n} so far"
REVIEWS_NA_TEXT = "Only {n} reviews so far. At least 20 are needed to check patterns."

# Per-tag wording: (inside a sentence, short buy-box phrase)
CONCERN_WORDING = {
    "Authenticity": ("a possibly fake or non-original item", "possibly non-original items"),
    "Wrong item": ("receiving the wrong item", "wrong items received"),
    "Description mismatch": ("an item that differs from its description", "items not as described"),
}

CONCERN_WITH_COUNT = "{concern} ({n})"
CONCERN_JOINER = " or "

COMPLAINTS_PASS_SHORT = "No authenticity complaints"
COMPLAINTS_PASS_TEXT = "No authenticity complaints in the last 90 days."
COMPLAINTS_SINGLE_SHORT = "1 order with an authenticity complaint"
COMPLAINTS_SINGLE_TEXT = (
    "1 order with an authenticity complaint in the last 90 days. "
    "A single complaint is not treated as a pattern."
)
COMPLAINTS_LOW_RATE_SHORT = "{n} complaints from {orders} orders"
COMPLAINTS_LOW_RATE_TEXT = (
    "{n} orders with authenticity complaints out of {orders} in the last 90 days ({rate}%)."
)
COMPLAINTS_WARN_SHORT = "{n} orders with authenticity complaints"
COMPLAINTS_WARN_TEXT = "{n} orders with authenticity complaints in the last 90 days."
COMPLAINTS_RATE_TEXT = " That is {n} of {orders} orders ({rate}%)."
COMPLAINTS_ALERT_SHORT = "Confirmed counterfeit item"
COMPLAINTS_ALERT_TEXT = "An investigation confirmed a counterfeit item from this seller on {date}."
COMPLAINTS_NA_SHORT = "Complaints: not enough history"
COMPLAINTS_NA_TEXT = "Too little history to assess complaints."
COMPLAINTS_UNAVAILABLE_SHORT = "Complaints data unavailable"
COMPLAINTS_UNAVAILABLE_TEXT = (
    "No complaints data is available for this seller. This is not the same as zero complaints."
)

# Shopper-facing reason for each factor's weight (see docs/weights.md for sources).
WEIGHT_REASONS = {
    "reviews": "Buyers describing a fake, wrong or mismatched item is the most direct evidence.",
    "complaints": "Formal complaints to customer service are direct evidence from a separate channel.",
    "price": "An unusually low price is a known warning sign, but genuine sales also happen.",
    "brand": "Unauthorised sellers can still sell genuine stock, so this is indirect evidence.",
    "history": "Feedback and order problems mostly reflect service, not authenticity.",
}

REASON_NEW_AND_FEW_REVIEWS = "Joined {duration} ago with only {n} reviews, so it is too new to assess."
REASON_NEW = "Joined {duration} ago, so it is too new to assess."
REASON_FEW_REVIEWS = "Only {n} reviews so far, so it cannot be assessed yet."
REASON_MISSING_FACTORS = "Too little information is available to assess this offer."
REASON_NOT_A_WARNING = " This is not a warning."
REASON_SEE_ALERT = " See the alert above."
