##
## Owner: networking
##
## Dependencies:
##   - vpc
## 
## Parameters:
##   - team (required): The team owning the stack
##   - environment (required): The environment where the stack is running on (dev, prod, etc)
##   - security_groups (required): A list of security groups dictionaries defined by:
##     - service (required): The name of the service the SG is associated with
##     - ingress_rules (required): A list of SecurityGroupIngress properties
##       (see Clodformation docs)
##     - egress_rules (required): A list of SecurityGroupEgress properties
##     - notes: Just a note/explanation/TODOs about the security group
##   - security_group_rules(optional): A list of ad-hoc security groups rules
##     defined by:
##     - name(required): A meaningful name for the rule. Must be unique within
##       the stack
##     - type (required): "ingress" or "egress". No defaults. Must be specified.
##     - properties (required): A list of SecurityGroupRuleEgress or
##       SecurityGroupRuleEgress resources.
##   - vpc(required): The VPC ID 
## Notes:
##   - When referencing another security group in a SG rule, join the string
##     "SecurityGroup" with the "$service", ie if the source SG is "frontendELB",
##     the ref should be "SecurityGroupfrontendELB". This is because CF doesn't
##     allow non-alphanumeric chars in the resource name key.
##
AWSTemplateFormatVersion: "2010-09-09"
Description: Stack for security group and rules for ${team}-${environment} 
Resources:
  % for sg in security_groups:
  SecurityGroup${sg["service"]}:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for ${team}-${environment}-${sg["service"]}
      VpcId: ${vpc}
      SecurityGroupIngress: ${sg["ingress_rules"]}
      SecurityGroupEgress: ${sg["egress_rules"]}
      Tags:
        - {Key: team, Value: ${team}}
        - {Key: environment, Value: ${environment}}
        - {Key: Name, Value: ${team}-${environment}-${sg["service"]}}

  SecurityGroupRuleAllowFromSelf${sg["service"]}:
    Type: AWS::EC2::SecurityGroupIngress
    Properties:
      IpProtocol: -1
      GroupId: {"Fn::GetAtt": [SecurityGroup${sg["service"]}, GroupId]}
      SourceSecurityGroupId: {"Fn::GetAtt": [SecurityGroup${sg["service"]}, GroupId]}
  % endfor

  % for rule in security_group_rules:
  SecurityGroupRule${rule["name"]}:
    % if rule["type"] == "ingress":
    Type: AWS::EC2::SecurityGroupIngress
    % else:
    Type: AWS::EC2::SecurityGroupEgress
    % endif
    Properties: ${rule["properties"]}
  % endfor
