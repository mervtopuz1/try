import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ==========================================
# 1. LOAD DATA
# ==========================================

df = pd.read_csv("data/cash_model_data.csv")

df["date"] = pd.to_datetime(df["date"])

df = pd.get_dummies(
    df,
    columns=["location", "atm_type"],
    dtype=int
)

print("Dataset loaded!")
print("Shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

# ==========================================
# 2. SORT BY DATE
# ==========================================

df = df.sort_values("date")


# ==========================================
# 3. FEATURES
# ==========================================
features = [
    # ATM information
    "atm_id",
    "atm_age",

    # Transaction information
    "transactions",

    # Calendar
    "is_weekend",
    "is_holiday",
    "day_of_week",
    "month",
    "day_of_month",

    # Historical withdrawal
    "previous_day_withdrawal",
    "withdrawal_7d_avg",
    "withdrawal_14d_avg",
    "withdrawal_30d_avg",
    "withdrawal_7d_std",

    # Transaction history
    "previous_day_transactions",
    "transactions_7d_avg",

    # Same day previous week
    "same_day_last_week",

    # Location
    "location_City Center",
    "location_Hospital",
    "location_Metro",
    "location_University",

    # ATM type
    "atm_type_Indoor",
    "atm_type_Outdoor"
]

target = "next_day_withdrawal"

X = df[features]
y = df[target]


# ==========================================
# 4. TRAIN / TEST SPLIT
# ==========================================

split_index = int(len(df) * 0.8)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]


print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# ==========================================
# 5. XGBOOST MODEL
# ==========================================

model = XGBRegressor(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    random_state=42
)


# ==========================================
# 6. TRAIN
# ==========================================

print("\nTraining XGBoost model...")

model.fit(X_train, y_train)

print("Training completed!")


# ==========================================
# 7. PREDICTIONS
# ==========================================

predictions = model.predict(X_test)


# ==========================================
# 8. EVALUATION
# ==========================================

mae = mean_absolute_error(y_test, predictions)

rmse = mean_squared_error(
    y_test,
    predictions
) ** 0.5

r2 = r2_score(
    y_test,
    predictions
)

# Ortalama yüzde hata
mape = (
    abs((y_test.values - predictions) / y_test.values).mean()
    * 100
)


print("\n==============================")
print("MODEL PERFORMANCE")
print("==============================")

print(f"MAE : {mae:,.2f} TL")
print(f"RMSE: {rmse:,.2f} TL")
print(f"R²  : {r2:.4f}")
print(f"MAPE: {mape:.2f}%")


# ==========================================
# 9. FEATURE IMPORTANCE
# ==========================================

importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\n==============================")
print("FEATURE IMPORTANCE")
print("==============================")

print(importance.to_string(index=False))


# ==========================================
# 10. PREDICTION RESULTS
# ==========================================

results = pd.DataFrame({
    "date": df.iloc[split_index:]["date"].values,
    "atm_id": df.iloc[split_index:]["atm_id"].values,
    "actual": y_test.values,
    "predicted": predictions
})

results["error"] = (
    results["actual"] - results["predicted"]
)

results["absolute_error"] = (
    abs(results["error"])
)

results["error_percentage"] = (
    results["absolute_error"]
    / results["actual"]
    * 100
)


print("\n==============================")
print("SAMPLE PREDICTIONS")
print("==============================")

print(
    results.head(10).to_string(index=False)
)


# ==========================================
# 11. WORST PREDICTIONS
# ==========================================

worst_predictions = results.sort_values(
    "absolute_error",
    ascending=False
).head(10)

print("\n==============================")
print("10 LARGEST ERRORS")
print("==============================")

print(
    worst_predictions.to_string(index=False)
)


# ==========================================
# 12. SAVE RESULTS
# ==========================================

results.to_csv(
    "data/cash_predictions.csv",
    index=False
)

importance.to_csv(
    "data/feature_importance.csv",
    index=False
)

print("\nResults saved:")
print("✓ data/cash_predictions.csv")
print("✓ data/feature_importance.csv")


# ==========================================
# 13. FEATURE IMPORTANCE GRAPH
# ==========================================

plt.figure(figsize=(10, 6))

plt.barh(
    importance["feature"],
    importance["importance"]
)

plt.xlabel("Importance")
plt.ylabel("Feature")
plt.title("XGBoost Feature Importance")

plt.gca().invert_yaxis()

plt.tight_layout()

plt.savefig(
    "data/feature_importance.png"
)

plt.show()


# ==========================================
# 14. ACTUAL VS PREDICTED
# ==========================================

plt.figure(figsize=(10, 6))

plt.plot(
    results["actual"].values[:200],
    label="Actual"
)

plt.plot(
    results["predicted"].values[:200],
    label="Predicted"
)

plt.xlabel("Test Sample")
plt.ylabel("Withdrawal (TL)")
plt.title("Actual vs Predicted Cash Demand")

plt.legend()

plt.tight_layout()

plt.savefig(
    "data/actual_vs_predicted.png"
)

plt.show()