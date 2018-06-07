import json
import os
import requests
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch
import yaml

import pytest

from gpwm.renderers import get_template_body
from gpwm.renderers import parse_json
from gpwm.renderers import parse_jinja
from gpwm.renderers import parse_mako
from gpwm.renderers import parse_yaml

mako_template = """
<%
    var = 1
%>
Resources:
  a: ${var}
  b: 2
  c: !CloudProviderTag tag-value
"""

jinja_template = """
{% set var = 1 %}
Resources:
  a: {{var}}
  b: 2
  c: !CloudProviderTag tag-value
"""

rendered_template = """
Resources:
  a: 1
  b: 2
  c: !CloudProviderTag tag-value
"""

expected_resources_dict = {
    "Resources": {
        "a": 1,
        "b": 2,
        "c": yaml.nodes.ScalarNode(tag='!CloudProviderTag', value='tag-value')
    }
}

expected_parsed_dict = {
    "Resources": {
        "a": 1,
        "b": 2,
        "c": yaml.nodes.ScalarNode(tag='!CloudProviderTag', value='tag-value')
    },
    "Outputs": {
        "a": {"Value": {"Ref": "a"}, "Export": {"Name": "my-stack-a"}},
        "b": {"Value": {"Ref": "b"}, "Export": {"Name": "my-stack-b"}},
        "c": {"Value": {"Ref": "c"}, "Export": {"Name": "my-stack-c"}}
    }
}

parameters = {"p1": "p11", "p2": "p22"}


def test_get_template_body_local_file():
    url = "examples/consumables/aws/network/vpc.mako"
    parsed_url, body = get_template_body(url)
    assert parsed_url.scheme == ""
    assert isinstance(body, str)


def test_get_template_body_http(mocker):
    url = "https://my-site.com/vpc.mako"
    mock_req = mocker.patch("requests.get")
    mock_resp = mocker.MagicMock()
    mock_req.return_value = mock_resp
    mock_resp.text = "somedata"

    parsed_url, body = get_template_body(url)
    assert parsed_url.scheme == "https"
    assert body == "somedata"


def test_get_template_body_s3(mocker):
    bucket = "my-bucket"
    filename = "vpc.mako"
    url = f"s3://{bucket}/{filename}"
    content = "somedata"

    mock_boto = mocker.patch("gpwm.renderers.boto3")
    mock_boto.resource.return_value.Object.return_value.get.return_value.__getitem__.return_value.read.return_value = content # noqa
    parsed_url, body = get_template_body(url)

    mock_boto.resource.assert_called_with("s3")
    mock_boto.resource().Object.assert_called_with(bucket, filename)
    assert parsed_url.scheme == "s3"
    assert body == content


def test_get_template_use_prefix(mocker):
    url = "vpc.mako"
    prefix = "https://my-site.com"
    mocker.patch.dict('os.environ', {"GPWM_TEMPLATE_URL_PREFIX": prefix})
    mock_req = mocker.patch("requests.get")
    mock_resp = mocker.MagicMock()
    mock_req.return_value = mock_resp
    mock_resp.text = "somedata"

    parsed_url, body = get_template_body(url)
    assert parsed_url.scheme == "https"
    assert body == "somedata"
    mock_req.assert_called_with(f"{prefix}/{url}")


def test_get_template_body_http_exception(mocker):
    url = "https://my-site.com/vpc.mako"
    mock_req = mocker.patch("requests.get")
    mock_req.side_effect = requests.exceptions.RequestException()
    with pytest.raises(SystemExit):
        parsed_url, body = get_template_body(url)


def test_get_template_body_s3_exception(mocker):
    bucket = "my-bucket"
    filename = "vpc.mako"
    url = f"s3://{bucket}/{filename}"
    content = "somedata"

    mock_boto = mocker.patch("gpwm.renderers.boto3")
#    mock_boto.meta.return_value.client.return_value.exceptions.return_value.NoSuchBucket.return_value = Exception()  # noqa
    mock_boto.resource.return_value.Object.return_value.get.side_effect = mock_boto.meta.client.exceptions.NoSuchBucket  # noqa
    print(mock_boto.meta.client.exceptions.NoSuchBucket)
    print(mock_boto.resource("s3").Object(bucket, filename).get())
