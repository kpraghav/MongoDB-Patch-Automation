
# MongoDB-Patch-Automation

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
