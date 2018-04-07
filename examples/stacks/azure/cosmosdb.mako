<%
    team = "accounting"
    environment = "dev"
    service = "web"
%>

name: ${team}-${environment}-${service}-cosmosdb
type: azure
resourceGroup:
  name: ${team}-${environment}-${service}-rg
  location: East US
  tags:
    team: ${team}
    environment: ${environment}
    service: ${service}
  persist: true
template: examples/consumables/azure/cosmosdb.mako
parameters:
  team: ${team}
  environment: ${environment}
  service: ${service}
  dbname: gus-db
mode: Incremental
