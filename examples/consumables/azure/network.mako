$schema: "http://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#"
contentVersion: 1.0.0.0
#parameters:
#variables:
resources:
  - type: Microsoft.Compute/availabilitySets
    name: availabilitySet1
    apiVersion: "2015-05-01-preview"
    location: West US
    properties: {}
  - name: gusstorageaccount
    type: Microsoft.Storage/storageAccounts
    apiVersion: "2017-10-01"
    sku:
      name: Standard_LRS
    kind: Storage
    location: "[resourceGroup().location]"
    location: East US
#    tags:
#    properties:
#outputs:
