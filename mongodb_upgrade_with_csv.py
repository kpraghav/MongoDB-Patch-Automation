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
    
    down_agents = [agent['hostname'] for agent in agents if agent['state'] != 'ACTIVE']
    if down_agents:
        logging.error(f"Group {group_id} has down agents: {down_agents}")
        return False, down_agents
    
    logging.info(f"All agents are active for Group {group_id}")
    return True, []

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

def monitor_upgrade(group_id, version):
    logging.info(f"Monitoring upgrade progress for Group {group_id}")
    while True:
        time.sleep(30)
        config = get_automation_config(group_id)
        states = [process.get('version') == version for process in config.get('processes', [])]
        
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

def write_to_csv(filename, data, headers):
    logging.info(f"Writing data to {filename}")
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

def main():
    parser = argparse.ArgumentParser(description="MongoDB Ops Manager Patch Upgrade Script")
    parser.add_argument('--version', required=True, help="MongoDB patch version to upgrade to")
    args = parser.parse_args()

    patch_results = []
    down_agents_data = []

    try:
        group_ids = get_group_ids()
        for group_id in group_ids:
            logging.info(f"Processing Group {group_id}...")
            
            health_status, down_agents = check_agent_health(group_id)
            if not health_status:
                logging.warning(f"Skipping Group {group_id} due to agent issues.")
                down_agents_data.append({'group_id': group_id, 'down_agents': ', '.join(down_agents)})
                continue

            try:
                update_version(group_id, args.version)
                if monitor_upgrade(group_id, args.version):
                    patch_results.append({'group_id': group_id, 'status': 'Success'})
                else:
                    raise Exception("Upgrade failed.")
            except Exception as e:
                logging.error(f"Error during upgrade for Group {group_id}: {str(e)}. Initiating rollback.")
                rollback(group_id)
                patch_results.append({'group_id': group_id, 'status': 'Failed'})

        # Write results to CSV
        write_to_csv('patch_results.csv', patch_results, ['group_id', 'status'])
        write_to_csv('down_agents.csv', down_agents_data, ['group_id', 'down_agents'])
        logging.info("Patch results and agent issues have been written to CSV files.")
    
    except Exception as e:
        logging.critical(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
