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

import os

import apiclient.discovery  # GCP API
from azure.common.client_factory import get_client_from_auth_file
from azure.common.client_factory import get_client_from_cli_profile
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
import boto3


def get_arm_client_via_service_principal():
    """ Returns an API client with via service principal variables

    A ResourceManagementClient() object is returned if all these
    environment variables are set:
        * AZURE_CLIENT_ID
        * AZURE_CLIENT_SECRET
        * AZURE_SUBSCRIPTION_ID
        * AZURE_TENANT_ID

    If any of these variables isn't set, the function returns None

    Args:

    Returns: A ResourceManagementClient() object

    Reference:
        *  https://github.com/MicrosoftDocs/azure-docs-sdk-python/blob/master/docs-ref-conceptual/python-sdk-azure-authenticate.md # noqa
    """
    client = os.environ.get("AZURE_CLIENT_ID")
    secret = os.environ.get("AZURE_CLIENT_SECRET")
    subscription = os.environ.get("AZURE_SUBSCRIPTION_ID")
    tenant = os.environ.get("AZURE_TENANT_ID")

    if client and secret and subscription and tenant:
        creds = ServicePrincipalCredentials(
            client_id=client,
            secret=secret,
            tenant=tenant
        )
        return ResourceManagementClient(
            credentials=creds,
            subscription_id=subscription
        )


def get_arm_client_via_auth_file():
    """ Returns an API client via auth file (AZURE_AUTH_LOCATION env)

    An auth file (profile) can be setup, normally via the CLI with the
    command:

        # az ad sp create-for-rbac --sdk-auth > ~/.azure/myProfile.json
        # export AZURE_AUTH_LOCATION=~/.azure/myProfile.json

    Args:

    Returns: A ResourceManagementClient() object

    Reference:
        * https://github.com/Azure/azure-sdk-for-python/blob/master/azure-common/azure/common/client_factory.py#L134 # noqa

    """
    if os.environ.get("AZURE_AUTH_LOCATION"):
        return get_client_from_auth_file(ResourceManagementClient)


def get_arm_client_via_cli_profile():
    """ Returns an API client via CLI profile

    A CLI profile can be setup with the following command:

        # az login
    Args:

    Returns: A ResourceManagementClient() object

    Reference:
        * https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli?view=azure-cli-latest #noqa
        * https://github.com/Azure/azure-sdk-for-python/blob/master/azure-common/azure/common/client_factory.py#L34 # noqa

    """
    return get_client_from_cli_profile(ResourceManagementClient)


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


class Azure(Singleton):
    """ Class representing an Azure Resource Manager API client """

    @property
    def client(self):
        if not hasattr(self, "_client"):
            # Attempts via service principal (AZURE_* variables) first
            self._client = get_arm_client_via_service_principal() or None

            # Then attempts via auth file
            if not self._client:
                self._client = get_arm_client_via_auth_file()

            # If nothing else works, tries the CLI profile
            if not self._client:
                self._client = get_arm_client_via_cli_profile()

        print(self._client.config.credentials.__dict__)
        return self._client


class GCP(Singleton):
    """ Class representing a GCP Deployment Manager API client """
    @property
    def client(self):
        if not hasattr(self, "_client"):
            self._client = apiclient.discovery.build("deploymentmanager", "v2")
        return self._client
