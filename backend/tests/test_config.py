import json
from pathlib import Path

from trust_score.config import FACTOR_ORDER, FACTOR_WEIGHTS, SPECIFIC_RULE_TAGS, WORDING_PATTERNS

CHECKPOINT = Path(__file__).resolve().parent.parent / "research/outputs/low_star_review_analysis.json"


def test_wording_patterns_match_frozen_checkpoint():
    frozen = json.loads(CHECKPOINT.read_text(encoding="utf-8"))["patterns"]
    assert WORDING_PATTERNS == frozen


def test_specific_rules_are_checkpoint_rules_with_frontend_tags():
    assert set(SPECIFIC_RULE_TAGS) <= set(WORDING_PATTERNS)
    assert list(SPECIFIC_RULE_TAGS.values()) == ["Authenticity", "Wrong item", "Description mismatch"]


def test_every_factor_has_a_weight_totalling_100():
    assert set(FACTOR_WEIGHTS) == set(FACTOR_ORDER)
    assert sum(FACTOR_WEIGHTS.values()) == 100
