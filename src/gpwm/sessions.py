# Copyright 2017 Gustavo Baratto. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


""" Session and connection handlers for the cloud provider's APIs
"""

import importlib
import os
import uuid

import apiclient.discovery  # GCP API
from azure.common.client_factory import get_client_from_auth_file
from azure.common.client_factory import get_client_from_cli_profile
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import SubscriptionClient
import boto3


class Singleton:
    """ A singleton base class to be reused
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance


class AWS(Singleton):
    """ Class representing an AWS CFN Boto client and resources """

    @property
    def client(self):
        if not hasattr(self, "_client"):
            self._client = boto3.client("cloudformation")
        return self._client

    @property
    def resource(self):
        if not hasattr(self, "_resource"):
            self._resource = boto3.resource("cloudformation")
        return self._resource


def get_azure_api_client(cls, **kwargs):
    """ Returns an Azure API client

    Returns an API client class either from a service principal auth
    file (if specified by AZURE_AUTH_LOCATION environment variable, or
    from a CLI profile.

    This function is just a helper for AzureClient.get()

    Args:
        cls(class): The client class, for example
            azure.mgmt.resource.SubscriptionClient
        kwargs(dict): optional keyword arguments used by either
            get_client_from_auth_file() or get_client_from_cli_profile(),
            for example client_id, secret, tenant

    https://github.com/Azure/azure-sdk-for-python/blob/master/azure-common/azure/common/client_factory.py # noqa
    """

    if os.environ.get("AZURE_AUTH_LOCATION"):
        return get_client_from_auth_file(cls, **kwargs)
    return get_client_from_cli_profile(cls, **kwargs)


class AzureClient(Singleton):
    """ Class for retrieving Azure API clients """

    __CACHE__ = {}

    def get(self, client, client_id=None, secret=None, tenant=None,
            subscription=None):
        """ Returns Azure API clients

        This method returns API clients based on various inputs in
        addition to the function arguments, in this priority:
            1- Method arguments
            2- Environment variables specifying the credentials:
                * AZURE_CLIENT_ID: UUID representing the user
                * AZURE_CLIENT_SECRET: secret used for user auth
                * AZURE_TENANT_ID: UUID representing the Azure tenant
                * AZURE_SUBSCRIPTION: Either an UUID or the subscription
                    name. If the subscription name is supplied, the UUID
                    is obtained by making a *SubscriptionClient.list()*
                    API call.
            3- The AZURE_AUTH_LOCATION environment variable which
               specifies a path to the service principal auth file. The
               auth. Can be obtained, for example by creating a new
               service principal:

                # az ad sp create-for-rbac --sdk-auth > ~/.azure/myProfile.json
                # export AZURE_AUTH_LOCATION=~/.azure/myProfile.json

            4- A CLI profile. The profile can be obtained by CLI logins:

                # az login

               Avoid using the CLI method in production. This is usually for
               "real people", not for applications. Use one of the methods
               above which makes use of service principals.

        Args:
            client(str): An alias to the API client, for example:
                - compute.ComputeManagementClient - shortcut to azure.mgmt.compute.ComputeManagementClient
                - network.NetworkManagementClient - shortcut to azure.mgmt.network.NetworkManagementClient
                - resource.SubscriptionClient -  shortcut to  azure.mgmt.resource.SubscriptionClient
                - resource.ResourceManagementClient - azure.mgmt.resource.resource.ResourceManagementClient

        Returns: An "azure.mgmt.*.*()" object

        Reference:
            * https://github.com/MicrosoftDocs/azure-docs-sdk-python/blob/master/docs-ref-conceptual/python-sdk-azure-authenticate.md # noqa
            * https://github.com/Azure/azure-sdk-for-python/blob/master/azure-common/azure/common/client_factory.py#L134 # noqa
            * https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli?view=azure-cli-latest #noqa
            * https://github.com/Azure/azure-sdk-for-python/blob/master/azure-common/azure/common/client_factory.py#L34 # noqa
        """
        client_id = client_id or os.environ.get("AZURE_CLIENT_ID")
        secret = secret or os.environ.get("AZURE_CLIENT_SECRET")
        tenant = tenant or os.environ.get("AZURE_TENANT_ID")
        subscription = subscription or \
            os.environ.get("AZURE_SUBSCRIPTION")

        # Get the api client class
        full_path = f"azure.mgmt.{client}".split(".")
        class_name = full_path[-1]
        module = ".".join(full_path[:-1])
        cls = getattr(importlib.import_module(module), class_name)

        kwargs = {}

        # Find the subscription id
        if subscription:
            # resolve UUID of the subscription (if passed as name)
            try:
                subscription_id = str(uuid.UUID(subscription, version=4))
            except ValueError as exc:
                subscription_client = get_azure_api_client(SubscriptionClient)
                for s in subscription_client.subscriptions.list():
                    print(s.__dict__)
                    if s.display_name == subscription:
                        subscription_id = s.subscription_id
                        break
                else:
                    raise SystemExit(f"Subscription {subscription} not found")
            kwargs["subscription_id"] = subscription_id

        # Get a credentials object if creds passed via this method or
        # environment variables
        if client and secret and tenant:
            kwargs["credentials"] = ServicePrincipalCredentials(
                client_id=client_id,
                secret=secret,
                tenant=tenant
            )

        return get_azure_api_client(cls, **kwargs)


class GCP(Singleton):
    """ Class representing a GCP Deployment Manager API client """
    @property
    def client(self):
        if not hasattr(self, "_client"):
            self._client = apiclient.discovery.build("deploymentmanager", "v2")
        return self._client
