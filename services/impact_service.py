"""
Operational Impact Engine — Phase 10.

Deliberately rule-based, not ML: impact reasoning must be transparent and
auditable to the operations manager, not a black box. Each factor adds
points to a running score; the final score maps to LOW/MEDIUM/HIGH/CRITICAL.
Thresholds are defined as module-level constants so they're easy to tune
without touching the scoring logic itself.

This function never claims certainty — output is always framed as
"potential impact", consistent with the rest of the AI layer.
"""
from models.vehicle import Vehicle
from models.driver import Driver

PRIORITY_POINTS = {"Critical": 4, "High": 3, "Medium": 1, "Low": 0}
VEHICLE_ACTIVE_STATUSES = {"On Ride"}

# Score thresholds -> impact level
SCORE_THRESHOLDS = [
    (7, "CRITICAL"),
    (5, "HIGH"),
    (3, "MEDIUM"),
]
DEFAULT_LEVEL = "LOW"


def assess_impact(issue):
    """
    Returns (impact_level: str, explanation: str).
    Factors considered (only those that apply to this issue are scored):
      - Issue priority
      - Whether the linked vehicle is currently active (On Ride)
      - Number of backup (Available) vehicles at the same hub
      - Whether a driver depends on the linked vehicle
      - Hub utilization (vehicles in use vs hub capacity)
    """
    score = 0
    reasons = []

    priority_points = PRIORITY_POINTS.get(issue.priority, 0)
    score += priority_points
    if priority_points > 0:
        reasons.append(f"issue priority is {issue.priority}")

    vehicle = issue.vehicle
    backup_count = None
    if vehicle:
        if vehicle.status in VEHICLE_ACTIVE_STATUSES:
            score += 3
            reasons.append(f"{vehicle.registration_number} is currently active (On Ride)")

        if vehicle.hub_id:
            backup_count = Vehicle.query.filter_by(hub_id=vehicle.hub_id, status="Available").count()
            if backup_count == 0:
                score += 3
                reasons.append("no backup vehicles are currently available at the same hub")
            elif backup_count == 1:
                score += 2
                reasons.append("only one backup vehicle is currently available at the same hub")
            elif backup_count <= 3:
                score += 1
                reasons.append(f"only {backup_count} backup vehicles are currently available at the same hub")

        dependent_driver = Driver.query.filter_by(vehicle_id=vehicle.id, status="On Shift").first()
        if dependent_driver:
            score += 2
            reasons.append(f"driver {dependent_driver.name} is on shift and depends on this vehicle")

    hub = issue.hub or (vehicle.hub if vehicle else None)
    if hub and hub.capacity:
        active_vehicles = sum(1 for v in hub.vehicles if v.status in ("On Ride", "Charging"))
        utilization = active_vehicles / hub.capacity
        if utilization >= 0.85:
            score += 2
            reasons.append(f"{hub.name} is operating near capacity ({active_vehicles}/{hub.capacity} vehicles active)")

    level = DEFAULT_LEVEL
    for threshold, label in SCORE_THRESHOLDS:
        if score >= threshold:
            level = label
            break

    if reasons:
        explanation = f"Potential impact is {level} because " + "; ".join(reasons) + "."
    else:
        explanation = f"Potential impact is {level} — no significant contributing factors were found."

    return level, explanation
