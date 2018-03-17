##
## Owner: infrastrucure
##
## Dependencies:
##   - subnet
##   - securitygroup
## 
## Parameters:
##   - team (required): The team owning the stack
##   - environment (required): The environment where the stack is running on (dev, prod, etc)
##   - application (required): The name of the application (frontend, zookeeper, kafka, etc)
##
<%
    service = "-".join([team, environment, application])
    tags = [
        {"Key": "team", "Value": team},
        {"Key": "environment", "Value": environment},
        {"Key": "application", "Value": application},
        {"Key": "Name", "Value": service}
    ]
    if "db_name" not in locals():
        db_name = service.replace("-", "")

    engine_major_version = ".".join(engine_version.split(".")[:-1])
    

    # dependent stack names
    subnet_stack = "subnet-{}-{}".format(team, environment)
    securitygroup_stack = "securitygroup-{}-{}".format(team, environment)

    security_groups = [get_stack_output(securitygroup_stack, "SecurityGroup{}".format(application))]
    subnet_ids = [get_stack_output(subnet_stack, subnet) for subnet in subnets]
    
    if "db_parameter_group" not in locals():
        db_parameter_group = {
            "Description": "RDS parameter group for " + service,
            "Family": engine + engine_major_version,
            "Parameters": {
                "character_set_client": "utf8",
                "character_set_connection": "utf8",
                "character_set_database": "utf8",
                "character_set_filesystem": "utf8",
                "character_set_results": "utf8",
                "character_set_server": "utf8",
                "collation_connection": "utf8_bin",
                "collation_server": "utf8_bin",
                "innodb_log_file_size": "268435456",
                "max_allowed_packet": "35651584"
            }
        }
    db_parameter_group["Tags"] = tags
                   
%>

AWSTemplateFormatVersion: "2010-09-09"
Resources:
  DBParameterGroup:
    Type: "AWS::RDS::DBParameterGroup"
    Properties: ${db_parameter_group}
        
  DBSubnetGroup: 
    Type: "AWS::RDS::DBSubnetGroup"
    Properties: 
      DBSubnetGroupDescription: Subnet group for ${service}
      SubnetIds: ${subnet_ids}
      Tags: ${tags}

  DBInstance:
    Type: "AWS::RDS::DBInstance"
    Properties: 
      DBName: ${db_name}
      AllocatedStorage: ${allocated_storage}
      DBInstanceClass: ${instance_class}
      Engine: ${engine}
      EngineVersion: ${engine_version}
      MasterUsername: ${username}
      MasterUserPassword: ${password}
      MultiAZ: ${multi_az}
      PreferredBackupWindow: "19:00-19:30"
      PreferredMaintenanceWindow: "sat:20:35-sat:21:05"
      DBSubnetGroupName: {Ref: DBSubnetGroup}
      Tags: ${tags}
      VPCSecurityGroups: ${security_groups}
    % if "deletion_policy" in locals() and deletion_policy:
    DeletionPolicy: ${deletion_policy}
    % endif

  RDSDNS:
    Type: AWS::Route53::RecordSet
    Properties:
      Name: ${service}.${hostedzone}.
      HostedZoneName: ${hostedzone}.
      Type: CNAME
      TTL: 180
      ResourceRecords:
        - {"Fn::GetAtt": [DBInstance, Endpoint.Address]}
