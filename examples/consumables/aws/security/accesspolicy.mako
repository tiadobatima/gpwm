##
## Owner: security
##
## Dependencies: None
## 
## Parameters:
##   - team (required): The team owning the stack
##   - environment (required): The environment where the stack is running on (dev, prod, etc)
##   - application (required): The name of the application (frontend, zookeeper, kafka, etc)
##   - policies (required): A list of dictionaries representing inline and
##     managed policies defined by:
##     - inline (optional): A list of inline policies (see Cloudformation docs for IAM)
##     - managed (optional): A list of ARNs for the managed profile attached to the
##       IAM role
##   - kms_cmk (optional): true or false. If a KMS CMK exclusive to the role (and admins)
##     should be created
##
## Notes:
##   - This template creates unique roles, instance profiles and policies for
##     services. The "$team-$environment-$application" tuple is defined as a service.
##
<%
    service = "-".join([team, environment, application])
    bucket_suffix = hostedzone.replace(".", "-")
    team_bucket = "{}-{}".format(team, bucket_suffix)
    service_bucket = "{}-{}".format(service, team_bucket)
%>

AWSTemplateFormatVersion: "2010-09-09"
Resources:
  Role:
    Type: AWS::IAM::Role
    Properties:
      RoleName: ${service}
      Path: "/service/"
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          -
            Effect: Allow
            Action:
              - sts:AssumeRole
            Principal:
              Service:
                - ec2.amazonaws.com
      % if policies.get("inline"):
      ManagedPolicyArns: ${policies.get("managed"), []}
      % endif
      Policies:
        -
          PolicyName: default
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              -
                Sid: AllowDescribeEverything
                Effect: Allow
                Action: ec2:Describe*
                Resource: "*"
              -
                Sid: AllowAccessToKeyMetadata
                Effect: Allow
                Action:
                  - kms:Describe*
                  - kms:Get*
                  - kms:List*
                Resource: "*"
              -
                Sid: AllowPutMetricData
                Effect: Allow
                Action: cloudwatch:PutMetricData
                Resource: "*"
              -
                Sid: AllowListingOnTeamBucketsRootFolder
                Effect: Allow
                Action:
                  - s3:ListBucket
                Resource:
                  - arn:aws:s3:::${team_bucket}
              -
                Sid: DenyAllListingExceptForServiceFolders
                Effect: Deny
                Action:
                  - s3:ListBucket
                Resource:
                  - arn:aws:s3:::${team_bucket}
                Condition:
                  "Null":
                    s3:prefix: "false"
                  StringNotLike:
                    s3:prefix:
                      - ""
                      - services
                      - services/*
                      - services/${service}
                      - services/${service}/*
              -
                Sid: AllowGetOnArtifactsFolder
                Effect: Allow
                Action: s3:Get*
                Resource:
                  - arn:aws:s3:::${team_bucket}/artifacts/services/${service}/*
              -
                Sid: FullAccessToServiceFolder
                Action:
                  - s3:*
                Effect: Allow
                Resource:
                  - arn:aws:s3:::${team_bucket}/services/${service}/*
                  - arn:aws:s3:::${team_bucket}/services/${service}
              -
                Sid: FullAccessToServiceBucket
                Action:
                  - s3:*
                Effect: Allow
                Resource:
                  - arn:aws:s3:::${service_bucket}
                  - arn:aws:s3:::${service_bucket}/*

        ## Service specific inline policies
        % if policies.get("inline"):
        - ${policies.get("inline")}
        % endif

  InstanceProfile:
    Type: AWS::IAM::InstanceProfile
    Properties:
      Path: "/"
      Roles: [{Ref: Role}]
      InstanceProfileName: ${service}

  % if "kms_cmk" in locals() and kms_cmk and kms_cmk != "false":
  CMK:
    Type: AWS::KMS::Key
    Properties:
      Description: Key for service ${service}
      Enabled: True
      EnableKeyRotation: False
      KeyPolicy:
        Version: "2012-10-17"
        Statement:
          -
            Sid: Full access from root account
            Effect: Allow
            Action: kms:*
            Resource: "*"
            Principal:
              AWS: {"Fn::Join": [":", ["arn:aws:iam:", {"Ref": "AWS::AccountId"}, root]]}
          -
            Sid: Enable service to encrypt and decrypt
            Effect: Allow
            Action:
              - kms:Encrypt
              - kms:Decrypt
              - kms:ReEncrypt
              - kms:GenerateDataKey*
              - kms:DescribeKey
            Resource: "*"
            Principal:
              AWS: {"Fn::GetAtt": [Role, Arn]}

  CMKAlias:
    Type: AWS::KMS::Alias
    Properties:
      AliasName: alias/${service}
      TargetKeyId: {Ref: CMK}
  % endif
