import json
import pandas as pd
from pathlib import Path
from collections import defaultdict
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import numpy as np

# ----------------------------------
# CONFIG
# ----------------------------------
BENIGN_FILE = "benign.jsonl"
MALICIOUS_FILE = "malicious.jsonl"
DATASET_OUT = "training_dataset.csv"

MODEL_OUT = "model.pkl"
VECTORIZER_OUT = "vectorizer.pkl"
FEATURE_COLS_OUT = "feature_columns.json"

# ----------------------------------
# Load JSONL
# ----------------------------------
def load_jsonl(path):
    rows = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except:
                pass
    return rows

print("[+] Loading JSON logs...")
benign_logs = load_jsonl(BENIGN_FILE)
mal_logs = load_jsonl(MALICIOUS_FILE)

# ----------------------------------
# Group by session
# ----------------------------------
def group_by_session(logs):
    sessions = defaultdict(list)
    for event in logs:
        sid = event.get("session")
        if sid:
            sessions[sid].append(event)
    return sessions

benign_sessions = group_by_session(benign_logs)
mal_sessions = group_by_session(mal_logs)

# ----------------------------------
# Feature extraction per session
# ----------------------------------
def extract_features(events):
    feature_dict = {
        "num_events": len(events),
        "num_failed_logins": 0,
        "num_commands": 0,
        "num_unique_commands": 0,
        "num_downloads": 0,
        "num_uploads": 0,
        "session_duration": 0.0,
    }

    commands = []
    timestamps = []

    for e in events:
        eventid = e.get("eventid", "")
        if "timestamp" in e:
            timestamps.append(e["timestamp"])

        if "login.failed" in eventid:
            feature_dict["num_failed_logins"] += 1

        if "command.input" in eventid:
            feature_dict["num_commands"] += 1
            commands.append(e.get("input", ""))

        if "file_download" in eventid:
            feature_dict["num_downloads"] += 1

        if "file_upload" in eventid:
            feature_dict["num_uploads"] += 1

    feature_dict["num_unique_commands"] = len(set(commands))

    if len(timestamps) >= 2:
        try:
            ts_sorted = sorted(timestamps)
            start = pd.to_datetime(ts_sorted[0])
            end = pd.to_datetime(ts_sorted[-1])
            feature_dict["session_duration"] = (end - start).total_seconds()
        except:
            pass

    return feature_dict


# ----------------------------------
# Build labeled dataset
# ----------------------------------
print("[+] Building feature dataset...")

dataset = []

for sid, events in benign_sessions.items():
    row = extract_features(events)
    row["label"] = 0
    dataset.append(row)

for sid, events in mal_sessions.items():
    row = extract_features(events)
    row["label"] = 1
    dataset.append(row)

df = pd.DataFrame(dataset)
df.fillna(0, inplace=True)

df.to_csv(DATASET_OUT, index=False)
print(f"[+] Dataset written to {DATASET_OUT}")
print(df.head())

# ----------------------------------
# Train-test split
# ----------------------------------
X = df.drop("label", axis=1)
y = df["label"]

feature_columns = list(X.columns)

# Save feature list
json.dump(feature_columns, open(FEATURE_COLS_OUT, "w"))

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

# ----------------------------------
# Train Random Forest
# ----------------------------------
print("[+] Training Random Forest Model...")

model = RandomForestClassifier(
    n_estimators=250,
    max_depth=None,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

pred = model.predict(X_test)

print("\n=== Classification Report ===")
print(classification_report(y_test, pred))

# Save model
joblib.dump(model, MODEL_OUT)
print(f"[+] Model saved to {MODEL_OUT}")
