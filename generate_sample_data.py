"""
Simulates 3 machines with runtime-based wear: as runtime_hours climbs,
temperature/vibration/pressure drift out of normal range, culminating
in a failure event for machines pushed close to end-of-life. This
gives the model both healthy and failed examples to learn from.

Usage:
    python app.py                                 # in one terminal
    python sample_data/generate_sample_data.py     # in another
"""

import random
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5004"

MACHINES = [
    {"machine_name": "Compressor Unit A", "machine_type": "compressor", "max_runtime": 1800, "will_fail": True},
    {"machine_name": "Pump Station B", "machine_type": "pump", "max_runtime": 900, "will_fail": False},
    {"machine_name": "Conveyor Motor C", "machine_type": "motor", "max_runtime": 2200, "will_fail": True},
]


def simulate_readings(machine_id, max_runtime, will_fail, days=60):
    start_date = datetime.today() - timedelta(days=days)
    runtime = 0.0

    for day in range(days):
        reading_date = start_date + timedelta(days=day)
        runtime += max_runtime / days + random.uniform(-2, 2)
        wear_fraction = min(runtime / max_runtime, 1.0)

        temperature = 55 + wear_fraction * 35 + random.uniform(-2, 2)
        vibration = 1.0 + wear_fraction * 4.0 + random.uniform(-0.2, 0.2)
        pressure = 5.0 + (wear_fraction * 2 if random.random() > 0.5 else -wear_fraction * 2) + random.uniform(-0.3, 0.3)

        is_last_day = day == days - 1
        failed = 1 if (will_fail and is_last_day and wear_fraction > 0.9) else 0

        requests.post(
            f"{BASE_URL}/api/readings",
            json={
                "machine_id": machine_id,
                "reading_date": reading_date.strftime("%Y-%m-%d"),
                "runtime_hours": round(runtime, 2),
                "temperature": round(temperature, 2),
                "vibration": round(vibration, 3),
                "pressure": round(pressure, 2),
                "failed": failed,
            },
        )


def main():
    machine_ids = []
    for m in MACHINES:
        resp = requests.post(
            f"{BASE_URL}/api/machines",
            json={"machine_name": m["machine_name"], "machine_type": m["machine_type"]},
        ).json()
        machine_ids.append(resp["machine_id"])
        print("Registered machine:", resp)

    for m, mid in zip(MACHINES, machine_ids):
        simulate_readings(mid, m["max_runtime"], m["will_fail"])
        print(f"Seeded 60 days of sensor readings for machine_id={mid}")

    print("\n--- Failure risk predictions ---")
    for m, mid in zip(MACHINES, machine_ids):
        result = requests.post(f"{BASE_URL}/api/predict/{mid}").json()
        print(f"{m['machine_name']:20s} -> risk={result['failure_risk']}% level={result['risk_level']} (source: {result['score_source']})")


if __name__ == "__main__":
    main()
