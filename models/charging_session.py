from datetime import datetime
from extensions.database import db


class ChargingSession(db.Model):
    __tablename__ = "charging_sessions"

    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey("charging_stations.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)

    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)

    station = db.relationship("ChargingStation", back_populates="sessions")
    vehicle = db.relationship("Vehicle", back_populates="charging_sessions")

    def to_dict(self):
        return {
            "id": self.id,
            "station_id": self.station_id,
            "vehicle": self.vehicle.registration_number if self.vehicle else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }
