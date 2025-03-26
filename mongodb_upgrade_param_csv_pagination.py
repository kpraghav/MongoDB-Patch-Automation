import requests
import time
import logging
import argparse
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

PATCH_STATUS_FILE = 'patch_status.csv'
AGENT_HEALTH_FILE = 'agent_health.csv'

def write_to_csv(file_name, data, headers):
    with open(file_name, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

# Fetch all group IDs with pagination
def get_group_ids():
    logging.info("Fetching group IDs with pagination...")
    group_ids = []
    page = 1
    limit = 100

    while True:
        response = requests.get(f"{BASE_URL}/groups?pageNum={page}&itemsPerPage={limit}", headers=HEADERS)
        response.raise_for_status()
        results = response.json()['results']

        if not results:
            break

        group_ids.extend([group['id'] for group in results])
        page += 1

    logging.info(f"Total Groups Found: {len(group_ids)}")
    return group_ids

def check_agent_health(group_id):
    logging.info(f"Checking agent health for Group {group_id}")
    response = requests.get(f"{BASE_URL}/groups/{group_id}/agents", headers=HEADERS)
    response.raise_for_status()
    agents = response.json()['results']

    down_agents = []
    for agent in agents:
        if agent['state'] != 'ACTIVE':
            logging.error(f"Agent {agent['hostname']} is not active.")
            down_agents.append({'groupId': group_id, 'hostname': agent['hostname'], 'state': agent['state']})
    
    return len(down_agents) == 0, down_agents

def get_automation_config(group_id):
    logging.info(f"Fetching automation config for Group {group_id}")
    response = requests.get(f"{BASE_URL}/groups/{group_id}/automationConfig", headers=HEADERS)
    response.raise_for_status()
    return response.json()

def update_version(group_id, version):
    logging.info(f"Initiating version upgrade to {version} for Group {group_id}")
    config = get_automation_config(group_id)
    
    for process in config.get('processes', []):
        process['version'] = version

    response = requests.put(
        f"{BASE_URL}/groups/{group_id}/automationConfig",
        headers=HEADERS,
        json=config
    )
    response.raise_for_status()
    logging.info(f"Upgrade initiated successfully for Group {group_id}")

def monitor_upgrade(group_id):
    logging.info(f"Monitoring upgrade progress for Group {group_id}")
    while True:
        time.sleep(30)
        config = get_automation_config(group_id)
        states = [process.get('lastKnownVersion') == process['version'] for process in config.get('processes', [])]
        if all(states):
            logging.info(f"Upgrade completed successfully for Group {group_id}")
            return True
        logging.info("Upgrade still in progress...")

def rollback(group_id):
    logging.warning(f"Initiating rollback for Group {group_id}")
    config = get_automation_config(group_id)
    
    for process in config.get('processes', []):
        process['version'] = process.get('lastKnownVersion', process['version'])
    
    response = requests.put(
        f"{BASE_URL}/groups/{group_id}/automationConfig",
        headers=HEADERS,
        json=config
    )
    response.raise_for_status()
    logging.info(f"Rollback completed for Group {group_id}")

def main():
    parser = argparse.ArgumentParser(description="MongoDB Ops Manager Patch Upgrade Script")
    parser.add_argument('--version', required=True, help="MongoDB patch version to upgrade to")
    args = parser.parse_args()

    patch_status = []
    agent_health_data = []

    try:
        group_ids = get_group_ids()
        for group_id in group_ids:
            logging.info(f"Processing Group {group_id}...")
            all_agents_active, down_agents = check_agent_health(group_id)

            if down_agents:
                agent_health_data.extend(down_agents)

            if not all_agents_active:
                patch_status.append({'groupId': group_id, 'status': 'Failed - Agent Issues'})
                continue

            try:
                update_version(group_id, args.version)
                if monitor_upgrade(group_id):
                    patch_status.append({'groupId': group_id, 'status': 'Success'})
                else:
                    raise Exception("Upgrade failed.")
            except Exception as e:
                logging.error(f"Error during upgrade for Group {group_id}: {str(e)}. Initiating rollback.")
                rollback(group_id)
                patch_status.append({'groupId': group_id, 'status': 'Failed - Rollback Executed'})
    
    except Exception as e:
        logging.critical(f"Unexpected error: {str(e)}")

    write_to_csv(PATCH_STATUS_FILE, patch_status, ['groupId', 'status'])
    write_to_csv(AGENT_HEALTH_FILE, agent_health_data, ['groupId', 'hostname', 'state'])
    logging.info("Patch status and agent health details written to CSV files.")

if __name__ == "__main__":
    main()
