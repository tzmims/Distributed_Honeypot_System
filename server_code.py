from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import json
from pathlib import Path
import requests
import datetime
import hashlib

DATA_DIR = Path("master_data")
AGG_FILE = DATA_DIR / "aggregated_logs.jsonl"
WORKERS_FILE = DATA_DIR / "workers.json"

app = FastAPI(title="Master Server")

def append_aggregate(entries):
    existing_hahses = set()

    with open(AGG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                entry_hash = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
                existing_hahses.add(entry_hash)
            except json.JSONDecodeError:
                continue
    
    with open(AGG_FILE, "a", encoding="utf-8") as f:
        new_count = 0
        for entry in entries:
            entry_hash = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
            if entry_hash not in existing_hahses:
                f.write(json.dumps(entry) + "\n")
                existing_hahses.add(entry_hash)
                new_count +=1 
    return new_count

def load_workers():
    with open(WORKERS_FILE, "r", encoding="utf-8") as f:
        data = f.read().strip()
        if not data:
            return {}
        return json.loads(data)
    
def save_workers(workers):
    with open(WORKERS_FILE, "w", encoding="utf-8") as f:
        json.dump(workers, f, indent=2)

def register_worker(host_name: str, ip: str):
    workers = load_workers()
    entry = workers.get(host_name, {})
    entry.update({
        "last_seen": datetime.datetime.utcnow().isoformat() + "Z",
        "ip": ip
    })
    workers[host_name] = entry
    save_workers(workers)

@app.post("/submit")
async def submit_log(request: Request):
    payload = await request.json()
    
    if isinstance(payload, dict) and "Log" in payload:
        logs = payload["Log"]
        source_file = payload.get("source_file", "unknown")
    elif isinstance(payload, list):
        logs = payload
        source_file = "unknown"
    else:
        return {"status": "error", "message": "Invalid payload format"}
    
    client = request.client
    client_ip = client.host if client else "unknown"
    register_worker(host_name=source_file, ip=client_ip)

    added = append_aggregate(logs)

    return {
        "status": "ok",
        "received": len(logs),
        "added_to_aggregate": added,
        "source_file": source_file,
        "worker_ip": client_ip
    }

@app.get("/aggregate")
def get_aggregate():
    with open(AGG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    return content

@app.get("/workers")
def get_workers():
    workers = load_workers()
    return workers

if __name__ == "__main__":
    uvicorn.run("server_code:app", host="0.0.0.0", port=6967, log_level="info")