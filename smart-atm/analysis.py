import pandas as pd

# Verileri oku
transactions = pd.read_csv("data/atm_transactions.csv")
maintenance = pd.read_csv("data/atm_maintenance.csv")
atm_info = pd.read_csv("data/atm_info.csv")

# -------------------------
# TRANSACTION DATA
# -------------------------

print("=== TRANSACTION DATA ===")

print("Shape:", transactions.shape)

print("\nColumns:")
print(transactions.columns.tolist())

print("\nFirst 5 rows:")
print(transactions.head())

print("\nStatistics:")
print(transactions.describe())

print("\nMissing values:")
print(transactions.isnull().sum())


# -------------------------
# MAINTENANCE DATA
# -------------------------

print("\n\n=== MAINTENANCE DATA ===")

print("Shape:", maintenance.shape)

print("\nColumns:")
print(maintenance.columns.tolist())

print("\nFirst 5 rows:")
print(maintenance.head())

print("\nMissing values:")
print(maintenance.isnull().sum())


# -------------------------
# ATM INFO
# -------------------------

print("\n\n=== ATM INFO ===")

print("Shape:", atm_info.shape)

print("\nFirst 5 rows:")
print(atm_info.head())