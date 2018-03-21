##
## Owner: Networking
##
## Dependencies: None
## 
## Parameters:
##   - team (required): The team owning the deployment/stack
##
$schema: "http://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#"
contentVersion: 1.0.0.0
#parameters:
variables:
resources:
  - type: Microsoft.Network/virtualNetworks
    name: vnet
    apiVersion: "2017-10-01"
    location: "[resourceGroup().location]"
    properties:
      addressSpace:
        addressPrefixes:
          - 10.0.0.0/16
    tags:
      team: ${team}
outputs:
  virtualNetwork:
    type: object
    value: "[reference('vnet')]"
