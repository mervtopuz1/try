import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# -----------------------------
# SETTINGS
# -----------------------------

NUM_ATMS = 105
NUM_DAYS = 365

np.random.seed(42)

# -----------------------------
# CREATE DATA FOLDER
# -----------------------------

os.makedirs("data", exist_ok=True)

# -----------------------------
# ATM INFORMATION
# -----------------------------

locations = [
    "Mall",
    "University",
    "Metro",
    "Hospital",
    "City Center",
    "Residential"
]

atm_types = [
    "Indoor",
    "Outdoor"
]

atm_info = []

for atm_id in range(1, NUM_ATMS + 1):

    location = np.random.choice(locations)
    atm_type = np.random.choice(atm_types)

    atm_age = np.random.randint(1, 11)

    atm_info.append({
        "atm_id": atm_id,
        "location": location,
        "atm_type": atm_type,
        "atm_age": atm_age
    })

atm_info_df = pd.DataFrame(atm_info)

# -----------------------------
# TRANSACTION DATA
# -----------------------------

start_date = datetime(2025, 1, 1)

transaction_data = []

for atm in atm_info:

    atm_id = atm["atm_id"]
    location = atm["location"]

    # Different locations have different demand levels
    location_multiplier = {
        "Mall": 1.4,
        "University": 0.8,
        "Metro": 1.5,
        "Hospital": 1.0,
        "City Center": 1.3,
        "Residential": 0.9
    }

    base_demand = 800 * location_multiplier[location]

    for day in range(NUM_DAYS):

        date = start_date + timedelta(days=day)

        day_of_week = date.weekday()

        is_weekend = 1 if day_of_week >= 5 else 0

        # Simple holiday simulation
        is_holiday = 1 if (
            date.month in [1, 4, 5, 7, 8]
            and date.day in [1, 15]
        ) else 0

        # Weekend effect
        weekend_multiplier = 1.2 if is_weekend else 1.0

        # Salary-period effect
        salary_multiplier = 1.3 if date.day <= 7 else 1.0

        # Random daily variation
        random_multiplier = np.random.normal(1.0, 0.15)

        transactions = int(
            base_demand
            * weekend_multiplier
            * salary_multiplier
            * random_multiplier
        )

        transactions = max(transactions, 50)

        # Average withdrawal per transaction
        average_withdrawal = np.random.normal(600, 100)

        total_withdrawal = int(
            transactions * average_withdrawal
        )

        transaction_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "atm_id": atm_id,
            "location": location,
            "transactions": transactions,
            "total_withdrawal": total_withdrawal,
            "is_weekend": is_weekend,
            "is_holiday": is_holiday
        })

transactions_df = pd.DataFrame(transaction_data)

# -----------------------------
# MAINTENANCE DATA
# -----------------------------

maintenance_data = []

for atm in atm_info:

    atm_id = atm["atm_id"]
    atm_age = atm["atm_age"]

    maintenance_count = np.random.randint(5, 20)
    failure_count = np.random.randint(0, 2)

    days_since_maintenance = np.random.randint(1, 60)

    for day in range(NUM_DAYS):

        date = start_date + timedelta(days=day)

        # -----------------------------------------
        # ERROR GENERATION
        # -----------------------------------------

        # Older ATMs experience more errors
        age_factor = atm_age / 10

        network_errors = np.random.poisson(
            2 + age_factor * 3
        )

        card_reader_errors = np.random.poisson(
            0.4 + age_factor * 1.2
        )

        dispenser_errors = np.random.poisson(
            0.4 + age_factor * 1.2
        )

        # -----------------------------------------
        # FAILURE PROBABILITY
        # -----------------------------------------

        # Failure risk increases with:
        # - ATM age
        # - days since maintenance
        # - previous failures
        # - network errors
        # - card reader errors
        # - dispenser errors

        risk_score = (
            -5.2
            + 0.12 * atm_age
            + 0.015 * days_since_maintenance
            + 0.18 * failure_count
            + 0.10 * network_errors
            + 0.25 * card_reader_errors
            + 0.30 * dispenser_errors
        )

        # Convert risk score to probability
        failure_probability = 1 / (
            1 + np.exp(-risk_score)
        )

        # Keep probabilities in a reasonable range
        failure_probability = np.clip(
            failure_probability,
            0.005,
            0.60
        )

        failure_next_24h = np.random.binomial(
            1,
            failure_probability
        )

        maintenance_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "atm_id": atm_id,
            "atm_age": atm_age,
            "days_since_maintenance": days_since_maintenance,
            "maintenance_count": maintenance_count,
            "failure_count": failure_count,
            "network_errors": network_errors,
            "card_reader_errors": card_reader_errors,
            "dispenser_errors": dispenser_errors,
            "failure_next_24h": failure_next_24h
        })

        # -----------------------------------------
        # AFTER FAILURE
        # -----------------------------------------

        if failure_next_24h == 1:

            failure_count += 1
            maintenance_count += 1

            # Maintenance is performed after failure
            days_since_maintenance = 0

        else:

            days_since_maintenance += 1

# -----------------------------
# SAVE FILES
# -----------------------------

maintenance_df = pd.DataFrame(maintenance_data)

atm_info_df.to_csv(
    "data/atm_info.csv",
    index=False
)

transactions_df.to_csv(
    "data/atm_transactions.csv",
    index=False
)

maintenance_df.to_csv(
    "data/atm_maintenance.csv",
    index=False
)

# -----------------------------
# SUMMARY
# -----------------------------

print("Data generation completed!")

print(f"Number of ATMs: {NUM_ATMS}")
print(f"Number of days: {NUM_DAYS}")

print(
    f"Transaction records: {len(transactions_df)}"
)

print(
    f"Maintenance records: {len(maintenance_df)}"
)

print("\nFiles created:")

print("✓ data/atm_info.csv")
print("✓ data/atm_transactions.csv")
print("✓ data/atm_maintenance.csv")

print("\nFailure statistics:")

print(
    "Total failures:",
    maintenance_df["failure_next_24h"].sum()
)

print(
    "Failure rate:",
    round(
        maintenance_df["failure_next_24h"].mean() * 100,
        2
    ),
    "%"
)
