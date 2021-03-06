<%
    team = "platform"
    stack_type = "network"
%>

name: ${team}-${stack_type}-vnet
type: azure
resourceGroup:
  name: ${team}-${stack_type}-vnet-rg
  location: East US
  tags:
    team: ${team}
  persist: false
template: examples/consumables/azure/network.mako
parameters:
  team: ${team}
mode: Incremental

