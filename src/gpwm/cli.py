#!/usr/bin/env python
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


""" CLI entry point
"""

from __future__ import print_function
import argparse
import logging
import os
import sys
import yaml

import jinja2
import mako.exceptions
import mako.template

import gpwm.utils
import gpwm.stacks


def build_common_args(parser):
    """ Configures arguments to all actions/subparsers
    """
    parser.add_argument(
        "stack",
        type=argparse.FileType("r"),
        help=("The path to the stack file. "
              "Use - for stdin, in which case -t must be specified")
    )
    parser.add_argument(
        "--templating-engine",
        "-t",
        type=str,
        choices=["mako", "jinja", "yaml"],
        default="mako",
        help=("The templating engine to render the stack. "
              "Only used when stack comes from stdin (-)")
    )
    parser.add_argument(
        "--wait",
        "-w",
        action="store_true",
        default=False,
        help="Waits for the stack to be ready/deleted before exiting"
    )
    parser.add_argument(
        "--build-id",
        "-b",
        default=os.getenv("BUILD_ID", ""),
        help="The build id. Defaults to BUILD_ID env variable"
    )


def parse_args(args):
    """ parse CLI options
    """

    parser = argparse.ArgumentParser("Manage cloudformation stacks")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Not implemented yet"
    )
    parser.add_argument(
        "--loglevel",
        "-l",
        default="error",
        help="The log level"
    )
    parser.add_argument(
        "--botocore-loglevel",
        default="error",
        help="The log level for botocore"
    )

    # subparser for each action
    subparser_obj = parser.add_subparsers(dest="action")
    actions = [
        "create",
        "update",
        "delete",
        "upsert",
        "list",
        "render",
        "validate"
    ]

    subparsers = {}
    for action in actions:
        subparsers[action] = subparser_obj.add_parser(action)
        build_common_args(subparsers[action])

    # action-specficic arguments
    #
    # update
    subparsers["update"].add_argument(
        "--review",
        "-r",
        action="store_true",
        default=False,
        help="Review changes"
    )

    # upsert
    subparsers["upsert"].add_argument(
        "--review",
        "-r",
        action="store_true",
        default=False,
        help="Review changes"
    )

    return parser.parse_args(args)


def resolve_templating_engine(args):
    """ Figures out what templating engine should be used to render the stack
    """
    # Figure out what templating engine to use.
    # Only use -t option when stack comes from stdin
    if args.stack.name == "<stdin>":
        return args.templating_engine
    elif ".mako" in args.stack.name[-5:]:
        return "mako"
    elif ".jinja" in args.stack.name[-6:]:
        return "jinja"
    elif ".yaml" in args.stack.name[-5:]:
        return "yaml"
    raise NotImplementedError("Templating engine not supported. Must be set "
                              "to 'mako', 'jinja', or '' in the command line "
                              "or by using the equivalent file extension")


def execute_action(stack, args, stack_attributes):
    """ Executes the specifc action
    """
    if args.action == "create":
        stack.create(wait=args.wait)
    elif args.action == "delete":
        stack.delete(wait=args.wait)
    elif args.action == "update":
        stack.update(wait=args.wait, review=args.review)
    elif args.action == "upsert":
        stack.upsert(wait=args.wait)
    elif args.action == "render":
        print("===> Stack Attributes:")
        print(yaml.dump(stack_attributes, indent=2))
        print("===> Final Template:")
        stack.render()
    elif args.action == "list":
        pass
    elif args.action == "validate":
        stack.validate()
    else:
        raise NotImplementedError("Action not implemented")


def main():
    """ Entry point
    """
    args = parse_args(sys.argv[1:])

    if not args.build_id:
        raise SystemExit("The build ID is required. \
            Use -b option or set BUILD_ID")

    # logging
    loglevel = getattr(logging, args.loglevel.upper(), None)
    botocore_loglevel = getattr(logging, args.botocore_loglevel.upper(), None)

    # botocore logging level
    boto_logger = logging.getLogger("botocore")
    boto_logger.setLevel(level=botocore_loglevel)

    # script logging level
    logging.basicConfig(level=loglevel)

    templating_engine = resolve_templating_engine(args)

    stack_file = args.stack.read()
    template_params = {
        "build_id": args.build_id,
        "call_aws": gpwm.utils.call_aws,
        "get_stack_output": gpwm.utils.get_stack_output,
        "get_stack_resource": gpwm.utils.get_stack_resource
    }

    # try rendering stack with mako first, if fails try jinja,
    # so we get all the goodies on the stack level as well,
    # not just the on the template

    if templating_engine == "mako":
        logging.debug("Trying to render mako input file...")
        stack_template = mako.template.Template(
            stack_file,
            strict_undefined=False
        )
        try:
            rendered_template = stack_template.render(**template_params)
        # mako wraps the exception where the real information is, so we unwrap
        # and display only the part that matters to the user
        except Exception:
            raise SystemExit(mako.exceptions.text_error_template().render())
    elif templating_engine == "jinja":
        stack_template = jinja2.Template(stack_file)
        rendered_template = yaml.load(stack_template.render(**template_params))
    else:
        stack_attributes = stack_file

    stack_attributes = yaml.load(rendered_template)
    stack_attributes["BuildId"] = args.build_id
    stack = gpwm.stacks.factory(**stack_attributes)
    execute_action(stack, args, stack_attributes)


if __name__ == "__main__":
    main()
