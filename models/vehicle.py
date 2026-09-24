from datetime import datetime
from extensions.database import db

VEHICLE_STATUSES = ("Available", "On Ride", "Charging", "Maintenance", "Offline")


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(50), unique=True, nullable=False)
    model = db.Column(db.String(100))
    battery_percentage = db.Column(db.Float, default=100.0)
    status = db.Column(db.String(30), default="Available", nullable=False)

    hub_id = db.Column(db.Integer, db.ForeignKey("hubs.id"), nullable=True)
    last_maintenance_date = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hub = db.relationship("Hub", back_populates="vehicles")
    drivers = db.relationship("Driver", back_populates="vehicle")
    issues = db.relationship("Issue", back_populates="vehicle")
    maintenance_records = db.relationship("Maintenance", back_populates="vehicle")
    charging_sessions = db.relationship("ChargingSession", back_populates="vehicle")

    def to_dict(self):
        return {
            "id": self.id,
            "registration_number": self.registration_number,
            "model": self.model,
            "battery_percentage": self.battery_percentage,
            "status": self.status,
            "hub": self.hub.name if self.hub else None,
            "open_issue_count": sum(1 for i in self.issues if i.status not in ("RESOLVED", "CLOSED", "REJECTED")),
        }
