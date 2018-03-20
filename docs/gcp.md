# GCP Stacks

GCP stacks (or deployments configurations) look very similar to *gcloud's* 
configurations for *Deployment Manager*.

GCP's APIs, SDKs, and the command line tool (gcloud) are a very messy bag of
cats, but a lot of the design choices GCP made closely mirror the ones this
tool made for AWS, with the caviat that GCP DM doesn't support one major 
piece of functionality: *Cross stack/deployment references*

Because the parameter mapping for the GCP DM API look so different from
*gcloud's*, the choice was made to follow *gcloud's* configuration, which at 
least has a bit of documentation and examples avalailable, unlike DM's API.

All parameters for *gcloud's* DM configuration are supported by this tool, with
the addition of:

* name (supported by API, not gcloud)
* description (supported by API, not gcloud)
* labels (supported by API, not gcloud)
* project (supported by APY, not gcloud)
* stack_type (required by this tool)


## Pre-requisites

The GCP SDK setup is a bit more complex than AWS'. These tools are needed:

* gcloud: OS specific package manager https://cloud.google.com/sdk/
* google cloud python SDK: ```pip install google-cloud```
* google API python SDK: ```pip install google-api-python-client```

But by using ```pip install -r requirements/pip-install.txt``` all dependencies
for all cloud providers will be installed. Or if you're developing the tool,
use the *Makefile* - see the [development page](docs/development.md).

## Authentication

follow the instructions
[here](https://developers.google.com/identity/protocols/application-default-credentials)

```
gcloud auth application-default login
```


## GCP Deployment Examples 

### Mako - instance.mako
```
<%
    project = "dev-island"
    dependent_stack = "gus-test-deployment"
%>
stack_type: gcp
name: gus-test-deployment-1
description: Gus test stack 1
project: ${project}
imports:
  - path: some_template.jinja
resources:
- type: compute.v1.instance
  name: gus-test-1
  properties:
    zone: us-west1-a
    machineType: https://www.googleapis.com/compute/v1/projects/dev-island/zones/us-west1-a/machineTypes/f1-micro
    disks:
    - deviceName: boot
      type: PERSISTENT
      boot: true
      autoDelete: true
      initializeParams:
        sourceImage: https://www.googleapis.com/compute/v1/projects/debian-cloud/global/images/debian-8-jessie-v20160301
    networkInterfaces:
    - network: https://www.googleapis.com/compute/v1/projects/dev-island/global/networks/default
      accessConfigs:
      - name: External NAT
        type: ONE_TO_ONE_NAT
outputs:
  - name: instance_id
    value: $(ref.gus-test-1.name)
  - name: some-output
    value: !GCPDM {deployment: ${dependent_stack}, output: instance_id, project: ${project}}
```

### Jinja - instance.jinja

```
{% set project = "dev-island" %}
{% set dependent_stack = "gus-test-deployment" %}

stack_type: gcp
name: gus-test-deployment-1
description: Gus test stack 1
project: {{project}}
imports:
  - path: some_template.jinja
resources:
- type: compute.v1.instance
  name: gus-test-1
  properties:
    zone: us-west1-a
    machineType: https://www.googleapis.com/compute/v1/projects/dev-island/zones/us-west1-a/machineTypes/f1-micro
    disks:
    - deviceName: boot
      type: PERSISTENT
      boot: true
      autoDelete: true
      initializeParams:
        sourceImage: https://www.googleapis.com/compute/v1/projects/debian-cloud/global/images/debian-8-jessie-v20160301
    networkInterfaces:
    - network: https://www.googleapis.com/compute/v1/projects/dev-island/global/networks/default
      accessConfigs:
      - name: External NAT
        type: ONE_TO_ONE_NAT
outputs:
  - name: instance_id
    value: $(ref.gus-test-1.name)
  - name: some-output
    value: !GCPDM {deployment: {{dependent_stack}}, output: instance_id, project: {{project}}}
```



## Extra yaml tags:

These extra tags make the process of referencing resources in different stacks
very simple, and when more providers are supported, we will be able to query
resources in one cloud provider and feed to stacks in other providers.

### !GCPDM

It take a dict with "deployment", "output", and "project" key as arguments. It returns the value of the output for that particular GCP deployment.

```
instance: !GCPDM {deployment: ${my_other_stack}, output: instance_id, project: dev-island}
```

The underlying function *get_stack_output()* can also be used for further processing of the value:
```
<%
    instance = get_stack_output("my-deployment", "instance_id", provider="gcp", project="my-project")
    team = instance.split("-")[0]
%>
my-team: ${team}
```
