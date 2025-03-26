
# MongoDB-Patch-Automation

# ✅ Required Packages
Here are the required packages:

requests → For making API calls to OpsManager. pip install requests

logging → For generating logs (already included in Python).

json → For handling JSON data (already included in Python).

csv → For writing reports to CSV (already included in Python).

argparse → For command-line argument parsing (already included in Python).

os → For file operations (already included in Python).

time → For monitoring and adding time delays (already included in Python).

Only requests needs to be installed if it is not present.

# Step by Step exeuction

✅ Step 1: Take Backup Before Upgrade
Purpose: Ensure you have a backup of all configurations in case of any failures.

Script: python opsmanager_backup.py

# What Happens:

- It takes a backup of automation configuration and cluster configuration for all group IDs.

- It triggers on-demand snapshots.

- Stores the backup files in the backup_data/ directory.

- Logs the agent health status to agent_health.csv.

✅ Step 2: Perform MongoDB Patch Upgrade
Purpose: Upgrade MongoDB to the desired version.

Script: python mongodb_upgrade.py --version <target-version>
example - python mongodb_upgrade.py --version 7.0.16

# What Happens:

- Fetches all group IDs.

- Checks if all agents are active.

- Upgrades MongoDB to the specified version for each group.

- Monitors the upgrade progress.

- In case of any failure, it triggers a rollback using the rollback logic within the script.

- Generates logs, and detailed upgrade reports in upgrade_summary.csv and agent_issues.csv

✅ Step 3: Rollback (If Needed)
Purpose: Revert to the previous state using the backed-up data if the upgrade fails or issues are observed.

Script: python opsmanager_rollback.py

# What Happens:

Uses backup files from backup_data/ to restore both automation and cluster configurations.

Validates if the rollback is successful for all group IDs.

Tracks any rollback failures and logs them into rollback_failures.csv.

Generates a summary confirming rollback success.


# what it covers 

This Python script covers all your requirements:

- Authentication: Uses API Key for secure access.

- Dynamic Group ID Retrieval: Fetches all group IDs using the API.

- Agent Health Check: Ensures all agents are active before upgrading.

- Version Upgrade: Updates the patch version to 7.0.16.

- Monitoring: Tracks the upgrade status with periodic checks.

- Rollback: Rolls back to the previous version in case of failure.

Make sure to replace <ops-manager-url> and <your-api-key> with actual values. Let me know if you'd like further tweaks or explanations!

# Check if requests is installed 

pip install requests

# while running parallel executions , make sure these are executed below
pip install requests argparse logging


# Command to run upgrade without param

python3 mongodb_upgrade.py

# Command to run upgrade with param

python3 mongodb_upgrade.py --version 7.0.16
