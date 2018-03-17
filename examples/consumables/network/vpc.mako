##
## Owner: networking
##
## Dependencies: None
## 
## Parameters:
##   - team (required): The team owning the stack
##   - environment (required): The environment where the stack is running on (dev, prod, etc)
##   - cidr (required): The CIDR for the VPC
##   - nat_availability_zones (required): A list of dictionaries representing the CIDR and
##     availability zone for the default NAT gateways:
##     - name (required): Availability zone name ("a", "b", "c"...)
##     - cidr (required): the CIDR NAT gateway's subnet.
##     
AWSTemplateFormatVersion: "2010-09-09"
Description: VPC stack for ${team}-${environment}

Resources:
  VPC:
    Type: "AWS::EC2::VPC"
    Metadata:
      Name: ${team}-${environment}
    Properties: 
      CidrBlock: ${cidr}
      EnableDnsSupport: true
      EnableDnsHostnames: true
      InstanceTenancy: default
      Tags: 
        - {Key: team, Value: ${team}}
        - {Key: version, Value: ${environment}}
        - {Key: Name, Value: ${team}-${environment}}

  InternetGateway:
    Type: "AWS::EC2::InternetGateway"
    Properties: 
      Tags: 
        - {Key: team, Value: ${team}}
        - {Key: type, Value: ${environment}}
        - {Key: Name, Value: ${team}-${environment}}

  VPCGatewayAttachment: 
    Type: "AWS::EC2::VPCGatewayAttachment"
    Properties:
      VpcId: {Ref: VPC}
      InternetGatewayId: {Ref: InternetGateway}

  RouteTablePublic:
    Type: "AWS::EC2::RouteTable"
    Properties:
      VpcId: {Ref: VPC}
      Tags: 
        - {Key: team, Value: ${team}}
        - {Key: type, Value: ${environment}}
        - {Key: Name, Value: ${team}-${environment}-public}

  Route:
    Type: "AWS::EC2::Route"
    DependsOn: VPCGatewayAttachment
    Properties:
      RouteTableId: {Ref: RouteTablePublic}
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: {Ref: InternetGateway}

  % for az in nat_availability_zones:
  SubnetAZ${az["name"]}:
    Type: "AWS::EC2::Subnet"
    Properties:
      VpcId: {Ref: VPC}
      CidrBlock: ${az["cidr"]}
      AvailabilityZone: {"Fn::Sub": "<%text>$</%text>{AWS::Region}${az["name"]}"}
      MapPublicIpOnLaunch: false
      Tags:
        - {Key: team, Value: ${team}}
        - {Key: type, Value: ${environment}}
        - {Key: Name, Value: ${team}-${environment}-nat-${az["name"]}-public}

  RouteTableAssociationAZ${az["name"]}:
    Type: "AWS::EC2::SubnetRouteTableAssociation"
    Properties:
      SubnetId: {Ref: SubnetAZ${az["name"]}}
      RouteTableId: {Ref: RouteTablePublic}

  RouteTablePrivateAZ${az["name"]}:
    Type: "AWS::EC2::RouteTable"
    Properties:
      VpcId: {Ref: VPC}
      Tags: 
        - {Key: team, Value: ${team}}
        - {Key: environment, Value: nat}
        - {Key: Name, Value: ${team}-${environment}-private-${az["name"]}}

  EIPNATAZ${az["name"]}:
    Type: "AWS::EC2::EIP"
    Properties:
      Domain: vpc

  NatGatewayAZ${az["name"]}:
    Type: "AWS::EC2::NatGateway"
    Properties:
      AllocationId: {"Fn::GetAtt": [EIPNATAZ${az["name"]}, AllocationId]}
      SubnetId: {Ref: SubnetAZ${az["name"]}}

  RoutePrivateAZ${az["name"]}:
    Type: "AWS::EC2::Route"
    Properties:
      RouteTableId: {Ref: RouteTablePrivateAZ${az["name"]}}
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: {Ref: NatGatewayAZ${az["name"]}}

  % endfor

##  SecurityGroup:
##    Type: "AWS::EC2::SecurityGroup"
##    Properties:
##      GroupDescription: VPC common security group
##      VpcId: {Ref: VPC}
##      Tags:
##        - {Key: team, Value: ${team}}
##        - {Key: type, Value: ${environment}}
##        - {Key: Name, Value: ${team}-${environment}}
##
##  % if "SearchDomains" in vars():
##  DHCPOptions:
##    Type: "AWS::EC2::DHCPOptions"
##    Properties:
##      DomainName: ${SearchDomains}
##      DomainNameServers:
##        - AmazonProvidedDNS
##      Tags:
##        - {Key: team, Value: ${team}}
##        - {Key: type, Value: ${environment}}
##        - {Key: Name, Value: ${team}-${environment}-${version}}
##
##  VPCDHCPOptionsAssociation:
##    Type: "AWS::EC2::VPCDHCPOptionsAssociation"
##    Properties:
##      DhcpOptionsId: {Ref: DHCPOptions}
##      VpcId: {Ref: VPC}
##  % endif

Outputs:
  CidrBlock:
    Value: {"Fn::GetAtt": [VPC, CidrBlock]}
    Export:
      Name: {"Fn::Sub": "<%text>$</%text>{AWS::StackName}-CidrBlock"}

