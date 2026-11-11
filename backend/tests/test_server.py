import json
import threading
import urllib.error
import urllib.request
from datetime import date
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from trust_score.loaders import load_seller_reviews
from trust_score.server import (
    DemoHandler,
    apply_edits,
    editable_inputs,
    extra_fake_reviews,
    flag,
    optional_number,
    recent_affected_orders,
    rescore,
    whole_number,
)

BACKEND = Path(__file__).resolve().parent.parent
LISTING = json.loads((BACKEND / "inputs/demo_listing.json").read_text(encoding="utf-8"))
REVIEWS = load_seller_reviews(BACKEND / "inputs/demo_reviews.csv")
CUTOFF = date(2026, 11, 6)


def _edit(seller_id, **changes):
    base = next(s for s in editable_inputs(LISTING)["sellers"] if s["id"] == seller_id)
    return {**base, **changes}


def test_recent_affected_orders_uses_window_and_counts_orders_once():
    seller = {"complaints": [{"id": "1", "order_id": "o1", "date": "2026-11-06"},
                             {"id": "2", "order_id": "o1", "date": "2026-11-01"},
                             {"id": "3", "date": "2026-08-09"}, {"id": "4", "date": "2026-08-08"}]}
    assert recent_affected_orders(seller, CUTOFF) == 2


def test_editable_inputs_lists_every_seller():
    inputs = editable_inputs(LISTING)
    assert inputs["dataCutoff"] == "2026-11-06"
    assert inputs["brandStatuses"] == ["verified", "not_authorised", "unverified", "contradicted"]
    assert [(s["id"], s["brandStatus"], s["recentComplaints"], s["complaintsAvailable"])
            for s in inputs["sellers"]] == [
        ("A", "verified", 0, True), ("B", "not_authorised", 0, True), ("C", "not_authorised", 3, True),
        ("D", "unverified", 0, True), ("E", "unverified", 0, True)]


@pytest.mark.parametrize("value", [None, 1.5, True, -1, 21, "3"])
def test_whole_number_rejects_invalid_values(value):
    with pytest.raises(ValueError, match="A: recentComplaints must be a whole number from 0 to 20."):
        whole_number({"id": "A", "recentComplaints": value}, "recentComplaints", 0, 20)


def test_apply_edits_replaces_profile_and_complaints_without_touching_original():
    edited = apply_edits(LISTING, {"sellers": [_edit("A", price=169999, recentComplaints=2)]})
    a = edited["sellers"][0]
    assert a["price"] == 169999
    assert [c["date"] for c in a["complaints"]] == ["2026-11-06", "2026-11-02"]
    assert LISTING["sellers"][0]["price"] == 254900


def test_apply_edits_rejects_unknown_seller():
    with pytest.raises(ValueError, match="Unknown seller id: 'Z'."):
        apply_edits(LISTING, {"sellers": [{"id": "Z"}]})


def test_apply_edits_rejects_bad_values():
    with pytest.raises(ValueError, match="A: positiveFeedbackPct must be from 0 to 100, or null."):
        apply_edits(LISTING, {"sellers": [_edit("A", positiveFeedbackPct=101)]})
    with pytest.raises(ValueError, match="A: brandStatus must be one of verified, not_authorised, unverified, contradicted."):
        apply_edits(LISTING, {"sellers": [_edit("A", brandStatus="yes")]})
    with pytest.raises(ValueError, match="A: complaintsAvailable must be true or false."):
        apply_edits(LISTING, {"sellers": [_edit("A", complaintsAvailable=None)]})


def test_optional_number_and_flag():
    assert optional_number({"x": None}, "x", 0, 100) is None
    assert optional_number({"x": 2.5}, "x", 0, 100) == 2.5
    assert flag({"x": False}, "x") is False


def test_apply_edits_complaints_unavailable_becomes_none():
    edited = apply_edits(LISTING, {"sellers": [_edit("C", complaintsAvailable=False)]})
    assert edited["sellers"][2]["complaints"] is None


