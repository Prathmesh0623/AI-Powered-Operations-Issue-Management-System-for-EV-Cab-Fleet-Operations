"""
Generates a synthetic (not real) issue dataset for training the category and
priority models. Text is built from realistic phrase templates per category,
combined with randomized entities (vehicle IDs, station numbers, etc.) so the
dataset has genuine linguistic variety rather than repeated boilerplate.

Run with:  python ml/data/generate_dataset.py
Output:    dataset/issues.csv
"""
import csv
import os
import random

random.seed(42)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "issues.csv")

VEHICLE_IDS = [f"EV-{100 + i}" for i in range(30)]
STATIONS = [f"station {i}" for i in range(1, 9)]
HUBS = ["Pune Central Hub", "Mumbai East Hub", "Bangalore South Hub", "Delhi North Hub"]

# category -> (priority_weights, list of description templates)
# Templates use {vehicle}, {station}, {hub} placeholders filled at generation time.
CATEGORY_TEMPLATES = {
    "Charging": {
        "priority_weights": {"Critical": 0.15, "High": 0.40, "Medium": 0.35, "Low": 0.10},
        "templates": [
            "{vehicle} is not charging at {station}.",
            "Charging stops after a few minutes for {vehicle} at {station}.",
            "{vehicle} shows charging error code and will not start charging.",
            "Charging cable at {station} appears damaged and vehicle is not accepting charge.",
            "{vehicle} battery percentage is not increasing despite being connected at {station}.",
            "Charging session for {vehicle} keeps disconnecting randomly.",
        ],
    },
    "Battery": {
        "priority_weights": {"Critical": 0.20, "High": 0.35, "Medium": 0.35, "Low": 0.10},
        "templates": [
            "Battery percentage dropped unusually fast during the last trip for {vehicle}.",
            "{vehicle} battery temperature is unusually high during operation.",
            "{vehicle} shows sudden battery drain even when parked.",
            "Battery health indicator for {vehicle} has degraded significantly this month.",
            "{vehicle} shuts down unexpectedly, suspected battery fault.",
        ],
    },
    "Vehicle": {
        "priority_weights": {"Critical": 0.25, "High": 0.35, "Medium": 0.30, "Low": 0.10},
        "templates": [
            "{vehicle} broke down during operation near {hub}.",
            "{vehicle} AC is not working properly.",
            "{vehicle} is making unusual noise from the motor.",
            "{vehicle} brakes feel soft and need inspection.",
            "{vehicle} tyre pressure warning light is on.",
            "{vehicle} dashboard display is flickering intermittently.",
        ],
    },
    "Driver": {
        "priority_weights": {"Critical": 0.10, "High": 0.30, "Medium": 0.40, "Low": 0.20},
        "templates": [
            "Driver has not arrived for the assigned shift at {hub}.",
            "Driver reported feeling unwell and requested a shift change.",
            "Driver was unreachable during the scheduled pickup window.",
            "Driver flagged a scheduling conflict for the upcoming shift at {hub}.",
            "Driver requested additional training on the new vehicle model.",
        ],
    },
    "Ride": {
        "priority_weights": {"Critical": 0.05, "High": 0.25, "Medium": 0.45, "Low": 0.25},
        "templates": [
            "Ride was cancelled midway without explanation for {vehicle}.",
            "Customer reported a long detour during the ride.",
            "Ride pickup location did not match the app location.",
            "Ride fare shown at the end did not match the estimate.",
            "Customer waited significantly longer than the estimated arrival time.",
        ],
    },
    "Customer": {
        "priority_weights": {"Critical": 0.10, "High": 0.30, "Medium": 0.40, "Low": 0.20},
        "templates": [
            "Customer was charged but booking was not confirmed.",
            "Customer complained about driver behavior during the ride.",
            "Customer requested a refund for a cancelled ride.",
            "Customer reported the vehicle was not clean on pickup.",
            "Customer support ticket unresolved for more than 3 days.",
        ],
    },
    "Maintenance": {
        "priority_weights": {"Critical": 0.15, "High": 0.35, "Medium": 0.35, "Low": 0.15},
        "templates": [
            "{vehicle} is due for scheduled maintenance and has not been serviced.",
            "Maintenance team flagged worn brake pads on {vehicle}.",
            "{vehicle} requires software update for the onboard diagnostics system.",
            "Routine inspection revealed a coolant leak in {vehicle}.",
            "{vehicle} maintenance was delayed due to parts unavailability.",
        ],
    },
    "Technical": {
        "priority_weights": {"Critical": 0.15, "High": 0.30, "Medium": 0.35, "Low": 0.20},
        "templates": [
            "Mobile app crashes when trying to book a ride from {hub}.",
            "GPS tracking for {vehicle} is showing an incorrect location.",
            "Telematics unit on {vehicle} stopped sending data.",
            "Backend sync issue causing duplicate ride records at {hub}.",
            "Push notifications for ride status are not being delivered.",
        ],
    },
    "Payment": {
        "priority_weights": {"Critical": 0.10, "High": 0.30, "Medium": 0.40, "Low": 0.20},
        "templates": [
            "Customer payment was successful but booking was not confirmed.",
            "Duplicate payment charged for a single ride.",
            "Refund for a cancelled ride has not been processed.",
            "Payment gateway timeout occurred during checkout.",
            "Driver payout for last week's shifts is showing as pending.",
        ],
    },
    "Hub Operations": {
        "priority_weights": {"Critical": 0.15, "High": 0.30, "Medium": 0.35, "Low": 0.20},
        "templates": [
            "{hub} is operating near full capacity with no available parking.",
            "Security gate at {hub} is malfunctioning.",
            "{hub} reported a power outage affecting charging operations.",
            "Vehicle count mismatch found during the shift-change audit at {hub}.",
            "{hub} requires additional staff during the evening peak hours.",
        ],
    },
    "Other": {
        "priority_weights": {"Critical": 0.05, "High": 0.15, "Medium": 0.40, "Low": 0.40},
        "templates": [
            "General feedback submitted about the overall service experience.",
            "Suggestion received to add more charging stations near {hub}.",
            "Query raised about the loyalty rewards program.",
            "Miscellaneous request that does not fit an existing category.",
        ],
    },
}

TITLE_PREFIXES = ["Issue:", "Report:", "Alert:", ""]


def weighted_choice(weights: dict) -> str:
    labels = list(weights.keys())
    probs = list(weights.values())
    return random.choices(labels, weights=probs, k=1)[0]


def generate_row(row_id: int) -> dict:
    category = random.choice(list(CATEGORY_TEMPLATES.keys()))
    config = CATEGORY_TEMPLATES[category]
    template = random.choice(config["templates"])

    description = template.format(
        vehicle=random.choice(VEHICLE_IDS),
        station=random.choice(STATIONS),
        hub=random.choice(HUBS),
    )
    priority = weighted_choice(config["priority_weights"])
    title_prefix = random.choice(TITLE_PREFIXES)
    title = f"{title_prefix} {description}".strip()
    if len(title) > 90:
        title = title[:87] + "..."

    return {"id": row_id, "title": title, "description": description, "category": category, "priority": priority}


def main(n_rows: int = 4000):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "description", "category", "priority"])
        writer.writeheader()
        for i in range(1, n_rows + 1):
            writer.writerow(generate_row(i))
    print(f"Generated {n_rows} synthetic issue records at {OUTPUT_PATH}")
    print("NOTE: This is entirely synthetic data created for prototype/training purposes.")


if __name__ == "__main__":
    main()
