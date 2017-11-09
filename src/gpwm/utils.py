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


from __future__ import print_function
import requests
from six.moves.urllib.parse import parse_qs
from six.moves.urllib.parse import urlunparse
import yaml

import apiclient.discovery  # GCP API
import boto3
import jinja2
import jmespath
import mako.exceptions
import mako.template


STACK_CACHE = {}
CF_STACK_RESOURCE_CACHE = {}

# CFN API objects
BOTO_CF_RESOURCE = boto3.resource("cloudformation")
BOTO_CF_CLIENT = boto3.client("cloudformation")

# GCP API objects
GCP_API = apiclient.discovery.build("deploymentmanager", "v2")


def yaml_cloudformation_constructor(loader, node):
    """ Implements the yaml tag !Cloudformation

    The tag takes a dict {stack: $stack_name, output: output_key}
    as node (argument).

    Example:
      VpcId: !Cloudformation {stack: ${vpc_stack}, output: VPC}
      VpcId: !Cloudformation {stack: ${vpc_stack}, resource_id: VPC}
    """
    output_dict = loader.construct_mapping(node)
    stack_name = output_dict["stack"]
    if "output" in output_dict.keys():
        return get_stack_output(stack_name, output_dict["output"])
    elif "resource_id" in output_dict.keys():
        return get_stack_resource(stack_name, output_dict["resource_id"])
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

    The tag takes a dict {service: $service_name,
      action: $action_name, arguments: $arguments,
      result_filter: $jmespath_string}
    as node (argument)

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


def yaml_gcp_dm_constructor(loader, node):
    """ Implements the yaml tag !GCPDM

    The tag takes a dict {deployment: $stack_name, output: output_key}
    as node (argument).

    Example:
      VpcId: !GCPDM {deployment: ${vpc_stack}, output: VPC}
    """
    output_dict = loader.construct_mapping(node)
    if "output" in output_dict.keys():
        return get_stack_output(
            stack_name=output_dict["deployment"],
            output_key=output_dict["output"],
            provider="gcp",
            project=output_dict["project"]
        )
    else:
        raise SystemExit("Either 'output' or 'resource' must be provided")


yaml.add_constructor(u'!Cloudformation', yaml_cloudformation_constructor)
yaml.add_constructor(u'!AWS', yaml_aws_constructor)
yaml.add_constructor(u'!SSM', yaml_ssm_constructor)
yaml.add_constructor(u'!GCPDM', yaml_gcp_dm_constructor)


def get_stack_output(
        stack_name,
        output_key,
        provider="cloudformation",
        **kwargs):
    if provider == "cloudformation":
        # caching results of calls to clouformation API
        if not STACK_CACHE.get(stack_name):
            STACK_CACHE[stack_name] = BOTO_CF_RESOURCE.Stack(stack_name)

        for output in STACK_CACHE[stack_name].outputs:
            if output["OutputKey"] == output_key:
                return output["OutputValue"]
    elif provider == "gcp":
        if not STACK_CACHE.get(stack_name):
            deployment = GCP_API.deployments().get(
                project=kwargs["project"],
                deployment=stack_name
            ).execute()
            manifest = GCP_API.manifests().get(
                project=kwargs["project"],
                deployment=stack_name,
                manifest=deployment["manifest"].split("/")[-1]
                ).execute()
            STACK_CACHE[stack_name] = {
                "deployment": deployment,
                "manifest": manifest
            }
        layout = yaml.load(STACK_CACHE[stack_name]["manifest"]["layout"])
        for output in layout.get("outputs", []):
            if output["name"] == output_key:
                return output["finalValue"]
    return ""


def get_stack_resource(stack_name, resource_id):
    # caching results of calls to clouformation API
    if not CF_STACK_RESOURCE_CACHE.get(stack_name):
        CF_STACK_RESOURCE_CACHE[stack_name] = {}
    if not CF_STACK_RESOURCE_CACHE[stack_name].get(resource_id):
        CF_STACK_RESOURCE_CACHE[stack_name][resource_id] = \
            BOTO_CF_RESOURCE.StackResource(stack_name, resource_id)
    return CF_STACK_RESOURCE_CACHE[stack_name][resource_id].physical_resource_id # noqa


def call_aws(service, action, arguments={}, result_filter=None):
    client = boto3.client(service)
    result = getattr(client, action)(**arguments)
    if result_filter is None:
        return result
    return jmespath.search(result_filter, result)


def get_template_body(url):
    """ Returns the text of the URL

    Args:
        url(str): a RFC 1808 compliant URL

    Returns: The text of the target URL

    This function supports 3 different schemes:
        - http/https
        - s3
        - path
    """
    if "http" in url.scheme:
        return requests.get(urlunparse(url)).text
    elif "s3" in url.scheme:
        s3_client = boto3.client("s3")
        extra_args = {k: v[0] for k, v in parse_qs(url.query).items()}
        obj = s3_client.get_object(
            Bucket=url.netloc,
            Key=url.path[1:],
            **extra_args
        )
        return obj["Body"].read()
    return open(url.path).read()


def parse_mako(stack_name, template_body, parameters):
    """ Parses Mako templates
    """
    # The default for strict_undefined is False. Change to True to
    # troubleshoot pesky templates
    mako_template = mako.template.Template(
        template_body,
        strict_undefined=False
    )
    parameters["get_stack_output"] = get_stack_output
    parameters["get_stack_resource"] = get_stack_resource
    parameters["call_aws"] = call_aws
    try:
        template = yaml.load(mako_template.render(**parameters))
    except Exception:
        raise SystemExit(
            mako.exceptions.text_error_template().render()
        )

    # Automatically adds and merges outputs for every resource in the
    # template - outputs are automatically exported.
    # An existing output in the template will not be overriden by an
    # automatic output.
    outputs = {
        k: {
            "Value": {"Ref": k},
            "Export": {"Name": "{}-{}".format(stack_name, k)}
        } for k in template.get("Resources", {}).keys()
    }
    outputs.update(template.get("Outputs", {}))
    template["Outputs"] = outputs
    return template


def parse_jinja(stack_name, template_body, parameters):
    """ Parses Jinja templates
    """
    jinja_template = jinja2.Template(template_body)
    parameters["get_stack_output"] = get_stack_output
    parameters["get_stack_resource"] = get_stack_resource
    parameters["call_aws"] = call_aws
    template = yaml.load(jinja_template.render(**parameters))

    # Automatically adds and merges outputs for every resource in the
    # template - outputs are automatically exported.
    # An existing output in the template will not be overriden by an
    # automatic output.
    outputs = {
        k: {
            "Value": {"Ref": k},
            "Export": {"Name": "{}-{}".format(stack_name, k)}}
        for k in template.get("Resources", {}).keys()
    }
    outputs.update(template.get("Outputs", {}))
    template["Outputs"] = outputs
    return template


def parse_json(stack_name, template_body, parameters):
    """ Parses Json templates
    """
    raise SystemExit("json templates not yet supported")


def parse_yaml(stack_name, template_body, parameters):
    """ Parses YAML templates
    """
    raise SystemExit("yaml templates not yet supported")
