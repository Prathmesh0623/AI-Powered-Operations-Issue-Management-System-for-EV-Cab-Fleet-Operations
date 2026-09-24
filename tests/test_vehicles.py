from tests.conftest import login, auth_headers


def test_list_vehicles(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = client.get("/api/vehicles", headers=auth_headers(token))
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 1


def test_get_vehicle_details(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = client.get("/api/vehicles/1", headers=auth_headers(token))
    assert res.status_code == 200
    assert res.get_json()["data"]["registration_number"] == "EV-999"


def test_get_nonexistent_vehicle(client):
    token = login(client, "operator@test.com", "Operator@123")
    res = client.get("/api/vehicles/9999", headers=auth_headers(token))
    assert res.status_code == 404


def test_create_vehicle_requires_admin(client):
    operator_token = login(client, "operator@test.com", "Operator@123")
    res = client.post("/api/vehicles", json={"registration_number": "EV-321"}, headers=auth_headers(operator_token))
    assert res.status_code == 403


def test_create_vehicle_as_admin(client):
    admin_token = login(client, "admin@test.com", "Admin@123")
    res = client.post("/api/vehicles", json={"registration_number": "EV-321", "model": "Test Model"}, headers=auth_headers(admin_token))
    assert res.status_code == 201


def test_create_vehicle_duplicate_registration_rejected(client):
    admin_token = login(client, "admin@test.com", "Admin@123")
    client.post("/api/vehicles", json={"registration_number": "EV-777"}, headers=auth_headers(admin_token))
    res = client.post("/api/vehicles", json={"registration_number": "EV-777"}, headers=auth_headers(admin_token))
    assert res.status_code == 409


def test_create_vehicle_invalid_status_rejected(client):
    admin_token = login(client, "admin@test.com", "Admin@123")
    res = client.post("/api/vehicles", json={"registration_number": "EV-555", "status": "Flying"}, headers=auth_headers(admin_token))
    assert res.status_code == 400


def test_update_vehicle_status(client):
    admin_token = login(client, "admin@test.com", "Admin@123")
    res = client.put("/api/vehicles/1", json={"status": "Maintenance"}, headers=auth_headers(admin_token))
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "Maintenance"
