import requests
import json
import logging
import os
import concurrent.futures
import time
from logging.handlers import RotatingFileHandler

# Configure Logging
log_file = 'backup_script.log'
logging.basicConfig(handlers=[RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)],
                    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://<ops-manager-url>/api/public/v1.0"
API_KEY = "<your-api-key>"
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

BACKUP_DIR = "backup_data"
os.makedirs(BACKUP_DIR, exist_ok=True)

# Exponential backoff
def request_with_backoff(url, method='GET', json_data=None):
    retries = 5
    backoff = 1
    for attempt in range(retries):
        try:
            if method == 'GET':
                response = requests.get(url, headers=HEADERS)
            elif method == 'POST':
                response = requests.post(url, headers=HEADERS, json=json_data)

            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logging.warning(f"Attempt {attempt + 1}/{retries} failed: {e}")
            time.sleep(backoff)
            backoff *= 2
    logging.error(f"Failed to get response from {url} after {retries} attempts.")
    return None

def get_group_ids():
    logging.info("Fetching group IDs...")
    url = f"{BASE_URL}/groups"
    response = request_with_backoff(url)
    if response:
        group_ids = [group['id'] for group in response.json().get('results', [])]
        logging.info(f"Found {len(group_ids)} group(s)")
        return group_ids
    return []

def backup_automation_config(group_id):
    logging.info(f"Backing up automation config for Group {group_id}")
    url = f"{BASE_URL}/groups/{group_id}/automationConfig"
    response = request_with_backoff(url)
    if response:
        with open(f"{BACKUP_DIR}/automation_config_{group_id}.json", "w") as f:
            json.dump(response.json(), f, indent=4)
        logging.info(f"Automation config backed up for Group {group_id}")

def backup_cluster_config(group_id):
    logging.info(f"Backing up cluster config for Group {group_id}")
    url = f"{BASE_URL}/groups/{group_id}/clusters"
    response = request_with_backoff(url)
    if response:
        with open(f"{BACKUP_DIR}/cluster_config_{group_id}.json", "w") as f:
            json.dump(response.json(), f, indent=4)
        logging.info(f"Cluster config backed up for Group {group_id}")

def trigger_snapshot(group_id):
    logging.info(f"Triggering on-demand snapshot for Group {group_id}")
    url = f"{BASE_URL}/groups/{group_id}/backup/snapshots"
    payload = {"force": True}
    response = request_with_backoff(url, method='POST', json_data=payload)
    if response and response.status_code == 201:
        logging.info(f"Snapshot triggered successfully for Group {group_id}")
    else:
        logging.warning(f"Failed to trigger snapshot for Group {group_id}")

def process_group(group_id):
    try:
        backup_automation_config(group_id)
        backup_cluster_config(group_id)
        trigger_snapshot(group_id)
    except Exception as e:
        logging.error(f"Error processing Group {group_id}: {e}")

def main():
    try:
        group_ids = get_group_ids()
        if not group_ids:
            logging.error("No group IDs found. Exiting.")
            return

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(process_group, group_ids)
        logging.info("Backup completed for all groups.")
    except Exception as e:
        logging.error(f"Error occurred during backup: {e}")

if __name__ == "__main__":
    main()
