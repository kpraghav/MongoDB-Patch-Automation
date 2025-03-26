import requests
import json
import logging
import os
import csv

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://<ops-manager-url>/api/public/v1.0"
API_KEY = "<your-api-key>"
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

BACKUP_DIR = "backup_data"
os.makedirs(BACKUP_DIR, exist_ok=True)

# CSV Path for Agent Health
AGENT_CSV_PATH = os.path.join(BACKUP_DIR, "agent_health.csv")

def get_group_ids():
    logging.info("Fetching group IDs...")
    response = requests.get(f"{BASE_URL}/groups", headers=HEADERS)
    response.raise_for_status()
    group_ids = [group['id'] for group in response.json()['results']]
    logging.info(f"Found {len(group_ids)} group(s)")
    return group_ids

def backup_automation_config(group_id):
    logging.info(f"Backing up automation config for Group {group_id}")
    response = requests.get(f"{BASE_URL}/groups/{group_id}/automationConfig", headers=HEADERS)
    response.raise_for_status()
    config_data = response.json()
    with open(f"{BACKUP_DIR}/automation_config_{group_id}.json", "w") as f:
        json.dump(config_data, f, indent=4)
    logging.info(f"Automation config for Group {group_id} backed up.")

def backup_cluster_config(group_id):
    logging.info(f"Backing up cluster config for Group {group_id}")
    response = requests.get(f"{BASE_URL}/groups/{group_id}/clusters", headers=HEADERS)
    response.raise_for_status()
    cluster_data = response.json()
    with open(f"{BACKUP_DIR}/cluster_config_{group_id}.json", "w") as f:
        json.dump(cluster_data, f, indent=4)
    logging.info(f"Cluster config for Group {group_id} backed up.")

def trigger_snapshot(group_id):
    logging.info(f"Triggering on-demand snapshot for Group {group_id}")
    payload = {"force": True}
    response = requests.post(f"{BASE_URL}/groups/{group_id}/backup/snapshots", headers=HEADERS, json=payload)
    if response.status_code == 201:
        logging.info(f"Snapshot triggered successfully for Group {group_id}")
    else:
        logging.warning(f"Failed to trigger snapshot for Group {group_id}: {response.json()}")

def check_agent_health(group_id):
    logging.info(f"Checking agent health for Group {group_id}")
    response = requests.get(f"{BASE_URL}/groups/{group_id}/agents", headers=HEADERS)
    response.raise_for_status()
    agents = response.json()['results']
    with open(AGENT_CSV_PATH, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Group ID", "Agent Hostname", "State"])
        for agent in agents:
            writer.writerow([group_id, agent['hostname'], agent['state']])
            logging.info(f"Agent {agent['hostname']} in Group {group_id} is {agent['state']}")

def main():
    try:
        group_ids = get_group_ids()
        with open(AGENT_CSV_PATH, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Group ID", "Agent Hostname", "State"])
        for group_id in group_ids:
            backup_automation_config(group_id)
            backup_cluster_config(group_id)
            trigger_snapshot(group_id)
            check_agent_health(group_id)
        logging.info("Backup completed for all groups. Agent health details are saved to CSV.")
    except Exception as e:
        logging.error(f"Error occurred during backup: {str(e)}")

if __name__ == "__main__":
    main()
