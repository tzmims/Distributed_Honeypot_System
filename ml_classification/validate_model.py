import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.utils import shuffle
import json
import warnings

print("[+] Loading dataset...")
df = pd.read_csv("training_dataset.csv")

print(f"[+] Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

# -------------------------------------------------------
# 1. Basic Dataset Sanity Checks
# -------------------------------------------------------
print("\n=== Dataset Overview ===")
print(df.head())
print(df.describe())

if "label" not in df.columns:
    raise ValueError("ERROR: Dataset missing required column 'label'")

X = df.drop(columns=["label"])
y = df["label"]

# -------------------------------------------------------
# 2. Train/Test Split Validation
# -------------------------------------------------------

print("\n[+] Performing train/test validation...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, shuffle=True
)

rf = RandomForestClassifier(n_estimators=250, random_state=42)
rf.fit(X_train, y_train)

y_pred = rf.predict(X_test)

print("\n=== Train/Test Classification Report ===")
print(classification_report(y_test, y_pred))
acc = accuracy_score(y_test, y_pred)
print(f"[+] Train/Test Accuracy: {acc:.4f}")

if acc == 1.0:
    warnings.warn(" PERFECT ACCURACY: This may indicate an extremely easy dataset or possible data leakage! ")

# -------------------------------------------------------
# 3. 5-Fold Cross Validation
# -------------------------------------------------------

print("\n[+] Running 5-fold cross-validation...")
rf_cv = RandomForestClassifier(n_estimators=250, random_state=42)

cv_scores = cross_val_score(rf_cv, X, y, cv=5)
print("=== Cross-Validation Scores ===")
print(cv_scores)
print(f"Mean CV Accuracy: {np.mean(cv_scores):.4f}")

if np.mean(cv_scores) == 1.0:
    warnings.warn(" PERFECT CROSS-VALIDATION SCORE: Strong sign dataset is extremely separable or leaked. ")

# -------------------------------------------------------
# 4. Random Label Sanity Test (Leakage Detection)
# -------------------------------------------------------

print("\n[+] Running random-label sanity check...")
y_random = shuffle(y, random_state=42)

rf_random = RandomForestClassifier(n_estimators=250, random_state=42)
rf_random.fit(X, y_random)

random_score = rf_random.score(X, y_random)
print(f"Random-Label Accuracy: {random_score:.4f}")

if random_score > 0.65:
    warnings.warn("""
    HIGH RANDOM-LABEL ACCURACY:
    This strongly suggests that your model is learning noise or metadata,
    meaning you may have feature leakage (e.g., timestamps, sensor names, IPs).
    """)

# -------------------------------------------------------
# 5. Feature Importance Check
# -------------------------------------------------------

print("\n[+] Evaluating feature importance...")
rf_imp = RandomForestClassifier(n_estimators=250, random_state=42)
rf_imp.fit(X, y)

importances = rf_imp.feature_importances_
importance_df = (
    pd.DataFrame({
        "feature": X.columns,
        "importance": importances
    })
    .sort_values(by="importance", ascending=False)
)

print("\n=== Feature Importance Rankings ===")
print(importance_df)

# Flag suspiciously dominant features
if importance_df["importance"].iloc[0] > 0.90:
    warnings.warn(f"""
    SINGLE FEATURE DOMINATES MODEL:
    Feature '{importance_df['feature'].iloc[0]}' contributes over 90% of model's decision power.
    This suggests the dataset may be too simple or imbalanced.
    """)

print("\n[+] Validation complete.")
