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

import json

from azure.mgmt.resource.resources.models import ParametersLink
from azure.mgmt.resource.resources.models import TemplateLink

import gpwm.renderers
import gpwm.stacks
from gpwm.sessions import AzureClient


class AzureStack(gpwm.stacks.BaseStack):
    """ Class defining an Azure stack (deployment)

    Azure requires ARM based deployments be done inside resource groups,
    therefore resource groups cannot be created using ARM. This
    chicken-and-egg situation requires the resource group to be created
    first via the resources API prior to ARM being able to spawn new
    resources.

    This is what an Azure deployment looks like

        name: myDeployment
        type: azure
        resourceGroup:
          name: myResourceGroup
          location: eastus
          tags:
            team: billing
            environment: dev
            service: web
        template: /path/to/template.mako
        templateLink: https://example.com/path/to/template.json
        parameters:
          minVMs: 1
          maxVMs: 3
        parametersLink: https://example.com/path/to/parameters.json
        mode: incremental|complete
    """
    def __init__(self, **kwargs):
        """
        Args:
            All Azure supported sections are allowed, plus:
            - BuildId(str): The build ID. This will be merged to the
              parameters dict.

        All arguments provided will be set as object attributes, but
        the attributes not supported by the resources API will be unset
        after initialization so the attributes can be fed to the API
        wholesale.

        """
        super().__init__(**kwargs)

        # Can't have both template and templateLink
        if hasattr(self, "templateLink") and hasattr(self, "template"):
            raise SystemExit(
                f"Please specify either template and templateLink"
            )

        if hasattr(self, "templateLink"):
            self.templateLink =  TemplateLink(self.templateLink)
        if hasattr(self, "parametersLink"):
            self.parametersLink = ParametersLink(self.parametersLink)

        if hasattr(self, "template"):
            # If template not already a dict, render from path/URL
            if not isinstance(self.template, dict):
                parsed_url, template_body = \
                    gpwm.renderers.get_template_body(self.template)

                if parsed_url.path[-5:] == ".mako":
                    if not hasattr(self, "parameters"):
                        self.parameters = {}
                    self.parameters["build_id"] = self.BuildId
                    args = [self.name, template_body, self.parameters]
                    template = gpwm.renderers.parse_mako(*args)
                    # mako doesn't need Parameters as they're available to the
                    # template as python variables
                    del self.parameters
                elif parsed_url.path[-6:] == ".jinja":
                    args = [self.name, template_body, self.parameters]
                    template = gpwm.renderers.parse_jinja(*args)
                    # jinja doesn't need Parameters as they're available to the
                    # template as python variables
                    del self.parameters
                elif parsed_url.path[-5:] == ".json":
                    args = [self.name, template_body, self.parameters]
                    template = gpwm.renderers.parse_json(*args)
                elif parsed_url.path[-5:] == ".yaml":
                    args = [self.name, template_body, self.parameters]
                    template = gpwm.renderers.parse_yaml(*args)
                else:
                    raise SystemExit("file extension not supported")

                self.template = template

        self.api_client = AzureClient().get(
            "resource.ResourceManagementClient"
        )

    @property
    def resourceGroupParameters(self):
        return {
            k: v for k, v in self.resourceGroup.items() if k not in [
                "name",
                "persist"
            ]
        }

    @property
    def deploymentProperties(self):
        return {
            k: v for k, v in self.__dict__.items() if k not in [
                "name",
                "resourceGroup",
                "type",
                "BuildId",
                "api_client"
            ]
        }

    def upsert(self, wait=False):
        self.create_resource_group()
        result = self.api_client.deployments.create_or_update(
            resource_group_name=self.resourceGroup["name"],
            deployment_name=self.name,
            properties=self.deploymentProperties
        )
        if wait:
            result.wait()

    def create(self, wait=False):
        self.upsert(wait=wait)

    def update(self, wait=False, review=False):
        self.upsert(wait=wait)

    def delete(self, wait=False):
        result = self.api_client.deployments.delete(
            resource_group_name=self.resourceGroup["name"],
            deployment_name=self.name
        )

        # Wait for deployment to be deleted before attempting to
        # delete the resource group
        # Also wait when explictly requested
        if not self.resourceGroup.get("persist", True):
            result.wait()
            self.delete_resource_group()
        elif wait:
            result.wait()

    def validate(self):
        self.create_resource_group()
        result = self.api_client.deployments.validate(
            resource_group_name=self.resourceGroup["name"],
            deployment_name=self.name,
            properties=self.deploymentProperties
        )
        if result.error:
            raise SystemExit(result.error.message)

    def render(self):
        print(json.dumps(self.deploymentProperties, indent=2))

    def create_resource_group(self):
        return self.api_client.resource_groups.create_or_update(
            self.resourceGroup["name"],
            self.resourceGroupParameters
        )

    def delete_resource_group(self):
        result = self.api_client.resource_groups.delete(
            self.resourceGroup["name"],
        )
        result.wait()