#    get_template_body(url)
#    mock_boto.resource.return_value.Object.return_value.get.return_value.__getitem__.return_value.read.side_effect = "s3.meta.client.exceptions.NoSuchBucket  # noqa
#    mock_bucket_exc = mocker.patch(
#        "gpwm.renderers.boto3.resource.meta.client.exceptions.NoSuchBucket",
#    )
#    mock_bucket_exc.return_value = Exception()
#
#    mock_get = mocker.patch("gpwm.renderers.boto3.resource().Object.get",
#    #        side_effect=mock_bucket_exc)
#    )
#    mock_get.side_effect = mock_bucket_exc

#    with pytest.raises(SystemExit):
#        parsed_url, body = get_template_body(url)


def test_parse_mako(mocker):
    stack_name = "my-stack"
    parsed_template = parse_mako(stack_name, mako_template, parameters)
    # dumping to yaml to make the assert done on a string, instead of
    # handling yaml node objects in a dict
    assert yaml.dump(parsed_template) == yaml.dump(expected_parsed_dict)

    mock_engine = mocker.patch("gpwm.renderers.mako.template.Template")
    mock_engine.render.return_value = rendered_template

    mock_yaml = mocker.patch("gpwm.renderers.yaml")
    mock_yaml.load.return_value = expected_resources_dict

    parse_mako(stack_name, mako_template, parameters)
    mock_engine.assert_called_once_with(mako_template, strict_undefined=False)
    mock_engine().render.assert_called_once_with(**parameters)
    mock_yaml.load.assert_called_once_with(mock_engine().render())


def test_parse_mako_exceptions():
    stack_name = "my-stack"

    # test catching a mako rendering exception
    with \
            patch("gpwm.renderers.mako.template.Template.render") as mock_render,\
            patch("gpwm.renderers.mako.exceptions.text_error_template") as mock_exception:
        mock_render.side_effect = Exception()
        mock_exception().render.return_value = "some-parse-error"

        with pytest.raises(SystemExit):
            parse_mako(stack_name, mako_template, parameters)

    # test catching yaml loading exception
    with patch("gpwm.renderers.yaml.load") as mock_yaml:
        exc = yaml.constructor.ConstructorError(None, None, "random_exception")
        mock_yaml.side_effect = exc

        with pytest.raises(yaml.constructor.ConstructorError):
            parse_mako(stack_name, mako_template, parameters)


def test_parse_jinja(mocker):
    stack_name = "my-stack"
    parsed_template = parse_jinja(stack_name, jinja_template, parameters)
    # dumping to yaml to make the assert done on a string, instead of
    # handling yaml node objects in a dict
    assert yaml.dump(parsed_template) == yaml.dump(expected_parsed_dict)

    mock_engine = mocker.patch("gpwm.renderers.jinja2.Template")
    mock_engine.render.return_value = rendered_template

    mock_yaml = mocker.patch("gpwm.renderers.yaml")
    mock_yaml.load.return_value = expected_resources_dict

    parse_jinja(stack_name, jinja_template, parameters)
    mock_engine.assert_called_once_with(jinja_template)
    mock_engine().render.assert_called_once_with(**parameters)
    mock_yaml.load.assert_called_once_with(mock_engine().render())


def test_parse_jinja_exceptions():
    stack_name = "my-stack"

    # test catching yaml loading exception
    with patch("gpwm.renderers.yaml.load") as mock_yaml:
        exc = yaml.constructor.ConstructorError(None, None, "random_exception")
        mock_yaml.side_effect = exc

        with pytest.raises(yaml.constructor.ConstructorError):
            parse_jinja(stack_name, mako_template, parameters)


def test_parse_yaml():
    with pytest.raises(SystemExit):
        parse_yaml("my-stack", rendered_template, parameters)


def test_parse_json():
    with pytest.raises(SystemExit):
        parse_json("my-stack", {"some": "json"}, parameters)
