import json
import time
import hashlib
from pathlib import Path
import joblib
import pandas as pd
from model_trainer import extract_features

AGG_FILE = Path("aggregated_logs.jsonl")
OUTPUT_FILE = Path("classified_sessions.jsonl")
SESSIONS_FILE = Path("seen_sessions.txt")

MODEL = "model.pkl"
FEATURES = "feature_columns.json"

model = joblib.load(MODEL)
feature_columns = json.load(open(FEATURES))

# ----------------------------------
# Helper
# ----------------------------------
def compute_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def load_seen_sessions():
    if not SESSIONS_FILE.exists():
        return set()
    else:
        print("Log already processed")
    return set(line.strip() for line in SESSIONS_FILE.open())

def save_seen_session(session_hash):
    with open(SESSIONS_FILE, "a") as f:
        f.write(session_hash + "\n")

def make_feature_df(feats_dict):
    """
    Create a one-row DataFrame using feature_columns order.
    This ensures sklearn receives feature names exactly as during training,
    avoiding the "X does not have valid feature names" warning.
    """
    # Ensure every expected column exists; if not present, fill with 0
    row = [feats_dict.get(col, 0) for col in feature_columns]
    df = pd.DataFrame([row], columns=feature_columns)
    return df

# ----------------------------------
# Main classifier
# ----------------------------------
def classify_events(events):
    feats = extract_features(events)
    X_df = make_feature_df(feats)
    pred = model.predict(X_df)[0]
    try:
        prob = float(model.predict_proba(X_df)[0][1])
    except Exception:
        prob = None

    return pred, prob, feats

# ----------------------------------
# Main loop
# ----------------------------------
def run_daemon():
    seen = load_seen_sessions()

    sessions = {}

    print("[INFO] Classifier daemon starting...")

    while True:
        if not AGG_FILE.exists():
            time.sleep(5)
            print("Agg file not found/empty")
            continue

        with open(AGG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    print("file empty")
                    continue

                try:
                    entry = json.loads(line)
                except:
                    continue

                sid = entry.get("session")
                if not sid:
                    continue
                
                if sid not in sessions:
                    sessions[sid] = []

                sessions[sid].append(entry)
        
        # Now classify completed sessions
        for sid, events in sessions.items():

            session_hash = compute_hash(sid)

            if session_hash in seen:
                print("Log already seen")
                continue

            pred, prob, feats = classify_events(events)

            result = {
                "session": sid,
                "prediction": "malicious" if pred == 1 else "benign",
                "probability": prob,
                "features": feats,
                "event_count": len(events),
            }

            with open(OUTPUT_FILE, "a") as out:
                out.write(json.dumps(result) + "\n")

            save_seen_session(session_hash)
            print(f"[+] Classified session {sid}: {result['prediction']}")

        time.sleep(10)

if __name__ == "__main__":
    run_daemon()
