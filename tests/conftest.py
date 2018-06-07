import requests
import yaml

import jinja2
import mako
import pytest


class Stack:
    def __init__(self, path, engine=None, build=1):
        self.path = path
        self.engine = engine
        self.build = build
        with open(path) as f:
            self.raw = f.read()

    @property
    def yaml(self):
        if not hasattr(self, "_yaml"):
            self._yaml = render_mako(self.raw)
        return self._yaml

    @property
    def dict(self):
        if not hasattr(self, "_dict"):
            self._dict = yaml.load(self.yaml)
            self._dict.update(BuildId=self.build)
        return self._dict

def render_mako(data, **params):
    tmpl = mako.template.Template(data)
    return tmpl.render(**params)

#@pytest.fixture(scope="module")
@pytest.fixture()
def aws_stack(mocker):
    path = "examples/stacks/aws/network/vpc-demo-dev.mako"
    engine = "mako"
    mocker.patch("gpwm.utils.get_aws_stack_output", "xoxox")
    return Stack(path, engine)

@pytest.fixture
def aws_stack1():
   return {
        "BuildId": 1,
        "StackName": "my-stack",
        "TemplateBody": "examples/consumables/aws/network/vpc.mako",
        "Parameters": {
            "team": "networking",
            "environment": "prod",
            "cidr": "10.0.0.0/16",
            "nat_availability_zones": [
                {"name": "a", "cidr": "10.0.0.0/28"},
                {"name": "b", "cidr": "10.0.0.16/28"}
            ]
        },
        "Tags": {
          "type": "network",
          "team": "networking",
          "environment": "prod"
        }
    }

#@pytest.fixture
#def http_body(mocker):
#    path = "examples/stacks/aws/network/vpc-demo-dev.mako"
#    engine = "mako"
#    mock_req = mocker.patch.object("requests", "get")
#    mock_resp = MagicMock()
#    mock_req.return_value = mock_resp
#    mock_resp.text = "xoxoxo"
#
