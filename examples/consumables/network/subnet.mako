##
## Owner: networking
##
## Dependencies:
##   - vpc
## 
## Parameters:
##   - team (required): The team owning the stack
##   - environment (required): The environment where the stack is running on (dev, prod, etc)
##   - subnets (required): A list of subnet dictionaries defined by:
##     - az (required): The availability zone for the subnet
##     - cidr (required): The CIDR for the subnet
##     - space (required): "public" or "private". Defines if the subnet is attached to a
##       public or private route table
##     - zone (required): The name for the isolation zone for the subnet. It should be the
##       service name, but it doesn't have to in cases where multiple services share
##       the same subnet
##
<%
    vpc_stack = "vpc-{}-{}".format(team, environment)
%>
AWSTemplateFormatVersion: "2010-09-09"
Description: Subnet stack for ${team}-${environment}
Resources:
% for subnet in subnets:
<%
    subnet_resource_name = "{}{}AZ{}".format(
        subnet["zone"].capitalize(),
        subnet["space"].capitalize(),
        subnet["az"]
    )
    if subnet["space"] == "private":
        route_table_output = "RouteTablePrivateAZ{}".format(subnet["az"])
    else:
        route_table_output = "RouteTablePublic"
%>
         
  Subnet${subnet_resource_name}:
    Type: "AWS::EC2::Subnet"
    Properties:
      VpcId: !Cloudformation {stack: ${vpc_stack}, output: VPC}
      CidrBlock: ${subnet["cidr"]}
      AvailabilityZone: {"Fn::Sub": "<%text>$</%text>{AWS::Region}${subnet['az']}"}
      MapPublicIpOnLaunch: ${subnet.get("map_public_ip", "false")}
      Tags:
        - {Key: team, Value: ${team}}
        - {Key: environment, Value: ${environment}}
        - {Key: space, Value: ${subnet["space"]}}
        - {Key: Name, Value: ${team}-${environment}-${subnet["zone"]}-${subnet["space"]}-${subnet["az"]}}

  RouteTableAssociation${subnet_resource_name}:
    Type: "AWS::EC2::SubnetRouteTableAssociation"
    Properties:
      SubnetId: {Ref: Subnet${subnet_resource_name}}
      RouteTableId: !Cloudformation {stack: ${vpc_stack}, output: ${route_table_output}}

%endfor
