##
## Owner: infrastructure
##
<%
    stack_type = "common"
    team = "demo"
%>
StackName: ${stack_type}-${team}
TemplateBody: tests/consumables/account/${stack_type}.mako
Parameters:
  team: ${team}
  s3_bucket: ${team}-island-dev-srcd-io
  hostedzone: island.dev.srcd.io
Tags:
  team: ${team}
  type: ${stack_type}
