# Azure Stacks

Azure stacks (or ARM deployments) work very similar to AWS Cloudformation,
except by the fact that deployment must be placed in an existing *Resource
Group*. But Azure *Resource Groups* themselves cannot be described or managed
via ARM, so they're descibed/managed via the stack itself.


## Pre-requisites

At this point, these tools are needed:

* Azure CLI: ```pip install azure-cli```
* azure Python SDK: ```pip install azure```

But by using ```pip install -r requirements/pip-install.txt``` all dependencies
for all cloud providers will be installed. Or if you're developing the tool,
use the *Makefile* - see the [development page](docs/development.md).


## Authentication

This is an annoying topic. There are several way to authenticate against Azure
Cloud, and depending on what we want to do, or how the Azure account is setup,
some of these methods might not work, for example some of these don't work with
multi-factor auth.

### Using a CLI Profile

Follow the instructions [here](https://developers.google.com/identity/protocols/application-default-credentials)
At this point only ```get_client_from_cli_profile()``` is implemented.

Further reference:

* https://docs.microsoft.com/en-us/python/azure/python-sdk-azure-get-started?view=azure-python#step-2)


### Using ADAL

Not yet implemented. This will require some environment variable to be setup.
For reference:

* https://github.com/AzureAD/azure-activedirectory-library-for-python
* https://azure.microsoft.com/en-us/resources/samples/resource-manager-python-template-deployment/
* https://docs.microsoft.com/en-us/cli/azure/create-an-azure-service-principal-azure-cli?view=azure-cli-latest


## Azure Deployment Examples 

Similarly to GCP, Azure APIs, SDKs, CLI and documentation aren't as good and
concise as AWS', so we made a choice to use the naming standard of the Azure
API for the stack/deployment DSL configuration, not the CLI or python SDK
naming (which also matches the ARM's template naming scheme), which means the
YAML keys representing an ARM deployment must be *lowerCamelCased*

### Mako - storage-account.mako

```
<%
    team = "accounting"
    environment = "dev"
    service = "web"
%>

name: ${team}-${environment}-${service}
type: azure
resourceGroup:
  name: ${team}-${environment}-${service}-rg
  location: East US
  tags:
    team: ${team}
    environment: ${environment}
    service: ${service}
  persist: false
template: examples/consumables/azure/storage-account.mako
parameters:
  team: ${team}
  environment: ${environment}
  service: ${service}
mode: Incremental
```


### Jinja - storage-account.jinja

```
{% set team = "accounting" %}
{% environment = "dev" %}
{% service = "web" %}

name: {{team}}-{{environment}}-{{service}}
type: azure
resourceGroup:
  name: {{team}}-{{environment}}-{{service}}-rg
  location: East US
  tags:
    team: {{team}}
    environment: {{environment}}
    service: {{service}}
  persist: false
template: examples/consumables/azure/storage-account.jinja
parameters:
  team: {{team}}
  environment: {{environment}}
  service: {{service}}
mode: Incremental
```


The deployment documents above are roughly equivalent to:

```
az group create \
    -g accounting-dev-web-rg \
    --location eastus \
    --tags team=accounting environment=dev service=web
az group deployment create \
    -g accounting-dev-web-rg \
    -n accounting-dev-web \
    --mode Incremental \
    --template-file examples/consumables/azure/storage-account.json \
    --parameters team=accounting environment=dev service=web
```


## Extra YMAL Tags:

These extra tags make the process of referencing resources in different stacks
very simple, and when more providers are supported, we will be able to query
resources in one cloud provider and feed to stacks in other providers.

### !ARM

It take a dict with "deployment", "resource-group", and "output" as hash keys.
It returns the value of the output for that particular ARM deployment.

```
vm: !ARM {resource-group: ${my_rg}, deployment: ${my_stack}, output: vmName}
```

The underlying function *get_azure_stack_output()* can also be used for further
processing of the output value:
```
<%
    vm = get_azure_stack_output(
        deployment="my_deployment",
        resource_group="my_resource_group",
        output="vm_name"
    )
%>
my-vm-name: ${vm}
```
