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


""" Utilities and helper functions
"""


import yaml

import boto3
import jmespath

from gpwm.sessions import AWS as AWSSession
from gpwm.sessions import Azure as AzureSession
from gpwm.sessions import GCP as GCPSession

STACK_CACHE = {}
CF_STACK_RESOURCE_CACHE = {}
YAML_TAGS = [
    "!Cloudformation",
    "!AWS",
    "!SSM",
    "!ARM",
    "!GCPDM"
]


def yaml_cloudformation_constructor(loader, node):
    """ Implements the yaml tag !Cloudformation

    The tag takes a dict {stack: $stack_name, output: output_key}
    as node (argument).

    Example:
      VpcId: !Cloudformation {stack: ${vpc_stack}, output: VPC}
      VpcId: !Cloudformation {stack: ${vpc_stack}, resource_id: VPC}
    """
    output_dict = loader.construct_mapping(node)
    stack = output_dict["stack"]
    if "output" in output_dict.keys():
        return get_aws_stack_output(stack=stack, output=output_dict["output"])
    elif "resource_id" in output_dict.keys():
        return get_stack_resource(stack, output_dict["resource_id"])
    else:
        raise SystemExit("Either 'output' or 'resource_id' must be provided")


def yaml_ssm_constructor(loader, node):
    """ Implements the yaml tag !SSM

    The tag takes the same arguments as SSM's GetParameter call:
    http://boto3.readthedocs.io/en/latest/reference/services/ssm.html#SSM.Client.get_parameter
    http://docs.aws.amazon.com/systems-manager/latest/APIReference/API_GetParameter.html

    Example:
      SomeValue: !SSM {Name: /some/parameter/name}
      SomePassword: !SSM {Name: /some/name, WithDecryption: true}
    """
    args = loader.construct_mapping(node)
    return call_aws(
        service="ssm",
        action="get_parameter",
        arguments=args
    )["Parameter"]["Value"]


def yaml_aws_constructor(loader, node):
    """ Implements the yaml tag !AWS

    The tag takes a dict like this as node (argument):
    {service: $service_name,  action: $action_name, arguments: $arguments, result_filter: $jmespath_string} # noqa

    Example:
      VpcId: !AWS {
          service: ec2, \
          action: describe_vpcs,
          arguments: {Filters: [{Name: "tag:team", Values: [sometag]}]},
          result_filter: "Vpcs[].VpcId"
      }
    """
    args_dict = loader.construct_mapping(node, deep=True)
    return call_aws(**args_dict)


def yaml_arm_constructor(loader, node):
    """ Implements the '!ARM' YAML tag

    The tag takes a yaml mapping like this as node (argument):
    {resource-group: ${resource_group_name}, deployment=${stack}, output: ${output_name}} # noqa

    Example:
      storageAccount: !ARM {resource-group: ${storage_resource_group}, deployment=${stack}, output: ${storageName}}
    """
    output_dict = loader.construct_mapping(node)
    if "output" in output_dict.keys():
        return get_azure_stack_output(
            resource_group=output_dict["resource-group"],
            deployment=output_dict["deployment"],
            output=output_dict["output"]
        )
#    elif "resource-id" in output_dict.keys():
#        return get_stack_resource(stack_name, output_dict["resource_id"])
#    else:
    raise SystemExit("Either 'output' or 'resource_id' must be provided")


def yaml_gcpdm_constructor(loader, node):
    """ Implements the yaml tag !GCPDM

    The tag takes a dict as node value:
        {project: ${project}, deployment: ${stack}, output: ${output}}

    Example:
      VpcId: !GCPDM {project: platform, deployment: core-network, output: VPC}
    """
    output_dict = loader.construct_mapping(node)
    if "output" in output_dict.keys():
        return get_gcp_stack_output(
            project=output_dict["project"],
            deployment=output_dict["deployment"],
            output=output_dict["output"]
        )
    else:
        raise SystemExit("Either 'output' or 'resource' must be provided")


def yaml_constructor(loader, tag_suffix, node):
    """ Handles YAML tags used in this tool

    If the tag in not specific to this tool, the yaml Node() object is
    returned, so it can be rendered back into YAML by the *representer*
    function.
    """
    if tag_suffix in YAML_TAGS:
        function = globals()[f"yaml_{tag_suffix[1:]}_constructor".lower()]
        return function(loader, node)
    return node


def yaml_representer(dumper, data):
    return data


# Empty string means all custom tags are handled by yaml_constructor()
# the constructor function handles what tags are specific to this
# script and which aren't. For example, !Cloudformation must be handled
# by this script, which !Sub, or !Ref must be passed to AWS.
yaml.add_multi_constructor("", yaml_constructor)
yaml.add_multi_representer(yaml.nodes.Node, yaml_representer)


def get_aws_stack_output(stack, output):
    if not STACK_CACHE.get(stack):
        STACK_CACHE[stack] = AWSSession().resource.Stack(stack)

    for stack_output in STACK_CACHE[stack].outputs:
        if stack_output["OutputKey"] == output:
            return stack_output["OutputValue"]


def get_azure_stack_output(resource_group, deployment, output):
    if not STACK_CACHE.get(deployment):
        STACK_CACHE[deployment] = AzureSession().client.deployments.get(
            deployment_name=deployment,
            resource_group_name=resource_group
        )
    if STACK_CACHE[deployment].properties.outputs is None:
        return None

    # deployment has outputs if not None
    for k, v in STACK_CACHE[deployment].properties.outputs.items():
        if k == output:
            return v["value"]


def get_gcp_stack_output(project, deployment, output):
    if not STACK_CACHE.get(deployment):
        deployment_result = GCPSession().client.deployments().get(
            project=project,
            deployment=deployment
        ).execute()
        manifest = GCPSession().client.manifests().get(
            project=project,
            deployment=deployment,
            manifest=deployment_result["manifest"].split("/")[-1]
            ).execute()
        STACK_CACHE[deployment] = {
            "deployment": deployment_result,
            "manifest": manifest
        }
    layout = yaml.load(STACK_CACHE[deployment]["manifest"]["layout"])
    for deployment_output in layout.get("outputs", []):
        if deployment_output["name"] == output:
            return deployment_output["finalValue"]


def get_stack_output(stack_name, output_key, provider="aws", **kwargs):
    cmd = locals()[f"get_{provider}_stack_output"]
    return cmd(stack_name=stack_name, output_key=output_key, **kwargs) or ""


def get_stack_resource(stack_name, resource_id):
    # caching results of calls to clouformation API
    if not CF_STACK_RESOURCE_CACHE.get(stack_name):
        CF_STACK_RESOURCE_CACHE[stack_name] = {}
    if not CF_STACK_RESOURCE_CACHE[stack_name].get(resource_id):
        CF_STACK_RESOURCE_CACHE[stack_name][resource_id] = \
            CF_STACK_RESOURCE_CACHE.StackResource(stack_name, resource_id)
    return CF_STACK_RESOURCE_CACHE[stack_name][resource_id].physical_resource_id # noqa


def call_aws(service, action, arguments={}, result_filter=None):
    client = boto3.client(service)
    result = getattr(client, action)(**arguments)
    if result_filter is None:
        return result
    return jmespath.search(result_filter, result)
