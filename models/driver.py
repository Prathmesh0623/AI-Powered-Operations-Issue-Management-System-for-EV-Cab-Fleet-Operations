from datetime import datetime
from extensions.database import db

DRIVER_STATUSES = ("Available", "On Shift", "Off Shift", "Unavailable")


class Driver(db.Model):
    __tablename__ = "drivers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact = db.Column(db.String(50))
    status = db.Column(db.String(30), default="Available", nullable=False)

    hub_id = db.Column(db.Integer, db.ForeignKey("hubs.id"), nullable=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    hub = db.relationship("Hub", back_populates="drivers")
    vehicle = db.relationship("Vehicle", back_populates="drivers")
    issues = db.relationship("Issue", back_populates="driver")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "contact": self.contact,
            "status": self.status,
            "hub": self.hub.name if self.hub else None,
            "vehicle": self.vehicle.registration_number if self.vehicle else None,
        }
