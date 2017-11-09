# GPWM Project

## What's GPWM?


GPWM are the initials for *Gwynedd Purves Wynn-Aubrey Meredith's* 


For the few who don't yet know, Major GPW Meredith, of the Seventh Heavy
Battery of the Royal Australian Artillery was the veteran commander of the 
Australians against the Emus in the bloody [Emu War](https://en.wikipedia.org/wiki/Emu_War)
of 1932.

Here we honor his courage, sacrifice, and life-story by aptly naming an 
*infrastructure-as-code* tool after his legacy.


##### The great GPW Meredith - Australian Hero

![The great GPW Meredith, Australian Hero](docs/gpwm.jpg "The great GPW Meredith")

##### Evil Emu - Enemy Of The State
![Evil Emu - Enemy Of The State](docs/emu.png "Evil Emu")


### Major GPW Meredith... Father, patriot and true hero. Lest we forget!

## Infrastructure as Code

The idea behind this is to allow for small, re-usable, independent, and readable infrastructure building blocks that different teams (networking/security/application) can own without affecting others, and allowing microservices in different environments and AWS accounts to be created just by modifying a set of values given to a template. 3 main components make up the system:

* Consumables: A YAML-like template rendered through a Python’s Mako engine that results in a CF template.
* Stacks (input values): A YAML file representing values that will be fed to a template (similar to the *–cli-input-json* option in the AWS CLI).
* Script: Interpolates the input values of a stack with a consumable and
  executes an action with the resulting rendered stack: creates, deletes,
  render, etc.

Cloudformation, GCP and pretty much all cloud providers infrastructure DSL have a few small deficiencies that make it somewhat hard to build reusable, concise, and easy to read templates, for example:

* No “for loops”.
* No high-level data structures like dictionaries or objects as variables.
* No ability to run custom code locally.
* Exports/Imports for linking stacks impose a hard dependency between stacks.

To address these shortcomings, the tool first uses a higher-level templating engine (Mako or Jinja) before sending the resulting stack to the cloud provider. This is not an abstraction layer like Terraform. The resulting template is an AWS Cloudformation stack, or GCP deployment, etc


## Usage Examples

```
pip install gpwm
export BUILD_ID="SOME_BUILD_ID"  # for example "$(date -u +'%F-%H-%M-%S')-$BITBUCKET_COMMIT"
export AWS_DEFAULT_PROFILE=some-profile
export AWS_DEFAULT_REGION=us-west-2

# getting help
python3 gpwm.py --help

# render: only print stack on screen
python3 gpwm.py render aws/stacks/vpc-training-dev.mako
python3 gpwm.py render google/deployments/instance.mako

# create: creates the stack in cloudformation
python3 gpwm.py create aws/stacks/vpc-training-dev.mako
python3 gpwm.py create google/deployments/instance.mako

# delete
python3 gpwm.py delete aws/stacks/vpc-training-dev.mako
python3 gpwm.py delete google/deployments/instance.mako

# update
python3 gpwm.py update aws/stacks/vpc-training-dev.mako
python3 gpwm.py update google/deployments/instance.mako

# update with review (change set)
python3 gpwm.py update aws/stacks/vpc-training-dev.mako -r
python3 gpwm.py update google/deployments/instance.mako -r

# Stack files can be fed via stdin (-t option must be used).
# Very handy when another tool is creating the stack file on the fly
cat my-stack.txt | python3 gpwm.py create -t jinja -
some-script.sh | python3 gpwm.py create -t jinja -
```

## Stacks

Amazon popularized the concept of "infrastructure as code" by proving a
declarative, standardized way for their users to describe what their
infrastructure should look like. Now, most reputable cloud providers offer their
own versions of templated, declarative resource managers:

* AWS: [Cloudformation](https://aws.amazon.com/cloudformation)
* Google Cloud: [Cloud Deployment Manager](https://cloud.google.com/free-trial/docs/map-aws-google-cloud-platform)
* Azure: [Resource Manager](https://azure.microsoft.com/en-us/features/resource-manager)
* Openstack: [Heat](https://docs.openstack.org/developer/heat/)
* Hashicorp: [Terraform](https://www.terraform.io/)

In this context, Stacks are text files that are processed through a templating
engine of choice, and must result in a YAML file after processing.
As of now, Mako and Jinja are supported, with raw Json and YAML in the roadmap
(if using these last two, the provider's CLI suffice)

These stacks are meant to represent resources in the cloud provider of choice,
either:

* Via the cloud provider's own *declarative* language which, describes the final state of the infrastructure
* Via commands or API calls used to get to that final states (*procedural* approach)

At this point, these types of stacks are supported:

* [Cloudformation](docs/aws.md) (declarative)
* [GCP](docs/gcp.md) (declarative)
* [Shell](docs/shell.md) (procedural)

Azure is in the roadmap.

Regardless of the provider, the idea behind this tool
is to never abstract, or dumb-down  the cloud provider's native
resource manager, only enhance it.

Also, the stacks/input files for each cloud provider try to use the syntax and 
constructs native to the provider, instead of, for example, trying to make GCP
Deployment Manager configurations look similar to AWS Cloudformation stacks.
To illustrate, in AWS, the variable and section names used in a CFN stack are
 all *CamelCase*, while GCP uses *Python-style* (lowercase with underscores) in
its Deployment Manager configuration. This tool tries hard to keep that spirit,
so not to throw off users already familiar with a particular cloud provider's DSL.


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


### Stack Types


* [Cloudformation](docs/aws.md)
* [GCP](docs/gcp.md)
* [Shell](docs/shell.md)


### Development

Follow the guidelines in the [development page](docs/development.md)



## Contacts
- Gustavo Baratto: gbaratto AT gmail
