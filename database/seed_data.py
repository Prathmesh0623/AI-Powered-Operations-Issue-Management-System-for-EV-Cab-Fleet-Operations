"""
Seeds the database with baseline reference data + a few demo records.
Run with:  python database/seed_data.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from extensions.database import db
from models.role import Role
from models.team import Team
from models.user import User
from models.hub import Hub
from models.vehicle import Vehicle
from models.driver import Driver
from models.charging_station import ChargingStation
from models.issue_category import IssueCategory

app = create_app()

with app.app_context():
    db.create_all()

    # --- Roles ---
    role_names = ["admin", "ops_manager", "operator", "maintenance"]
    roles = {}
    for name in role_names:
        role = Role.query.filter_by(name=name).first()
        if not role:
            role = Role(name=name)
            db.session.add(role)
            db.session.flush()
        roles[name] = role

    # --- Teams ---
    team_names = ["Charging & Maintenance", "Driver Operations", "Customer Support"]
    teams = {}
    for name in team_names:
        team = Team.query.filter_by(name=name).first()
        if not team:
            team = Team(name=name)
            db.session.add(team)
            db.session.flush()
        teams[name] = team

    # --- Issue categories ---
    for cat in ["Vehicle", "Battery", "Charging", "Driver", "Ride", "Customer", "Maintenance", "Technical", "Payment", "Hub Operations", "Other"]:
        if not IssueCategory.query.filter_by(name=cat).first():
            db.session.add(IssueCategory(name=cat))

    # --- Demo users (one per role) ---
    demo_users = [
        ("Asha Admin", "admin@demo.com", "Admin@123", "admin", None),
        ("Manoj Manager", "manager@demo.com", "Manager@123", "ops_manager", None),
        ("Ritu Operator", "operator@demo.com", "Operator@123", "operator", None),
        ("Sanjay Support", "support@demo.com", "Support@123", "maintenance", "Charging & Maintenance"),
    ]
    for name, email, password, role_key, team_key in demo_users:
        if not User.query.filter_by(email=email).first():
            user = User(
                name=name,
                email=email,
                role_id=roles[role_key].id,
                team_id=teams[team_key].id if team_key else None,
            )
            user.set_password(password)
            db.session.add(user)

    db.session.flush()

    # --- Hub + fleet demo data ---
    hub = Hub.query.filter_by(name="Pune Central Hub").first()
    if not hub:
        hub = Hub(name="Pune Central Hub", location="Pune, MH", capacity=50)
        db.session.add(hub)
        db.session.flush()

    if not Vehicle.query.filter_by(registration_number="EV-102").first():
        db.session.add(Vehicle(registration_number="EV-102", model="Tata Nexon EV", battery_percentage=42.0, status="Available", hub_id=hub.id))
    if not Vehicle.query.filter_by(registration_number="EV-105").first():
        db.session.add(Vehicle(registration_number="EV-105", model="MG ZS EV", battery_percentage=78.0, status="On Ride", hub_id=hub.id))

    if not Driver.query.filter_by(name="Vikram Rao").first():
        db.session.add(Driver(name="Vikram Rao", contact="9990001111", status="On Shift", hub_id=hub.id))

    if not ChargingStation.query.filter_by(hub_id=hub.id).first():
        db.session.add(ChargingStation(hub_id=hub.id, status="Available", capacity=2))

    db.session.commit()
    print("Seed data created successfully.")
    print("Demo logins:")
    for name, email, password, role_key, _ in demo_users:
        print(f"  {role_key:12s} -> {email} / {password}")
