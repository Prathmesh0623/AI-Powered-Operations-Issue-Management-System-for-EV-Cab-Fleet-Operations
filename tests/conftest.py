import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"

from app import create_app
from extensions.database import db
from models.role import Role
from models.team import Team
from models.user import User
from models.hub import Hub
from models.vehicle import Vehicle


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)

    with app.app_context():
        db.create_all()
        _seed_minimal(db)
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _seed_minimal(db):
    """Minimal fixture data every test can rely on."""
    admin_role = Role(name="admin")
    manager_role = Role(name="ops_manager")
    operator_role = Role(name="operator")
    maintenance_role = Role(name="maintenance")
    db.session.add_all([admin_role, manager_role, operator_role, maintenance_role])
    db.session.flush()

    team = Team(name="Charging & Maintenance")
    db.session.add(team)
    db.session.flush()

    admin = User(name="Admin User", email="admin@test.com", role_id=admin_role.id)
    admin.set_password("Admin@123")
    manager = User(name="Manager User", email="manager@test.com", role_id=manager_role.id)
    manager.set_password("Manager@123")
    operator = User(name="Operator User", email="operator@test.com", role_id=operator_role.id)
    operator.set_password("Operator@123")
    db.session.add_all([admin, manager, operator])
    db.session.flush()

    hub = Hub(name="Test Hub", location="Test City", capacity=10)
    db.session.add(hub)
    db.session.flush()

    vehicle = Vehicle(registration_number="EV-999", model="Test EV", battery_percentage=50.0, status="On Ride", hub_id=hub.id)
    db.session.add(vehicle)
    db.session.commit()


def login(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    return res.get_json()["data"]["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
