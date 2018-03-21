##
## Owner: networking
##
<%
    stack_type = "subnet"
    team = "demo"
    environment = "dev"
%>
StackName: ${stack_type}-${team}-${environment}
TemplateBody: examples/consumables/aws/network/subnet.mako
Parameters:
  team: ${team}
  environment: ${environment}
  vpc: !Cloudformation {stack: vpc-${team}-${environment}, output: vpcid}
  subnets:
    - zone: ELB
      cidr: 10.0.1.0/24
      space: public
      az: a
      map_public_ip: "true"
    - zone: app
      cidr: 10.0.2.0/24
      space: private
      az: a
    - zone: data
      cidr: 10.0.3.0/28
      space: private
      az: a
    - zone: data
      cidr: 10.0.3.16/28
      space: private
      az: b
Tags:
  type: ${stack_type}
  team: ${team}
  environment: ${environment}

