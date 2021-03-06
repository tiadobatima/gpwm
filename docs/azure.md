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
multi-factor auth. To make it easier for the use to both test and use this tool
in production, as of this writing all authentication methods supported:

1. Service principal via environment variables
2. Service principal via auth file
3. CLI profile

If multiple authentication methods are setup, the method in chosen based on the
order above.

This is a description of the authentication methods:

### Authenticating using Service Principal Environment Variables

Similar method as `Service Principal` above, but no need to rely on a file if
your auth info can be obtained dynamically. These environment variables must be
set:

* AZURE_CLIENT_ID: The UUID of the service principal
* AZURE_CLIENT_SECRET: The secret the service principal uses to autenticate
* AZURE_TENANT_ID: The UUID of the tenant
* AZURE_SUBSCRIPTION: Either the UUID of the subscription, or its name

For example:

```
az ad sp create-for-rbac -n myPipeline --sdk-auth
export AZURE_CLIENT_ID=3b433e78-cac0-4a23-cd8b-34c5b45ce51a
export AZURE_CLIENT_SECRET=b8b467d0-cef4-4b8f-a573-76537148c7d
export AZURE_TENANT_ID=e6358ac9-aacf-33fc-9ee4-cf93fbfe5d68
export AZURE_SUBSCRIPTION=0432b1d0-5e2e-4e2a-ad73-e33d0652e5b2

# Or using the subscription name
export AZURE_SUBSCRIPTION=dev-subscription
```

Notice that unlike AWS, these environment variables aren't honoured anywhere in
the Azure SDK, but they are used in some of their code examples, so this tool
is using the same variable names to make it familiar for people that have been
playing with Azure's example code.

For reference:

* https://github.com/AzureAD/azure-activedirectory-library-for-python
* https://azure.microsoft.com/en-us/resources/samples/resource-manager-python-template-deployment/
* https://docs.microsoft.com/en-us/cli/azure/create-an-azure-service-principal-azure-cli?view=azure-cli-latest


### Autheticating With a Service Principal Auth File

This method uses a *service principal*, which is fancy wording for a
*service user*, instead of your own account. To set it up, just set the path to
the profile in the `AZURE_AUTH_LOCATION` environment variable. For example:

```
az ad sp create-for-rbac -n myPipeline --sdk-auth > ~/.azure/myPipelineProfile.json
export AZURE_AUTH_LOCATION=~/.azure/myPipelineProfile.json
```

This variable is honoured by the Azure SDKs (at least Python and .NET)

For further reference on this auth method:

* https://github.com/MicrosoftDocs/azure-docs-sdk-python/blob/master/docs-ref-conceptual/python-sdk-azure-authenticate.md
* https://github.com/Azure/azure-sdk-for-python/blob/master/azure-common/azure/common/client_factory.py#L134


### Authenticating With a CLI Profile

This is the simplest of the methods. To set it up, just do a CLI login:

```
azure login
```

In a nutshell, this method sets up an Azure auth profile in
`~/azure/azureProfile`, and is most suitable for users that are testing with
their own credentials. Avoid using this method in production.

For further reference on this auth method:

* https://github.com/AzureAD/azure-activedirectory-library-for-python
* https://docs.microsoft.com/en-us/python/azure/python-sdk-azure-get-started?view=azure-python#step-2


## Azure Deployment Examples 

Similarly to GCP, Azure APIs, SDKs, CLI and documentation aren't as good and
concise as AWS', so we made the choice of using the naming standard of the Azure
API/AEM for the stack/deployment DSL configuration, not the CLI or python SDK
naming. So, the YAML keys representing an ARM deployment is *lowerCamelCased*

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
# Using GPWM
gpwm create path/to/storage-account.mako


# Using the Azure CLIa - obviously you don't get the goodies this way
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
processing of the output value, in mako or jinja:
```
<%
    vm = utils.get_azure_stack_output(
        deployment="my_deployment",
        resource_group="my_resource_group",
        output="vm_name"
    )
%>
my-vm-name: ${vm}
```