def test_apply_edits_confirmed_counterfeit_adds_a_confirmed_complaint():
    edited = apply_edits(LISTING, {"sellers": [_edit("A", confirmedCounterfeit=True)]})
    assert [c["confirmed_counterfeit"] for c in edited["sellers"][0]["complaints"]] == [True]


def test_extra_fake_reviews_cycle_texts_and_are_one_star():
    reviews = extra_fake_reviews("A", 7, CUTOFF)
    assert len(reviews) == 7
    assert {r.stars for r in reviews} == {1}
    assert reviews[6].text == reviews[0].text


def test_rescore_without_edits_matches_build():
    doc = rescore(LISTING, REVIEWS, {})
    assert [(s["id"], s["band"], s["score"]) for s in doc["sellers"]] == [
        ("A", "High", 100), ("B", "Medium", 55), ("C", "Low", 0), ("D", "Not enough data", None),
        ("E", "Not enough data", None)]


def test_rescore_low_price_and_complaints_drop_seller_a_to_medium():
    doc = rescore(LISTING, REVIEWS, {"sellers": [_edit("A", price=169999, recentComplaints=2)]})
    a = doc["sellers"][0]
    # 2 complaints out of 900 orders is a low rate, so only the price concern applies (cap -> Medium)
    assert (a["band"], a["score"]) == ("Medium", 83)
    assert (a["factors"]["price"]["severity"], a["factors"]["complaints"]["status"]) == ("concern", "pass")


def test_rescore_extreme_price_forces_low_with_alert():
    doc = rescore(LISTING, REVIEWS, {"sellers": [_edit("A", price=5000)]})
    a = doc["sellers"][0]
    assert (a["band"], a["factors"]["price"]["severity"]) == ("Low", "alert")
    assert a["alert"] == a["factors"]["price"]["short"]


def test_rescore_fake_reviews_alone_cap_seller_a_at_medium():
    doc = rescore(LISTING, REVIEWS, {"sellers": [_edit("A", extraFakeReviews=3)]})
    a = doc["sellers"][0]
    assert (a["factors"]["reviews"]["status"], a["score"], a["band"]) == ("warn", 71, "Medium")


def test_rescore_new_seller_becomes_not_enough_data():
    doc = rescore(LISTING, REVIEWS, {"sellers": [_edit("A", daysSelling=30)]})
    assert doc["sellers"][0]["band"] == "Not enough data"


@pytest.fixture()
def server(tmp_path):
    (tmp_path / "index.html").write_text("<p>site</p>", encoding="utf-8")
    DemoHandler.listing = LISTING
    DemoHandler.reviews_by_seller = REVIEWS
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(DemoHandler, directory=str(tmp_path)))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def _post(url, body):
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def test_server_serves_static_files_and_inputs(server):
    with urllib.request.urlopen(server + "/index.html") as response:
        assert response.read() == b"<p>site</p>"
    with urllib.request.urlopen(server + "/api/inputs") as response:
        assert json.loads(response.read())["sellers"][0]["id"] == "A"


def test_server_rescores_valid_edits(server):
    body = json.dumps({"sellers": [_edit("A", price=169999, recentComplaints=2)]}).encode()
    status, doc = _post(server + "/api/score", body)
    assert (status, doc["sellers"][0]["band"]) == (200, "Medium")


def test_server_rejects_invalid_edits_with_message(server):
    status, payload = _post(server + "/api/score", json.dumps({"sellers": [{"id": "Z"}]}).encode())
    assert (status, payload) == (400, {"error": "Unknown seller id: 'Z'."})


def test_server_rejects_non_object_body(server):
    status, payload = _post(server + "/api/score", b"[1]")
    assert (status, payload) == (400, {"error": "Request body must be a JSON object."})


def test_server_unknown_post_route_is_404(server):
    status, payload = _post(server + "/api/other", b"{}")
    assert (status, payload) == (404, {"error": "Not found."})
