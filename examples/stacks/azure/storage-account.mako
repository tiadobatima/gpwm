<%
    team = "accounting"
    environment = "dev"
    service = "web"
%>

name: ${team}-${environment}-${service}
type: azure
resourceGroup:
  name: ${team}-${environment}-${service}-rg
  location: East US
  tags:
    team: ${team}
    environment: ${environment}
    service: ${service}
  persist: false
template: examples/consumables/azure/storage-account.mako
parameters:
  team: ${team}
  environment: ${environment}
  service: ${service}
mode: Incremental
#templateLink: https://example.com/path/to/template.json
#parametersLink: https://example.com/path/to/parameters.json
xoxoxo: ${utils.get_azure_stack_output(resource_group="platform-network-vnet-rg",
deployment="platform-network-vnet", output="virtualNetwork")}
