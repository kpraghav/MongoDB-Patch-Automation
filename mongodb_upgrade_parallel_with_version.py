import requests
import logging
import time
import concurrent.futures
import argparse
from logging.handlers import RotatingFileHandler

# Configure Logging
log_file = 'upgrade_script.log'
logging.basicConfig(handlers=[RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)],
                    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://<ops-manager-url>/api/public/v1.0"
API_KEY = "<your-api-key>"
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Exponential backoff
def request_with_backoff(url, method='GET', json_data=None):
    retries = 5
    backoff = 1
    for attempt in range(retries):
        try:
            if method == 'GET':
                response = requests.get(url, headers=HEADERS)
            elif method == 'PUT':
                response = requests.put(url, headers=HEADERS, json=json_data)

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
        return [group['id'] for group in response.json().get('results', [])]
    return []

def check_agent_health(group_id):
    logging.info(f"Checking agent health for Group {group_id}")
    url = f"{BASE_URL}/groups/{group_id}/agents"
    response = request_with_backoff(url)
    if response:
        agents = response.json().get('results', [])
        unhealthy_agents = [a for a in agents if a['stateName'] != 'HEALTHY']
        if unhealthy_agents:
            logging.error(f"Unhealthy agents found in Group {group_id}")
            return False
        logging.info(f"All agents are healthy in Group {group_id}")
        return True
    return False

def perform_upgrade(group_id, target_version):
    logging.info(f"Initiating upgrade for Group {group_id} to version {target_version}")
    url = f"{BASE_URL}/groups/{group_id}/automationConfig"
    response = request_with_backoff(url)
    if response:
        config = response.json()
        for process in config.get('processes', []):
            process['version'] = target_version
        upgrade_response = request_with_backoff(url, method='PUT', json_data=config)
        if upgrade_response:
            logging.info(f"Upgrade initiated successfully for Group {group_id}")
        else:
            logging.error(f"Upgrade failed for Group {group_id}, initiating rollback")
            rollback_config(group_id, config)

def rollback_config(group_id, backup_config):
    logging.info(f"Rolling back Group {group_id}")
    url = f"{BASE_URL}/groups/{group_id}/automationConfig"
    rollback_response = request_with_backoff(url, method='PUT', json_data=backup_config)
    if rollback_response:
        logging.info(f"Rollback completed successfully for Group {group_id}")
    else:
        logging.error(f"Rollback failed for Group {group_id}")

def process_group(group_id, target_version):
    if check_agent_health(group_id):
        perform_upgrade(group_id, target_version)
    else:
        logging.error(f"Skipping upgrade for Group {group_id} due to unhealthy agents")

def main():
    parser = argparse.ArgumentParser(description="MongoDB Upgrade Script")
    parser.add_argument('--version', required=True, help='Target MongoDB version for upgrade (e.g., 7.0.16)')
    args = parser.parse_args()
    target_version = args.version

    try:
        group_ids = get_group_ids()
        if not group_ids:
            logging.error("No group IDs found. Exiting.")
            return

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(lambda group_id: process_group(group_id, target_version), group_ids)
        logging.info("Upgrade completed for all applicable groups.")
    except Exception as e:
        logging.error(f"Error occurred during upgrade: {e}")

if __name__ == "__main__":
    main()
