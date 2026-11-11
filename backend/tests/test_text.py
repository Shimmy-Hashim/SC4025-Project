import pytest

from trust_score.text import (
    format_duration,
    format_indian_number,
    format_inr,
    interpreted_tag,
    matched_exclusions,
    is_missing_text,
    matched_rules,
    norm,
    specific_tag,
    strip_excluded_phrases,
)


def test_norm_collapses_whitespace_trims_and_casefolds():
    assert norm("  This IS\n\tFake  ") == "this is fake"


@pytest.mark.parametrize("value", [None, "", "   ", "NA", "None", "nan", "N/A", "null"])
def test_is_missing_text_true_for_pandas_missing_values(value):
    assert is_missing_text(value) is True


@pytest.mark.parametrize("value", ["Ok", "👍", "na ", "Not available"])
def test_is_missing_text_false_for_real_text(value):
    assert is_missing_text(value) is False


def test_matched_rules_finds_generic_and_specific_rules():
    assert matched_rules("Waste of money, this is a fake") == {
        "waste_of_money", "fake_word", "counterfeit_wording"}


def test_matched_rules_empty_for_positive_text():
    assert matched_rules("Lovely phone, works perfectly.") == set()


@pytest.mark.parametrize("text, tag", [
    ("This phone is not genuine.", "Authenticity"),
    ("Looks like a knock-off.", "Authenticity"),
    ("Received a different model.", "Wrong item"),
    ("Not what I ordered.", "Wrong item"),
    ("Not as described at all.", "Description mismatch"),
    ("Colour doesn't match the picture.", "Description mismatch"),
])
def test_specific_tag_maps_each_rule_to_its_tag(text, tag):
    assert specific_tag(text) == tag


def test_specific_tag_prefers_authenticity_when_several_rules_match():
    assert specific_tag("Fake phone and not as described.") == "Authenticity"


def test_specific_tag_none_for_generic_complaint():
    assert specific_tag("Poor quality and a waste of money.") is None


def test_specific_tag_matches_negated_wording_known_limitation():
    # Regex-only screening cannot read negation (context_trap_burst limitation).
    assert specific_tag("This is not fake; delivery was slow.") == "Authenticity"


@pytest.mark.parametrize("value, expected", [
    (0, "0"), (999, "999"), (1000, "1,000"), (8410, "8,410"), (99999, "99,999"),
    (100000, "1,00,000"), (254900, "2,54,900"), (12345678, "1,23,45,678"), (-254900, "-2,54,900"),
])
def test_format_indian_number_groups_lakhs_and_crores(value, expected):
    assert format_indian_number(value) == expected


def test_format_inr_adds_rupee_sign():
    assert format_inr(164999) == "₹1,64,999"


@pytest.mark.parametrize("days, expected", [
    (1, "1 week"), (13, "1 week"), (21, "3 weeks"), (30, "1 month"), (125, "4 months"),
    (364, "12 months"), (365, "1 year"), (2230, "6 years"),
])
def test_format_duration_uses_weeks_months_years(days, expected):
    assert format_duration(days) == expected


@pytest.mark.parametrize("text", [
    "This is not fake; delivery was slow.",
    "Fake reviews everywhere, battery is poor.",
    "Other reviews were fake, battery is poor.",
    "Looks like a duplicate of the Titan watch.",
    "I ordered the wrong size myself.",
])
def test_interpreted_tag_drops_known_false_positive_contexts(text):
    assert specific_tag(text) is not None
    assert interpreted_tag(text) is None


@pytest.mark.parametrize("text, tag", [
    ("Fake reviews here, and this phone is fake too.", "Authenticity"),
    ("Received a different model.", "Wrong item"),
    ("Not as described.", "Description mismatch"),
])
def test_interpreted_tag_keeps_allegations_that_remain(text, tag):
    assert interpreted_tag(text) == tag


def test_interpreted_tag_none_without_stage_one_match():
    assert interpreted_tag("Lovely phone.") is None


def test_matched_exclusions_and_strip():
    assert matched_exclusions("Not fake, and fake reviews.") == {"negated", "about_other_reviews"}
    assert "fake" not in strip_excluded_phrases("Not fake.").lower()
