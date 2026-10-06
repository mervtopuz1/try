import pandas as pd

# ==========================================
# 1. LOAD DATA
# ==========================================

transactions = pd.read_csv("data/atm_transactions.csv")
atm_info = pd.read_csv("data/atm_info.csv")

transactions["date"] = pd.to_datetime(transactions["date"])

# ATM ve tarih sırasına göre sırala
transactions = transactions.sort_values(["atm_id", "date"])


# ==========================================
# 2. MERGE ATM INFORMATION
# ==========================================

df = transactions.drop(
    columns=["location"],
    errors="ignore"
)

df = df.merge(
    atm_info[["atm_id", "location", "atm_type", "atm_age"]],
    on="atm_id",
    how="left"
)

print("ATM information merged!")


# ==========================================
# 3. CALENDAR FEATURES
# ==========================================

df["day_of_week"] = df["date"].dt.dayofweek
df["month"] = df["date"].dt.month
df["day_of_month"] = df["date"].dt.day


# ==========================================
# 4. PREVIOUS DAY
# ==========================================

df["previous_day_withdrawal"] = (
    df.groupby("atm_id")["total_withdrawal"]
    .shift(1)
)


# ==========================================
# 5. WITHDRAWAL AVERAGES
# ==========================================

df["withdrawal_7d_avg"] = (
    df.groupby("atm_id")["total_withdrawal"]
    .transform(
        lambda x: x.shift(1).rolling(7).mean()
    )
)

df["withdrawal_14d_avg"] = (
    df.groupby("atm_id")["total_withdrawal"]
    .transform(
        lambda x: x.shift(1).rolling(14).mean()
    )
)

df["withdrawal_30d_avg"] = (
    df.groupby("atm_id")["total_withdrawal"]
    .transform(
        lambda x: x.shift(1).rolling(30).mean()
    )
)


# ==========================================
# 6. WITHDRAWAL VOLATILITY
# ==========================================

df["withdrawal_7d_std"] = (
    df.groupby("atm_id")["total_withdrawal"]
    .transform(
        lambda x: x.shift(1).rolling(7).std()
    )
)


# ==========================================
# 7. TRANSACTION FEATURES
# ==========================================

df["previous_day_transactions"] = (
    df.groupby("atm_id")["transactions"]
    .shift(1)
)

df["transactions_7d_avg"] = (
    df.groupby("atm_id")["transactions"]
    .transform(
        lambda x: x.shift(1).rolling(7).mean()
    )
)


# ==========================================
# 8. SAME DAY LAST WEEK
# ==========================================

df["same_day_last_week"] = (
    df.groupby("atm_id")["total_withdrawal"]
    .shift(7)
)


# ==========================================
# 9. TARGET
# ==========================================

df["next_day_withdrawal"] = (
    df.groupby("atm_id")["total_withdrawal"]
    .shift(-1)
)


# ==========================================
# 10. REMOVE MISSING VALUES
# ==========================================

df = df.dropna()


# ==========================================
# 11. SAVE
# ==========================================

df.to_csv(
    "data/cash_model_data.csv",
    index=False
)


# ==========================================
# 12. CHECK
# ==========================================

print("Cash model dataset updated!")

print("Shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nATM features:")
print("✓ location")
print("✓ atm_type")
print("✓ atm_age")

print("\nTime-series features:")
print("✓ withdrawal_7d_avg")
print("✓ withdrawal_14d_avg")
print("✓ withdrawal_30d_avg")
print("✓ withdrawal_7d_std")
print("✓ same_day_last_week")

print("\nMissing values:")
print(df.isnull().sum())