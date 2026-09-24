from tests.conftest import login, auth_headers


def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["success"] is True


def test_login_success(client):
    res = client.post("/api/auth/login", json={"email": "manager@test.com", "password": "Manager@123"})
    body = res.get_json()
    assert res.status_code == 200
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert body["data"]["user"]["role"] == "ops_manager"


def test_login_wrong_password(client):
    res = client.post("/api/auth/login", json={"email": "manager@test.com", "password": "wrong"})
    assert res.status_code == 401
    assert res.get_json()["success"] is False


def test_login_missing_fields(client):
    res = client.post("/api/auth/login", json={"email": "manager@test.com"})
    assert res.status_code == 400


def test_login_unknown_user(client):
    res = client.post("/api/auth/login", json={"email": "ghost@test.com", "password": "whatever"})
    assert res.status_code == 401


def test_me_requires_auth(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_returns_current_user(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = client.get("/api/auth/me", headers=auth_headers(token))
    assert res.status_code == 200
    assert res.get_json()["data"]["email"] == "operator@test.com"


def test_protected_route_rejects_missing_token(client):
    res = client.get("/api/issues")
    assert res.status_code == 401


def test_protected_route_rejects_garbage_token(client):
    res = client.get("/api/issues", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code in (401, 422)
