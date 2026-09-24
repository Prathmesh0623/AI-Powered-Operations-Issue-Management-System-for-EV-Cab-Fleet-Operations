from tests.conftest import login, auth_headers


def _create_issue(client, token, **overrides):
    payload = {"title": "Test issue", "description": "A description that is reasonably detailed."}
    payload.update(overrides)
    return client.post("/api/issues", json=payload, headers=auth_headers(token))


def test_create_issue_success(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = _create_issue(client, token)
    body = res.get_json()
    assert res.status_code == 201
    assert body["data"]["status"] == "OPEN"
    assert body["data"]["title"] == "Test issue"


def test_create_issue_missing_title(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = client.post("/api/issues", json={"description": "only description"}, headers=auth_headers(token))
    assert res.status_code == 400


def test_create_issue_empty_description(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = client.post("/api/issues", json={"title": "x", "description": ""}, headers=auth_headers(token))
    assert res.status_code == 400


def test_list_issues(client):
    token = login(client, "operator@test.com", "Operator@123")
    _create_issue(client, token)
    res = client.get("/api/issues", headers=auth_headers(token))
    body = res.get_json()
    assert res.status_code == 200
    assert body["data"]["total"] >= 1


def test_get_nonexistent_issue(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = client.get("/api/issues/9999", headers=auth_headers(token))
    assert res.status_code == 404


def test_invalid_status_transition_rejected(client):
    token = login(client, "operator@test.com", "Operator@123")
    create_res = _create_issue(client, token)
    issue_id = create_res.get_json()["data"]["id"]

    # OPEN -> RESOLVED is not a valid direct transition.
    res = client.post(f"/api/issues/{issue_id}/status", json={"status": "RESOLVED"}, headers=auth_headers(token))
    assert res.status_code == 400


def test_valid_status_transition_succeeds(client):
    token = login(client, "operator@test.com", "Operator@123")
    create_res = _create_issue(client, token)
    issue_id = create_res.get_json()["data"]["id"]

    res = client.post(f"/api/issues/{issue_id}/status", json={"status": "ASSIGNED"}, headers=auth_headers(token))
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "ASSIGNED"


def test_invalid_priority_value_rejected(client):
    token = login(client, "operator@test.com", "Operator@123")
    create_res = _create_issue(client, token)
    issue_id = create_res.get_json()["data"]["id"]

    res = client.post(f"/api/issues/{issue_id}/priority", json={"priority": "Super Urgent"}, headers=auth_headers(token))
    assert res.status_code == 400


def test_empty_comment_rejected(client):
    token = login(client, "operator@test.com", "Operator@123")
    create_res = _create_issue(client, token)
    issue_id = create_res.get_json()["data"]["id"]

    res = client.post(f"/api/issues/{issue_id}/comments", json={"comment": "   "}, headers=auth_headers(token))
    assert res.status_code == 400


def test_add_valid_comment(client):
    token = login(client, "operator@test.com", "Operator@123")
    create_res = _create_issue(client, token)
    issue_id = create_res.get_json()["data"]["id"]

    res = client.post(f"/api/issues/{issue_id}/comments", json={"comment": "Looking into this."}, headers=auth_headers(token))
    assert res.status_code == 201


def test_assign_issue_moves_to_assigned(client):
    token = login(client, "operator@test.com", "Operator@123")
    create_res = _create_issue(client, token)
    issue_id = create_res.get_json()["data"]["id"]

    res = client.post(f"/api/issues/{issue_id}/assign", json={"user_id": 1}, headers=auth_headers(token))
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "ASSIGNED"


def test_issue_gets_operational_impact_on_creation(client):
    token = login(client, "operator@test.com", "Operator@123")
    # vehicle_id=1 is the seeded EV-999, status "On Ride"
    res = _create_issue(client, token, vehicle_id=1, priority="Critical")
    issue_id = res.get_json()["data"]["id"]

    detail_res = client.get(f"/api/issues/{issue_id}", headers=auth_headers(token))
    data = detail_res.get_json()["data"]
    assert data["operational_impact"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert data["impact_explanation"]
