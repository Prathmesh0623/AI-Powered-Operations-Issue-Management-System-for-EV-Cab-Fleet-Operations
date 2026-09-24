from tests.conftest import login, auth_headers
from ml.inference.category_predictor import is_ready as category_ready
from ml.inference.priority_predictor import is_ready as priority_ready
from ml.inference.similarity_engine import find_similar_issues


def test_classify_missing_description(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = client.post("/api/ai/classify", json={"title": "no description"}, headers=auth_headers(token))
    assert res.status_code == 400


def test_classify_returns_prediction_when_model_ready(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = client.post(
        "/api/ai/classify",
        json={"title": "Charging issue", "description": "EV-101 is not charging at station 3."},
        headers=auth_headers(token),
    )
    if category_ready():
        assert res.status_code == 200
        assert "predicted_category" in res.get_json()["data"]
    else:
        assert res.status_code == 503


def test_priority_missing_description(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = client.post("/api/ai/priority", json={"title": "x"}, headers=auth_headers(token))
    assert res.status_code == 400


def test_priority_returns_prediction_when_model_ready(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = client.post(
        "/api/ai/priority",
        json={"title": "Battery issue", "description": "Battery drains too fast.", "category": "Battery"},
        headers=auth_headers(token),
    )
    if priority_ready():
        assert res.status_code == 200
    else:
        assert res.status_code == 503


def test_similarity_engine_detects_near_duplicate():
    candidates = [(1, "EV-102 is not charging", "EV-102 is not charging at station 4")]
    results = find_similar_issues(
        "Vehicle 102 charging failure",
        "Vehicle 102 has a charging failure at the station",
        candidates,
        threshold=0.1,
    )
    assert len(results) == 1
    assert results[0][0] == 1


def test_similarity_engine_no_match_for_unrelated_text():
    candidates = [(1, "Driver did not show up", "Driver has not arrived for the assigned shift")]
    results = find_similar_issues("Payment issue", "Customer was double charged for a ride.", candidates, threshold=0.5)
    assert results == []


def test_similarity_engine_empty_candidates():
    results = find_similar_issues("Some title", "Some description", [])
    assert results == []


def test_impact_analysis_endpoint(client):
    token = login(client, "operator@test.com", "Operator@123")
    create_res = client.post(
        "/api/issues",
        json={"title": "Vehicle issue", "description": "Something is wrong.", "vehicle_id": 1},
        headers=auth_headers(token),
    )
    issue_id = create_res.get_json()["data"]["id"]

    res = client.get(f"/api/ai/issues/{issue_id}/impact-analysis", headers=auth_headers(token))
    assert res.status_code == 200
    assert res.get_json()["data"]["operational_impact"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_impact_analysis_nonexistent_issue(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = client.get("/api/ai/issues/9999/impact-analysis", headers=auth_headers(token))
    assert res.status_code == 404
