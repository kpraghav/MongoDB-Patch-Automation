# what it covers 

This Python script covers all your requirements:

- Authentication: Uses API Key for secure access.

- Dynamic Group ID Retrieval: Fetches all group IDs using the API.

- Agent Health Check: Ensures all agents are active before upgrading.

- Version Upgrade: Updates the patch version to 7.0.16.

- Monitoring: Tracks the upgrade status with periodic checks.

- Rollback: Rolls back to the previous version in case of failure.

Make sure to replace <ops-manager-url> and <your-api-key> with actual values. Let me know if you'd like further tweaks or explanations!



# MongoDB-Patch-Automation



4. PUT /api/public/v1.0/groups/{groupId}/automationConfig

   Request body - 
{
  "processes": [
    {
      "_id": "rs0_1",
      "hostname": "mongodb-node1.example.com",
      "args2_6": {
        "net": {
          "port": 27017
        },
        "replication": {
          "replSetName": "rs0"
        }
      },
      "version": "7.0.16"
    },
    {
      "_id": "rs0_2",
      "hostname": "mongodb-node2.example.com",
      "args2_6": {
        "net": {
          "port": 27017
        },
        "replication": {
          "replSetName": "rs0"
        }
      },
      "version": "7.0.16"
    }
  ],
  "authSchemaVersion": 5
}
