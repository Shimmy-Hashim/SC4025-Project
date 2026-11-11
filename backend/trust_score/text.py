"""Text normalisation, wording rules and number formatting."""

import re
from typing import Dict, Optional, Pattern, Set

from trust_score.config import (
    CONTEXT_EXCLUSION_PATTERNS,
    PANDAS_NA_STRINGS,
    SPECIFIC_RULE_TAGS,
    WORDING_PATTERNS,
)

COMPILED_PATTERNS: Dict[str, Pattern[str]] = {
    name: re.compile(pattern, re.I) for name, pattern in WORDING_PATTERNS.items()
}
COMPILED_EXCLUSIONS: Dict[str, Pattern[str]] = {
    name: re.compile(pattern, re.I) for name, pattern in CONTEXT_EXCLUSION_PATTERNS.items()
}


def norm(text: str) -> str:
    """Collapse whitespace, trim and case-fold; identical to the research's norm()."""
    return re.sub(r"\s+", " ", text).strip().casefold()


def is_missing_text(value: Optional[str]) -> bool:
    """True when a raw CSV value counts as missing, matching pandas' default reading."""
    return value is None or value in PANDAS_NA_STRINGS or not value.strip()


def matched_rules(text: str) -> Set[str]:
    """Names of every Checkpoint 1 wording rule that matches the text."""
    return {name for name, pattern in COMPILED_PATTERNS.items() if pattern.search(text)}


def specific_tag(text: str) -> Optional[str]:
    """Stage 1: tag of the first matching Checkpoint 1 authenticity/mismatch rule, or None."""
    rules = matched_rules(text)
    for rule, tag in SPECIFIC_RULE_TAGS.items():
        if rule in rules:
            return tag
    return None


def strip_excluded_phrases(text: str) -> str:
    """Text with every stage 2 exclusion phrase replaced by a space."""
    for pattern in COMPILED_EXCLUSIONS.values():
        text = pattern.sub(" ", text)
    return text


def matched_exclusions(text: str) -> Set[str]:
    """Names of stage 2 exclusion patterns found in the text."""
    return {name for name, pattern in COMPILED_EXCLUSIONS.items() if pattern.search(text)}


def interpreted_tag(text: str) -> Optional[str]:
    """Stage 2: the stage 1 tag after removing excluded phrases ("fake reviews", "not fake",
    "duplicate of", "I ordered the wrong"), or None when nothing specific remains."""
    if specific_tag(text) is None:
        return None
    return specific_tag(strip_excluded_phrases(text))


def format_indian_number(value: int) -> str:
    """Group digits the Indian way: 254900 -> '2,54,900'."""
    digits = str(abs(value))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        pairs = []
        while len(head) > 2:
            pairs.insert(0, head[-2:])
            head = head[:-2]
        digits = ",".join([head] + pairs + [tail])
    return ("-" if value < 0 else "") + digits


def format_inr(amount: int) -> str:
    """Rupee amount with Indian grouping: 254900 -> '₹2,54,900'."""
    return "₹" + format_indian_number(amount)


def format_duration(days: int) -> str:
    """Human seller-history length: years from 365 days, months from 30, otherwise weeks."""
    if days >= 365:
        years = days // 365
        return f"{years} year" + ("s" if years != 1 else "")
    if days >= 30:
        months = days // 30
        return f"{months} month" + ("s" if months != 1 else "")
    weeks = max(days // 7, 1)
    return f"{weeks} week" + ("s" if weeks != 1 else "")
