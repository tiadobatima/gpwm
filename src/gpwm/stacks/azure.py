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
from six.moves.urllib.parse import urlparse
import yaml

import gpwm.stacks
from gpwm.utils import AZURE_API_CLIENT
from gpwm.utils import get_template_body
from gpwm.utils import parse_json
from gpwm.utils import parse_jinja
from gpwm.utils import parse_mako
from gpwm.utils import parse_yaml


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

        if isinstance(self.template, dict):
            self.template = json.dumps(self.template, indent=2, sort_keys=True)
        else:
            template_url = urlparse(self.template)
            template_body = get_template_body(template_url)

            if ".mako" in template_url.path[-5:]:
                if not hasattr(self, "parameters"):
                    self.parameters = {}
                self.parameters["build_id"] = self.BuildId
                args = [self.name, template_body, self.parameters]
                template = parse_mako(*args)
                # mako doesn't need Parameters as they're available to the
                # template as python variables
                del self.parameters
            elif ".jinja" in template_url.path[-6:]:
                args = [self.name, template_body, self.parameters]
                template = parse_jinja(*args)
                # jinja doesn't need Parameters as they're available to the
                # template as python variables
                del self.parameters
            elif ".json" in template_url.path[-5:]:
                args = [self.name, template_body, self.parameters]
                template = parse_json(*args)
            elif ".yaml" in template_url[-5:]:
                args = [self.name, template_body, self.parameters]
                template = parse_yaml(*args)
            else:
                raise SystemExit("file extension not supported")

            self.template = template

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
                "BuildId"
            ]
        }

    def upsert(self, wait=False):
        self.create_resource_group()
        result = AZURE_API_CLIENT.deployments.create_or_update(
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
        result = AZURE_API_CLIENT.deployments.delete(
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
        result = AZURE_API_CLIENT.deployments.validate(
            resource_group_name=self.resourceGroup["name"],
            deployment_name=self.name,
            properties=self.deploymentProperties
        )

    def render(self):
        print(json.dumps(self.deploymentProperties, indent=2))

    def create_resource_group(self):
        return AZURE_API_CLIENT.resource_groups.create_or_update(
            self.resourceGroup["name"],
            self.resourceGroupParameters
        )

    def delete_resource_group(self):
        result = AZURE_API_CLIENT.resource_groups.delete(
            self.resourceGroup["name"],
        )
        result.wait()

