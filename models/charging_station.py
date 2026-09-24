from datetime import datetime
from extensions.database import db

STATION_STATUSES = ("Available", "Occupied", "Maintenance", "Offline")


class ChargingStation(db.Model):
    __tablename__ = "charging_stations"

    id = db.Column(db.Integer, primary_key=True)
    hub_id = db.Column(db.Integer, db.ForeignKey("hubs.id"), nullable=False)
    status = db.Column(db.String(30), default="Available", nullable=False)
    capacity = db.Column(db.Integer, default=1)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    hub = db.relationship("Hub", back_populates="charging_stations")
    sessions = db.relationship("ChargingSession", back_populates="station")

    def to_dict(self):
        return {
            "id": self.id,
            "hub": self.hub.name if self.hub else None,
            "status": self.status,
            "capacity": self.capacity,
        }
