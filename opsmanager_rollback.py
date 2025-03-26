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
FAILURE_CSV = "rollback_failures.csv"
os.makedirs(BACKUP_DIR, exist_ok=True)


def rollback_automation_config(group_id):
    try:
        backup_path = f"{BACKUP_DIR}/automation_config_{group_id}.json"
        if not os.path.exists(backup_path):
            logging.error(f"Automation config backup not found for Group {group_id}")
            return False

        with open(backup_path, "r") as f:
            config_data = json.load(f)

        response = requests.put(f"{BASE_URL}/groups/{group_id}/automationConfig", headers=HEADERS, json=config_data)
        response.raise_for_status()
        logging.info(f"Automation config rollback completed for Group {group_id}")
        return True
    except Exception as e:
        logging.error(f"Failed to rollback automation config for Group {group_id}: {str(e)}")
        return False


def rollback_cluster_config(group_id):
    try:
        backup_path = f"{BACKUP_DIR}/cluster_config_{group_id}.json"
        if not os.path.exists(backup_path):
            logging.error(f"Cluster config backup not found for Group {group_id}")
            return False

        with open(backup_path, "r") as f:
            cluster_data = json.load(f)

        response = requests.put(f"{BASE_URL}/groups/{group_id}/clusters", headers=HEADERS, json=cluster_data)
        response.raise_for_status()
        logging.info(f"Cluster config rollback completed for Group {group_id}")
        return True
    except Exception as e:
        logging.error(f"Failed to rollback cluster config for Group {group_id}: {str(e)}")
        return False


def get_group_ids():
    logging.info("Fetching group IDs...")
    group_ids = []
    page = 1

    while True:
        response = requests.get(f"{BASE_URL}/groups?pageNum={page}&itemsPerPage=100", headers=HEADERS)
        response.raise_for_status()
        results = response.json().get('results', [])

        if not results:
            break

        group_ids.extend([group['id'] for group in results])
        page += 1

    logging.info(f"Found {len(group_ids)} group(s)")
    return group_ids


def write_to_csv(failed_groups):
    if failed_groups:
        with open(FAILURE_CSV, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Group ID", "Error Message"])
            for group_id, error in failed_groups:
                writer.writerow([group_id, error])
        logging.info(f"Rollback failures written to {FAILURE_CSV}")
    else:
        logging.info("No rollback failures. All groups restored successfully.")


def main():
    try:
        group_ids = get_group_ids()
        failed_groups = []

        for group_id in group_ids:
            logging.info(f"Starting rollback for Group {group_id}")
            automation_success = rollback_automation_config(group_id)
            cluster_success = rollback_cluster_config(group_id)

            if not automation_success or not cluster_success:
                failed_groups.append((group_id, "Automation or Cluster rollback failed"))

        write_to_csv(failed_groups)
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
