import requests
import time
import logging
import argparse

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://<ops-manager-url>/api/public/v1.0"
API_KEY = "<your-api-key>"
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

def get_group_ids():
    logging.info("Fetching group IDs...")
    response = requests.get(f"{BASE_URL}/groups", headers=HEADERS)
    response.raise_for_status()
    group_ids = [group['id'] for group in response.json()['results']]
    logging.info(f"Found {len(group_ids)} group(s)")
    return group_ids

def check_agent_health(group_id):
    logging.info(f"Checking agent health for Group {group_id}")
    response = requests.get(f"{BASE_URL}/groups/{group_id}/agents", headers=HEADERS)
    response.raise_for_status()
    agents = response.json()['results']
    for agent in agents:
        if agent['state'] != 'ACTIVE':
            logging.error(f"Agent {agent['hostname']} is not active. Upgrade aborted.")
            return False
    logging.info(f"All agents are active for Group {group_id}")
    return True

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

    try:
        group_ids = get_group_ids()
        for group_id in group_ids:
            logging.info(f"Processing Group {group_id}...")
            
            if not check_agent_health(group_id):
                logging.warning(f"Skipping Group {group_id} due to agent issues.")
                continue

            try:
                update_version(group_id, args.version)
                if not monitor_upgrade(group_id):
                    raise Exception("Upgrade failed.")
            except Exception as e:
                logging.error(f"Error during upgrade for Group {group_id}: {str(e)}. Initiating rollback.")
                rollback(group_id)
    except Exception as e:
        logging.critical(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
