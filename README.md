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
