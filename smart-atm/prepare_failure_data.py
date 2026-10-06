import pandas as pd

# Load maintenance data
df = pd.read_csv("data/atm_maintenance.csv")

df["date"] = pd.to_datetime(df["date"])

print("Maintenance data loaded!")
print("Shape:", df.shape)

# Features we will use
features = [
    "atm_age",
    "days_since_maintenance",
    "maintenance_count",
    "failure_count",
    "network_errors",
    "card_reader_errors",
    "dispenser_errors"
]

target = "failure_next_24h"

# Create model dataset
model_df = df[["date", "atm_id"] + features + [target]].copy()

# Remove missing values
model_df = model_df.dropna()

# Save
model_df.to_csv("data/failure_model_data.csv", index=False)

print("\nFailure model dataset created!")
print("Shape:", model_df.shape)

print("\nColumns:")
print(model_df.columns.tolist())

print("\nTarget distribution:")
print(model_df[target].value_counts())

print("\nFailure rate:")
print(model_df[target].mean() * 100, "%")