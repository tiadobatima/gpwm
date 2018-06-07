import mock
import pytest
from gpwm.cli import resolve_templating_engine

class Stack:
    pass

class Args:
    stack = Stack()

@pytest.fixture
def args():
    return Args()

def test_resolve_templating_engine_stdin(args):
    args.stack.name = "abc.jinja"
#    monkeypatch.setitem('builtins.input', lambda x: "Mark")
    assert resolve_templating_engine(args) == "jinja"

def resolve_templating_engine_local(args, engine):
    args.stack.name = f"abc.{engine}"
    assert resolve_templating_engine(args) == engine

def test_template_engines(args):
    engines = ["mako", "jinja", "yaml"]
    for engine in engines:
        resolve_templating_engine_local(args, engine)

