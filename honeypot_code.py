import requests
import time
import json
from pathlib import Path
import shutil
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def read_logs(filepath: Path) -> list[str]:
    logs = []
    with open(filepath, "r") as lines:
        for line in lines:
            line = line.strip() 
            log = json.loads(line)
            logs.append(log)
    return logs

def send_logs(filepath: Path, master_url: str) -> bool:
    logs = read_logs(filepath)

    data = {"Log": logs, "source_file": filepath.name}
    try:
        resp = requests.post(master_url, json=data, timeout=10)
        resp.raise_for_status()
        destination = SENT_DIR / filepath.name
        shutil.move(str(filepath), str(destination))
        return True
    except Exception as e:
        logging.error(f"Failed to send {filepath}: {e}")
        return False
    
def push_to_master(master_url: str, wait: int = 30):
    while True:
        files = sorted(LOGS_DIR.glob("*.json"))
        for f in files:
            if f.parent == SENT_DIR:
                continue
            send_logs(f, master_url)
        time.sleep(wait)

if __name__ == "__main__":
    MASTER_URL = "http://IPADDER:6967/submit"
    LOGS_DIR = Path("/cowrie/cowrie/var/logs")
    SENT_DIR = LOGS_DIR / "sent"
    LOGS_DIR.mkdir(exist_ok=True, parents=True)
    SENT_DIR.mkdir(exist_ok=True, parents=True)
    
    logging.info(f"Worker started. Sending logs from '{LOGS_DIR}' to {MASTER_URL}")
    push_to_master(MASTER_URL, 30)
