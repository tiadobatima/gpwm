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


""" Miscelaneous rendering functions """

import os
import requests
from six.moves.urllib.parse import parse_qs
from six.moves.urllib.parse import urlparse
import yaml

import boto3
import jinja2
import mako.exceptions
import mako.template

import gpwm.utils


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
    url_prefix = os.environ.get("GPWM_TEMPLATE_URL_PREFIX", "")
    if url_prefix:
        if url_prefix.endswith("/"):
            url_prefix = url_prefix[:-1]
        if url.startswith("/"):
            url = url[1:]
        url = f"{url_prefix}/{url}"

    parsed_url = urlparse(url)
    if "http" in parsed_url.scheme:  # http and https
        try:
            request = requests.get(url)
            request.raise_for_status()
            body = request.text
        except requests.exceptions.RequestException as exc:
            raise SystemExit(exc)
    elif parsed_url.scheme == "s3":
        s3 = boto3.resource("s3")
        obj = s3.Object(parsed_url.netloc, parsed_url.path[1:])
        extra_args = {k: v[0] for k, v in parse_qs(parsed_url.query).items()}
        try:
            body = obj.get(**extra_args)["Body"].read()
        except s3.meta.client.exceptions.NoSuchBucket as exc:
            raise SystemExit(
                f"Error: S3 bucket doesn't exist: {parsed_url.netloc}"
            )
        except s3.meta.client.exceptions.NoSuchKey as exc:
            raise SystemExit(f"Error: S3 object doesn't exist: {url}")
    elif not parsed_url.scheme:
        with open(url) as local_file:
            body = local_file.read()
    else:
        raise SystemExit(f"URL scheme not supported: {parsed_url.scheme}")

    return parsed_url, body


def parse_mako(stack_name, template_body, parameters):
    """ Parses Mako templates
    """
    # The default for strict_undefined is False. Change to True to
    # troubleshoot pesky templates
    mako_template = mako.template.Template(
        template_body,
        strict_undefined=False
    )
    parameters["utils"] = gpwm.utils
#    parameters["get_stack_output"] = get_stack_output
#    parameters["get_stack_resource"] = get_stack_resource
#    parameters["call_aws"] = call_aws
    try:
        template = yaml.load(mako_template.render(**parameters))
    # Ignoring yaml tags unknown to this script, because one might want to use
    # the providers tags like !Ref, !Sub, etc in their templates
    except yaml.constructor.ConstructorError as exc:
        if "could not determine a constructor for the tag" not in exc.problem:
            raise exc
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
    if outputs:
        template["Outputs"] = outputs
    return template


def parse_jinja(stack_name, template_body, parameters):
    """ Parses Jinja templates
    """
    jinja_template = jinja2.Template(template_body)
    parameters["utils"] = gpwm.utils
#    parameters["get_stack_output"] = get_stack_output
#    parameters["get_stack_resource"] = get_stack_resource
#    parameters["call_aws"] = call_aws
    try:
        template = yaml.load(jinja_template.render(**parameters))
    # Ignoring yaml tags unknown to this script, because one might want to use
    # the providers tags like !Ref, !Sub, etc in their templates
    except yaml.constructor.ConstructorError as exc:
        if "could not determine a constructor for the tag" not in exc.problem:
            raise exc
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
