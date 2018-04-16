# Cloudformation Stacks

Cloudformation stacks looks very similar to AWS CLI's *--cli-input-json* file, but has the ability to:

* Reference a template with a path
* Feed the templates with richer data structures as parameters

Because these parameters can be lists or dictionaries, creating reusable
master templates where we the number of resources aren't known in advance
is quite simple (and also easy to read).

## Pre-requisites

The only pre-requisite is the python AWS SDK (Boto3) and jmespath.
Both are automatically installed with the the tool.

## Authentication

Authentication against AWS is done by configuring Boto or the AWS CLI (which 
uses Boto). The easiest way is to create a default CLI/boto profile with the 
AWS CLI (which pretty much everyone already has installed):

```
$ aws configure
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: us-west-2
Default output format [None]: ENTER
```

If the AWS CLI isn't available, any of these options defined in the [Boto 
configuration page](http://boto3.readthedocs.io/en/latest/guide/configuration.html)
will work.


## Stacks

Stacks represent a clouformation Stack, with input values, or *Parameters* that can be passed to a
consumable, which is the equivalent to a CFN template.

As mentioned in other places, stacks with *.mako*, and *.jinja* extensions get
first rendered via *mako* or *jinja* templating engines respectively, then the
all the parameters defined in the *Parameters* section of the stack, and some 
functions "exported" as template enginet variables to the consumable defined by
the file name (or url) in the *TemplateBody* key. The consumable in its turn is
also rendered with the templating engine based on the file extension of the
consumable (.mako, or .jinja). The rendered string of the whole consumable is
set as the stack's *TemplateBody* as per CFN's API requirement.

### Mako - subnet.mako
```
##
## Owner: networking
##
<%
    stack_type = "subnet"
    team = "consulting"
    environment = "prd"
%>
StackName: ${stack_type}-${team}-${environment}
TemplateBody: templates/${stack_type}.mako
Parameters:
  team: ${team}
  environment: ${environment}
  vpc_stack: vpc-${team}-${environment}
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
  team: ${team}
  environment: ${environment}
  type: ${stack_type}
```

### Jinja - subnet.jinja
```
##
## Owner: networking
##

{% set stack_type = "subnet" %}
{% set team = "consulting" %}
{% set environment = "prd" %}
StackName: {{stack_type}}-{{team}-{{environment}}
TemplateBody: templates/{{stack_type}}.mako
Parameters:
  team: {{team}}
  environment: {{environment}}
  vpc_stack: vpc-{{team}}-{{environment}}
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
  team: {{team}}
  environment: {{environment}}
  type: {{stack_type}}
```


Stacks can also pull templates from S3 buckets or webservers:

```
##
## Owner: networking
##
StackName: vpc-training-dev
TemplateBody: s3://training-island-dev-srcd-io/gus-test/vpc.mako?SSECustomerKey=abcdefghijklmnopqrstuvwxyz123456&SSECustomerAlgorithm=AES256
Parameters:
  team: training
  environment: dev
  cidr: 10.0.0.0/16
  nat_availability_zones:
    - {"name": "a", "cidr": "10.0.0.0/28"}
    - {"name": "b", "cidr": "10.0.0.16/28"}
Tags:
  team: training
  environment: dev
  type: vpc
```

## Consumables

After processing, a consumable must be 100% clouformation-compatible templates.

In short, consumables are CFN templates that have these main extra features:

* Ability to be rendered with a higher level text templating engine (mako only one supported now).
* Extra yaml tags (!Cloudformation and !AWS) that makes queries to the appropriate API and replace them with results from those calls.
* Extra helper functions that, as the extra yaml tags, allows for querying data
  in AWS
* Automatic creation of CF outputs for every resource present in the template.

### Example Template
```
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
```

## Change sets

When making updates to stacks, sometimes it's useful to know what actual changes to
resources will be made. For this, the script supports CFN change sets. The
usual use-case for this is interactive, non-pipeline changes, not fully
automated pipeline-based updates.

The way it works is simple. Add a *"-r"* option to the *"update"* action:

```
python gpwm.py update stacks/network/vpc-demo-dev.yaml -r
---------- Change Set ----------
Capabilities: []
ChangeSetId:
arn:aws:cloudformation:us-west-2:329193457145:changeSet/vpc-demo-dev-1/c776d600-0f54-4436-ad78-58693091c97e
ChangeSetName: vpc-demo-dev-1
Changes:
- ResourceChange:
    Action: Remove
    Details: []
    LogicalResourceId: DHCPOptions
    PhysicalResourceId: dopt-ba9f98dd
    ResourceType: AWS::EC2::DHCPOptions
    Scope: []
  Type: Resource
CreationTime: 2017-07-18 00:43:54.803000+00:00
ExecutionStatus: AVAILABLE
NotificationARNs: []
StackId:
arn:aws:cloudformation:us-west-2:329193457145:stack/vpc-demo-dev/af6631f0-6759-11e7-8760-50a68d01a68d
StackName: vpc-demo-dev
Status: CREATE_COMPLETE
Tags:
- {Key: environment, Value: dev}
- {Key: build_id, Value: '1'}
- {Key: team, Value: demo}
- {Key: type, Value: vpc}

--------------------------------
Execute(e), Delete (d), or Keep(k) change set?wsdadsa
Valid answers: e, d, k
Execute(e), Delete (d), or Keep(k) change set?k
Changeset vpc-demo-dev-1 unchanged. No changes made to stack vpc-demo-dev
```

In the example above the user first made a mistake and chose an invalid option, but later 
choose to keep the changeset to be dealt with later (option *"k"*) maybe via the AWS UI.

The user could have executed the changeset if he/she agreed with the changes
(option *"e"*), or deleted it without any changes to the resources if changes were not good (option *"d"*).


## Extra yaml tags:

These extra tags make the process of referencing resources in different stacks
very simple, and when more providers are supported, we will be able to query
resources in one cloud provider and feed to stacks in other providers.

### !Cloudformation

It takes a dictionary with "stack" and either "output" or "resource_id" keys as
arguments. It returns the value of the output or the physical resource_id for
that CF stack. Very simple way o
f doing stack references without having to tie different pieces of
infrastructure together with "Import".
```
VPC: !Cloudformation {stack: my-vpc-stack, output: VpcId}
VPC: !Cloudformation {stack: my-vpc-stack, resource_id: VPC}
```
Sometimes we need to do further processing of the value returned. So, instead
of using the !Cloudformation tag, we can just use the underlying functions
*get_aws_stack_output()* or *get_aws_stack_resource()* to get the output or
 the physical resource_id values:
```
<%
    # "my.subdomain.company.com" into "my-subdomain-company-com"
    hostedzone = get_aws_stack_output(common_stack, "Hostezone")
    s3_bucket = "-".join(hostedzone.split("."))
%>
S3Bucket: ${s3_bucket}
```

### !AWS
It takes a dictionary with the keys "service", "action", "arguments", and
"result_filter" as tag arguments.
This tag makes a call to **ANY** AWS service with any argument wanted and
filters the result with a *JMESPATH* query, if needed.
This is very powerful because not every resource can be created with
Cloudformation, eg when AWS releases a new service or feature, it can take
months or years for them to be available withi
n Cloudformation. The arguments to *!AWS* are standard
[botocore](https://botocore.readthedocs.io/en/latest/index.html) entities:

* service (required): The AWS service such as *ec2*, *s3*, *reoute53*,
  *kinesis*, etc.
* action (required): The botocore method for the service. eg
  *describe_instances*, *get_hosted_zone*, etc
* arguments (optional, but usually required by the action): A
  dictionary/hashmap of the arguments provided to the action, eg *{Filters:
[{Name: "tag:team", Values: [accounting]}]}*, *{Id: my
-domain.com}*
* result_filter (optional): A [JMESPATH](http://jmespath.org) query string that
  locally filters result of the API call

Examples:
```
VPC: !AWS {service: ec2, action: describe_vpcs, arguments: {Filters: [{Name:
cidr, Values: [10.0.0.0/16]}]}, result_filter: "Vpcs[].VpcId"}

HostedZoneId: !AWS {service: route53, action: list_hosted_zones_by_name,
arguments: {DNSName: abc.com}, result_filter: "HostedZones[0].Id"}
```

Similarly to the !Cloudformation tag, the underlying function (*call_aws()*)
for the !AWS tag can also be used:
```
<%
    vpcs = call_aws(
        service="ec2",
        action="describe_vpcs",
        arguments={"Filters": [{"Name": "tag:sometag", "Values":
["somevalue"]}]},
        result_filter="Vpcs[].VpcId"
    )
    for vpc in the vpcs:
        do_something_with_vpc()
%>
```

### !SSM
It takes a dictionary with the keys "Name" and "WithDecryption" as arguments, per
[get_parameter()](http://boto3.readthedocs.io/en/latest/reference/services/ssm.html#SSM.Client.get_parameter)
method of Boto's SSM client.
This tag returns the value of a parameter from the AWS Simple System Manager
(SSM) Parameter Store, and is specially useful to retrieve secrets
(passwords/keys) from SSM's parameter store so they are not kept plaintext in
git or any other SCM of choice.
Naturally, plain text parameters can also be retrieved, thus the argument
"WithDecryption" is optional, but must be specified when retrieving
encrypted parameters.

Examples:
```
Password: !SSM {Name: my-password, WithDecryption: true}

PlainTextParam: !SSM {Name: /some/useful/param}
```

This tag uses *call_aws()* as underlying function, so if the parameter is
needed inside a python block, something like this should be done:

```
<%
    password = call_aws(
        service="ssm",
        action="get_parameter",
        arguments={Name="my-password", WithDecryption: true}
    )["Parameter"]["Value"]
%>
```
