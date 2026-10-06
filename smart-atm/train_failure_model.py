import pandas as pd
import numpy as np

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score
)

# ==========================================
# 1. LOAD DATA
# ==========================================

df = pd.read_csv("data/failure_model_data.csv")

print("Dataset loaded!")
print("Shape:", df.shape)

# ==========================================
# 2. FEATURES / TARGET
# ==========================================

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

X = df[features]
y = df[target]

# ==========================================
# 3. TRAIN / TEST SPLIT
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# ==========================================
# 4. HANDLE CLASS IMBALANCE
# ==========================================

negative = (y_train == 0).sum()
positive = (y_train == 1).sum()

scale_pos_weight = negative / positive

print("\nClass distribution:")
print("Normal:", negative)
print("Failure:", positive)
print("scale_pos_weight:", scale_pos_weight)

# ==========================================
# 5. TRAIN XGBOOST
# ==========================================

print("\nTraining XGBoost failure model...")

model = XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    scale_pos_weight=scale_pos_weight,
    random_state=42
)

model.fit(X_train, y_train)

print("Training completed!")

# ==========================================
# 6. PREDICTIONS
# ==========================================

y_probability = model.predict_proba(X_test)[:, 1]

# Default threshold
y_pred = (y_probability >= 0.5).astype(int)

# ==========================================
# 7. PERFORMANCE
# ==========================================

print("\n==============================")
print("FAILURE MODEL PERFORMANCE")
print("==============================")

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

roc_auc = roc_auc_score(y_test, y_probability)
pr_auc = average_precision_score(y_test, y_probability)

print("\nROC-AUC:", round(roc_auc, 4))
print("PR-AUC :", round(pr_auc, 4))

# ==========================================
# 8. FEATURE IMPORTANCE
# ==========================================

importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\nFeature Importance:")
print(importance.to_string(index=False))

# ==========================================
# 9. SAVE FEATURE IMPORTANCE
# ==========================================

importance.to_csv(
    "data/failure_feature_importance.csv",
    index=False
)

# ==========================================
# 10. SAVE PREDICTIONS
# ==========================================

results = df.loc[X_test.index, ["date", "atm_id"]].copy()

results["actual_failure"] = y_test.values
results["failure_probability"] = y_probability
results["predicted_failure"] = y_pred

results["risk_level"] = pd.cut(
    results["failure_probability"],
    bins=[-0.01, 0.20, 0.50, 1.0],
    labels=["LOW", "MEDIUM", "HIGH"]
)

results.to_csv(
    "data/failure_predictions.csv",
    index=False
)

print("\nResults saved:")
print("✓ data/failure_predictions.csv")
print("✓ data/failure_feature_importance.csv")