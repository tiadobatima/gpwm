##
## Owner: networking
##
<%
    stack_type = "vpc"
    team = "demo"
    environment = "dev"
%>
StackName: ${stack_type}-${team}-${environment}
TemplateBody: examples/consumables/aws/network/vpc.mako
Parameters:
  team: ${team}
  environment: ${environment}
  cidr: 10.0.0.0/16
  nat_availability_zones:
    - {"name": "a", "cidr": "10.0.0.0/28"}
    - {"name": "b", "cidr": "10.0.0.16/28"}
Tags:
  type: ${stack_type}
  team: ${team}
  environment: ${environment}
