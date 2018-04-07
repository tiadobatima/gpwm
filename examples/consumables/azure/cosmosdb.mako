##
## Owner: platform
##
## Dependencies: None
## 
## Parameters:
##   - team (required): The team owning the deployment/stack
##   - environment (required): The environment where the stack is running on (dev, prod, etc)
##   - service (required): The name of the application (frontend, zookeeper, kafka, etc)
##   - dbname (required): the name of the database
##
$schema: "http://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#"
contentVersion: 1.0.0.0
resources:
  - type: Microsoft.DocumentDB/databaseAccounts
    name: ${team}-${environment}-${service}-cosmosdb
    apiVersion: "2015-04-08"
    location: "[resourceGroup().location]"
    kind: MongoDB
    properties:
      databaseAccountOfferType: Standard
      name: ${dbname}
    tags:
      team: ${team}
      environment: ${environment}
      service: ${service}
outputs:
  cosmosDB:
    type: object
    value: "[reference('${team}-${environment}-${service}-cosmosdb')]"
