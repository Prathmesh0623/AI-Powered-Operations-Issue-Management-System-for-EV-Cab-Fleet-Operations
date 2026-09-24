from datetime import datetime
from extensions.database import db

MAINTENANCE_STATUSES = ("Scheduled", "In Progress", "Completed", "Cancelled")


class Maintenance(db.Model):
    __tablename__ = "maintenance_records"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=True)

    maintenance_type = db.Column(db.String(100))
    scheduled_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(30), default="Scheduled", nullable=False)
    technician_team = db.Column(db.String(100))
    resolution_notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = db.relationship("Vehicle", back_populates="maintenance_records")
    issue = db.relationship("Issue", back_populates="maintenance_records")

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle": self.vehicle.registration_number if self.vehicle else None,
            "maintenance_type": self.maintenance_type,
            "status": self.status,
            "technician_team": self.technician_team,
        }
