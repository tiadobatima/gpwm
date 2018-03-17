name: gusDeployment
type: azure
resourceGroup:
  name: gusResourceGroup
  location: eastus
  tags:
    team: gus
    environment: dev
    service: web
  persist: false
template: examples/consumables/azure/network.mako
#templateLink: https://example.com/path/to/template.json
#parameters:
#  minVMs: 1
#  maxVMs: 3
#parametersLink: https://example.com/path/to/parameters.json
mode: Incremental

