##
## Owner: platform
##
## Dependencies: None
## 
## Parameters:
##   - team (required): The team owning the deployment/stack
##   - environment (required): The environment where the stack is running on (dev, prod, etc)
##   - service (required): The name of the application (frontend, zookeeper, kafka, etc)
##
$schema: "http://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#"
contentVersion: 1.0.0.0
parameters:
variables:
  vnet: !ARM {stack: platform-network-vnet, resource-group: platform-network-vnet-rg, output: virtualNetwork}
resources:
  - type: Microsoft.Compute/availabilitySets
    name: ${team}-${environment}-${service}-as
    apiVersion: "2017-12-01"
    location: "[resourceGroup().location]"
    properties: {}
    tags:
      team: ${team}
      environment: ${environment}
      service: ${service}
  - type: Microsoft.Storage/storageAccounts
    name: ${team}${environment}${service}001
    apiVersion: "2017-10-01"
    sku:
      name: Standard_LRS
    kind: Storage
    location: "[resourceGroup().location]"
    tags:
      team: ${team}
      environment: ${environment}
      service: ${service}
outputs:
  availabilitySet:
    type: object
    value: "[reference('${team}-${environment}-${service}-as')]"
  storageAccount:
    type: object
    value: "[reference('${team}${environment}${service}001')]"
