from datetime import datetime
from extensions.database import db


class Hub(db.Model):
    __tablename__ = "hubs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(255))
    capacity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    vehicles = db.relationship("Vehicle", back_populates="hub")
    drivers = db.relationship("Driver", back_populates="hub")
    charging_stations = db.relationship("ChargingStation", back_populates="hub")
    issues = db.relationship("Issue", back_populates="hub")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "capacity": self.capacity,
            "vehicle_count": len(self.vehicles),
        }
