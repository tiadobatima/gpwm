# GPWM Project

## What's GPWM?


GPWM are the initials for *Gwynedd Purves Wynn-Aubrey Meredith's*


For the few who don't yet know, Major GPW Meredith, of the Seventh Heavy
Battery of the Royal Australian Artillery was the veteran commander of the
Australians against the Emus in the bloody [Emu War](https://en.wikipedia.org/wiki/Emu_War)
of 1932.

Here we honor his courage, sacrifice, and life-story by aptly naming an
*infrastructure-as-code* DSL wrapper tool after his legacy.


##### The great GPW Meredith - Australian Hero

![The great GPW Meredith, Australian Hero](docs/gpwm.jpg "The great GPW Meredith")

##### Evil Emu - Enemy Of The State
![Evil Emu - Enemy Of The State](docs/emu.png "Evil Emu")


### Major GPW Meredith... Father, patriot and true hero. Lest we forget!

## Infrastructure as Code

The idea behind this is to allow for small, re-usable, independent, and
readable infrastructure building blocks that different teams
(networking/security/application) can own without affecting others, and
allowing microservices in different cloud provider accounts and environments to
be created just by modifying a set of values given to a template. Three main
components make up the system:

* Consumables: A YAML-like template rendered through a Python’s Mako engine
  that results in a CF template.
* Stacks (input values): A YAML file representing values that will be fed to a
  template (similar to the *–cli-input-json* option in the AWS CLI).
* Script: Interpolates the input values of a stack with a consumable and
  executes an action with the resulting rendered stack: creates, deletes,
  render, etc.

Cloudformation, GCP Deployment Manager, Azure Resource Manager and pretty much
any infrastructure DSL out there have a few small deficiencies that makes it
somewhat hard to build reusable, concise, and easy to read templates, for\
example:

* No “for loops”.
* No high-level data structures like dictionaries or objects as variables.
* No ability to run custom code locally.
* Exports/Imports for linking stacks impose a hard dependency between stacks.

To address these shortcomings, the tool first uses a higher-level templating
engine (Mako or Jinja) to provide a richer and featureful text processing
capabilities to the provider's DSL before compliling into the provider's native
DSL and sending the resulting stack to the cloud provider.

This is not an abstraction layer like Terraform. The resulting template is a
native AWS Cloudformation stack, or GCP/ARM deployments.


## Stack Types

For documentation specific to the provider of choice:

* [AWS](docs/aws.md)
* [Azure](docs/azure.md)
* [GCP](docs/gcp.md)
* [Shell](docs/shell.md)


## Examples

### Usage
```
pip install gpwm

# Configure authentication with AWS (assuming a CLI profile already exists)
export AWS_DEFAULT_PROFILE=some-profile
export AWS_DEFAULT_REGION=us-west-2

# Getting help
python3 gpwm.py --help

# Specify a build ID
export BUILD_ID="SOME_BUILD_ID"  # for example "$(date -u +'%F-%H-%M-%S')-$BITBUCKET_COMMIT"

# prints a rendered stack on the screen
python3 gpwm.py render aws/stacks/vpc-training-dev.mako
python3 gpwm.py render google/deployments/instance.mako

# Creates the stack/deployment in with the cloud provider
python3 gpwm.py create aws/stacks/vpc-training-dev.mako
python3 gpwm.py create google/deployments/instance.mako

# Deletes the stack/deployment from the cloud provider
python3 gpwm.py delete aws/stacks/vpc-training-dev.mako
python3 gpwm.py delete google/deployments/instance.mako

# Updates an existing stack/deployment in the cloud provider
python3 gpwm.py update aws/stacks/vpc-training-dev.mako
python3 gpwm.py update google/deployments/instance.mako

# Updates a stack with review (change set) - AWS only
python3 gpwm.py update aws/stacks/vpc-training-dev.mako -r

# The template path/url specified in the stack/deployment file
# will be prepended by GPWM_TEMPLATE_URL_PREFIX (if set).
# This can be used to enforce the use of company-certified templates, for
# when used with a deployment pipeline tool such as Jenkins
export GPWM_TEMPLATE_URL_PREFIX=s3://my-s3-bucket/subfolder
python3 gpwm.py create aws/stacks/vpc-training-dev.mako

# Stack files can be fed via stdin (-t option must be used).
# Very handy when another tool is creating the stack file on the fly
cat my-stack.txt | python3 gpwm.py create -t jinja -
some-script.sh | python3 gpwm.py create -t jinja -
```

### AWS

#### Stack
```
<%
    stack_type = "vpc"
    team = "demo"
    environment = "dev"
%>
StackName: ${stack_type}-${team}-${environment}
TemplateBody: examples/consumables/network/vpc.mako
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
```

#### Template

```
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
```


## Why should I use this tool?

Amazon popularized the concept of "infrastructure as code" by proving a
declarative, standardized way for their users to describe what their
infrastructure should be like. Now, most reputable cloud providers offer their
own versions of templated, declarative resource managers:

* AWS: [Cloudformation](https://aws.amazon.com/cloudformation)
* Google Cloud: [Cloud Deployment Manager](https://cloud.google.com/free-trial/docs/map-aws-google-cloud-platform)
* Azure: [Resource Manager](https://azure.microsoft.com/en-us/features/resource-manager)
* Openstack: [Heat](https://docs.openstack.org/developer/heat/)
* Hashicorp: [Terraform](https://www.terraform.io/)

In this context, *stacks or deployments* are text files that are processed
through a templating engine of choice, and must result in a YAML file after
processing.
As of now, Mako and Jinja are supported, with raw JSON and YAML in the roadmap,
though if using the latter two, there's really no reason to this tool, just use
the provider's own CLI/SDK

These *stacks* are meant to represent resources in the cloud provider of choice,
either:

* Via the cloud provider's own *declarative* language which, describes the
  final state of the infrastructure
* Via commands or API calls used to get to that final states, ie the
  *procedural* approach. The procedural approach should be used only when
  there's really no other way of managing resources via a declarative approach

At this point, these types of *stacks/deployments* are supported:

* [AWS](docs/aws.md) (declarative)
* [Azure](docs/azure.md) (declarative)
* [GCP](docs/gcp.md) (declarative)
* [Shell](docs/shell.md) (procedural)


Regardless of the provider, the idea behind this tool is to:

* Never abstract, or dumb-down the cloud provider's native resource manager DSL,
  only enhance it
* Never race the provider for features. We are going to lose.
* Simplicity and flexibility: Allow for small, focused *stack/deployment* 
  building blocks that can be reused and loosely connected with other
  deployments, without having to deploy a massive tightly coupled group of
  resources
* Never mix concepts and constructs from different cloud providers, eg AWS *VPC*
  is **not** the same as Azure *vnet*. Related to *abstraction* mentioned
  above, for maximum flexibility and efficiency, we want to be able to tune
  every knob of a resource. And this can only be done, if we treat every
  resource natively.
* Assume that we know better than the cloud provider about how their
  infrastructure should be managed

With the guidelines above, the tool always attempts to provide the cloud
provider's *look-and-feel* for the syntax/constructs in the stacks/deployment
files: An AWS Clouformation stack looks like Cloudformation; an ARM
deployment file looks like ARM, etc. To illustrate, in AWS, the variable and
section names used in a CFN stack are *UpperCamelCase*, in Azure they are
*lowerCamelCase*, and GCP uses *snake_case* (python-like).
This tool tries hard to keep that spirit, so not to throw off users already
familiar with a particular cloud provider's DSL.


### Why a higher level template engine? And why Mako as default?

A text templating engine extends the functionality of a CFN template or any
other text file by allowing "for loops", the use of more complex data types like
dictionaries and objects, and overall better readability by not having to deal
with CFN's hard-to-read intrinsic functions. On top of that, Mako allows for
inline python code right inside the template.

Mako is the default because it's very easy to define simple blocks of python
code inside the template, making it a very powerful tool. But to simplify the
lives of the folks familiar to Ansible, Saltstack, and others, Jinja is also
supported, but be warned that it's just not as flexible as Mako.


### Development

Follow the guidelines in the [development page](docs/development.md)



## Contacts
- Gustavo Baratto: gbaratto AT gmail
