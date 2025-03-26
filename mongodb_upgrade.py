import requests
import time

BASE_URL = "https://<ops-manager-url>/api/public/v1.0"
API_KEY = "<your-api-key>"
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

def get_group_ids():
    response = requests.get(f"{BASE_URL}/groups", headers=HEADERS)
    response.raise_for_status()
    return [group['id'] for group in response.json()['results']]

def check_agent_health(group_id):
    response = requests.get(f"{BASE_URL}/groups/{group_id}/agents", headers=HEADERS)
    response.raise_for_status()
    agents = response.json()['results']
    for agent in agents:
        if agent['state'] != 'ACTIVE':
            print(f"Agent {agent['hostname']} is not active. Upgrade aborted.")
            return False
    return True

def get_automation_config(group_id):
    response = requests.get(f"{BASE_URL}/groups/{group_id}/automationConfig", headers=HEADERS)
    response.raise_for_status()
    return response.json()

def update_version(group_id, version="7.0.16"):
    config = get_automation_config(group_id)
    for process in config.get('processes', []):
        process['version'] = version

    response = requests.put(
        f"{BASE_URL}/groups/{group_id}/automationConfig",
        headers=HEADERS,
        json=config
    )
    response.raise_for_status()
    print(f"Upgrade initiated for Group {group_id}")

def monitor_upgrade(group_id):
    print(f"Monitoring upgrade for Group {group_id}...")
    while True:
        time.sleep(30)
        config = get_automation_config(group_id)
        states = [process.get('lastKnownVersion') == process['version'] for process in config.get('processes', [])]
        if all(states):
            print(f"Upgrade completed successfully for Group {group_id}")
            return True
        print("Upgrade still in progress...")

def rollback(group_id):
    print(f"Rolling back changes for Group {group_id}")
    config = get_automation_config(group_id)
    for process in config.get('processes', []):
        process['version'] = process.get('lastKnownVersion', process['version'])
    
    response = requests.put(
        f"{BASE_URL}/groups/{group_id}/automationConfig",
        headers=HEADERS,
        json=config
    )
    response.raise_for_status()
    print(f"Rollback completed for Group {group_id}")

def main():
    try:
        group_ids = get_group_ids()
        for group_id in group_ids:
            print(f"Processing Group {group_id}...")
            
            if not check_agent_health(group_id):
                print(f"Skipping Group {group_id} due to agent issues.")
                continue

            try:
                update_version(group_id)
                if not monitor_upgrade(group_id):
                    raise Exception("Upgrade failed.")
            except Exception as e:
                print(f"Error in Group {group_id}: {str(e)}. Initiating rollback.")
                rollback(group_id)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
