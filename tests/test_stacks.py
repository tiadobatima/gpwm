import mock
import pytest
import gpwm.stacks
from gpwm.stacks.aws import CloudformationStack

#@pytest.fixture
#def args():
#    return Args()

def test_base_stack():
    attrs = {"a": 1, "b": 2, "c": 3}
    base_stack = gpwm.stacks.BaseStack(**attrs)
    assert base_stack.__dict__ == attrs


def test_factory(aws_stack1):
    stack = gpwm.stacks.factory(**aws_stack1)
    assert isinstance(stack, CloudformationStack)

def test_aws(aws_stack):
    stack = gpwm.stacks.factory(**aws_stack.dict)

    assert isinstance(stack, CloudformationStack)

