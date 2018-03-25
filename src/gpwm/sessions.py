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


import apiclient.discovery  # GCP API
from azure.common.client_factory import get_client_from_cli_profile
from azure.mgmt.resource import ResourceManagementClient
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


class Azure(Singleton):
    """ Class representing an Azure Resource Manager API client """

    @property
    def client(self):
        if not hasattr(self, "_client"):
            self._client = get_client_from_cli_profile(
                ResourceManagementClient
            )
        return self._client


class GCP(Singleton):
    """ Class representing a GCP Deployment Manager API client """
    @property
    def client(self):
        if not hasattr(self, "_client"):
            self._client = apiclient.discovery.build("deploymentmanager", "v2")
        return self._client
