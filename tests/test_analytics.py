from tests.conftest import login, auth_headers


def test_overview_requires_auth(client):
    res = client.get("/api/analytics/overview")
    assert res.status_code == 401


def test_overview_returns_kpis(client):
    token = login(client, "manager@test.com", "Manager@123")
    res = client.get("/api/analytics/overview", headers=auth_headers(token))
    body = res.get_json()
    assert res.status_code == 200
    for key in ("total_issues", "open_issues", "critical_issues", "resolved_issues"):
        assert key in body["data"]


def test_issues_breakdown_structure(client):
    token = login(client, "manager@test.com", "Manager@123")
    res = client.get("/api/analytics/issues", headers=auth_headers(token))
    body = res.get_json()
    assert res.status_code == 200
    for key in ("by_category", "by_priority", "by_status", "by_hub", "trend_last_30_days"):
        assert key in body["data"]


def test_recurring_issues_empty_when_no_data(client):
    token = login(client, "manager@test.com", "Manager@123")
    res = client.get("/api/analytics/recurring-issues", headers=auth_headers(token))
    assert res.status_code == 200
    assert isinstance(res.get_json()["data"], list)


def test_audit_logs_admin_only(client):
    manager_token = login(client, "manager@test.com", "Manager@123")
    res = client.get("/api/audit-logs", headers=auth_headers(manager_token))
    assert res.status_code == 403

    admin_token = login(client, "admin@test.com", "Admin@123")
    res2 = client.get("/api/audit-logs", headers=auth_headers(admin_token))
    assert res2.status_code == 200


def test_notifications_endpoint(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = client.get("/api/notifications", headers=auth_headers(token))
    body = res.get_json()
    assert res.status_code == 200
    assert "unread_count" in body["data"]
