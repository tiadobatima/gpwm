##
## Owner: infrastrucure
##
## Dependencies:
##   - subnet
##   - securitygroup
##   - accesspolicy
## 
## Parameters:
##   - team (required): The team owning the stack
##   - environment (required): The environment where the stack is running on (dev, prod, etc)
##   - application (required): The name of the application (frontend, zookeeper, kafka, etc)
##   - ami (required): The AMI id
##   - associate_public_ip_address (optional): "true" or "false"
##   - block_device_mappings (optional): A list of BlockDeviceMappings (see
##     cloudformation docs)
##   - build_id (optional): The build ID used to assemble default user-data. optional
##     if proving user_data as a parameter
##   - cluster_size (require): A dictionary with "desired", "min" and "max" keys
##     representing the cluster size
##   - creation_policy (optional):
##   - elb (optional): A dictionary with the following keys representing an ELB
##     - cross_zone (optional): "true" or "false". default to "true"
##     - health_check (required): An ELB Health Check type (see Cloudformation docs)
##     - listeners (required): A list of ELB Listener types (see Cloudformation docs)
##     - scheme (optional): "internal" or "internet-facing". default "internal"
##     - securit_groups (required): A list of security groups
##     - subnets (required): A list of "output" names from the subnet stack for the
##       environment, eg ["SubnetElbPublicAZa", ["SubnetElbPublicAZb"] in the 
##       "subnet-elevate-dev" stack
##   - extra_tags (optional): An dictionary of extra tags to be associated with
##     instances/EBS/ELB. Automatically converted to a list.
##   - health_check (optional): A dictionary with "type" and "grace_period"
##     keys representing the health checks
##   - hostedzone(optional): The name of hosted zone the DNS records for the ELB
##     will be created in
##   - instance_profile (required): The instance profile for the autoscaling group
##   - instance_type (required): The instance type
##   - key_name (required): The SSH key pair to assign to the instances
##   - s3_bucket (optional): The S3 bucket where config mgmt package is. optional 
#      if providing user_data in as a parameter
##   - securit_groups (required): A list of security groups
##   - subnets (required): A list of subnets for the autoscaling group
##   - update_policy (optional):
##   - user_data (optional): The UserData to be provided to the instances.
##     Beware of using shell variables between curly brackets, such as "${USER}, as
##     Mako interprets these as its own interpolation variables. The template
##     takes care of base64 encoding the user_data.
##
<%
    from base64 import b64encode
    service = "-".join([team, environment, application])
    tags = [
        {"Key": "team", "Value": team},
        {"Key": "environment", "Value": environment},
        {"Key": "application", "Value": application},
        {"Key": "Name", "Value": service}
    ]
    if "extra_tags" in locals() and extra_tags:
        [tags.append({"Key": k, "Value": v}) for k, v in extra_tags.items()]

    instance_tags = []
    [instance_tags.append({"Key": i["Key"], "Value": i["Value"], "PropagateAtLaunch": "true"}) for i in tags]

    if "user_data" not in locals() or not user_data:
        user_data = """
        #!/bin/bash -xe
        HOME=/root
        cd $HOME
        yum -y update
        yum -y install puppet3
        aws s3 cp s3://{s3_bucket}/artifacts/services/{service}/{service}-{build_id}.tar.gz ./
        tar xfvz {service}-{build_id}.tar.gz -C /
        /usr/bin/puppet apply --color=false --onetime --verbose --ignorecache --no-daemonize --no-usecacheonfailure --no-splay --show_diff --modulepath=/etc/puppet/modules /etc/puppet/manifests/site.pp 2>&1
        """.format(s3_bucket=s3_bucket, service=service, build_id=build_id)

%>

AWSTemplateFormatVersion: "2010-09-09"
Resources:
  AutoScalingLaunchConfig:
    Type: AWS::AutoScaling::LaunchConfiguration
    Properties:
      % if "associate_public_ip_address" in locals() and associate_public_ip_address:
      AssociatePublicIpAddress: ${associate_public_ip_address}
      % endif
      % if "block_device_mappings" in locals() and block_device_mappings:
      BlockDeviceMappings: ${block_device_mappings}
      % endif
      IamInstanceProfile: ${instance_profile}
      ImageId: ${ami}
      InstanceType: ${instance_type}
      KeyName: ${key_name}
      SecurityGroups: ${security_groups}
      % if "user_data" in locals() and user_data:
      UserData: ${b64encode(user_data.encode("utf-8")).decode("utf-8")}
      % endif

  AutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      DesiredCapacity: ${cluster_size["desired"]}
      MinSize: ${cluster_size["min"]}
      MaxSize: ${cluster_size["max"]}
      % if "elb" in locals() and elb:
      LoadBalancerNames: [{Ref: ElasticLoadBalancer}]
      % endif
      % if "health_check" in locals() and health_check:
      HealthCheckGracePeriod: ${health_check["grace_period"]}
      HealthCheckType: ${health_check["type"]}
      % endif
      LaunchConfigurationName: {Ref: AutoScalingLaunchConfig}
      Tags: ${instance_tags}
      VPCZoneIdentifier: ${subnets}
    % if "creation_policy" in locals() and creation_policy:
    CreationPolicy: ${creation_policy}
    % endif
    % if "update_policy" in locals() and update_policy:
    UpdatePolicy: ${update_policy}
    % endif

  % if "elb" in locals() and elb:
  ElasticLoadBalancer:
    Type: AWS::ElasticLoadBalancing::LoadBalancer
    Properties:
      CrossZone: ${elb.get("cross_zone", "true")}
      HealthCheck: ${elb["health_check"]}
      Listeners: ${elb["listeners"]}
      Scheme: ${elb.get("scheme", "internal")}
      SecurityGroups: ${elb["security_groups"]}
      Subnets: ${elb["subnets"]}
      Tags: ${tags}

  ElasticLoadBalancerDNS:
    Type: AWS::Route53::RecordSet
    Properties:
      Name: ${service}.${hostedzone}.
      HostedZoneName: ${hostedzone}.
      Type: A
      AliasTarget:
        DNSName: {"Fn::GetAtt": [ElasticLoadBalancer, CanonicalHostedZoneName]}
        HostedZoneId: {"Fn::GetAtt": [ElasticLoadBalancer, CanonicalHostedZoneNameID]}
  % endif
