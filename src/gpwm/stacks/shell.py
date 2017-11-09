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


from __future__ import print_function
import logging
import os
import subprocess
import yaml

import gpwm.stacks


class ShellStack(gpwm.stacks.BaseStack):
    """ Class for stacks of type "Shell"

    This class allows for running commands in the local system.
    Mostly used to provide a consistent interface to infrastructure
    deployments when resources cannot be handled using
    cloudformation
    """
    def __init__(self, **kwargs):
        """
        Args:
            Actions(dict): Actions allowed in for the stack. For each
                action, these dict keys are available:
                - Commands(str|list): Required. Represents the shell
                commands to be executed for the action, and works
                similarly to the "args" option in "subprocess.Popen()"
                - Environments(dict): Optional. Represents environment
                variables specific to the action
            BuildId(str): The build ID. It will be exported as an
                environment BUILD_ID.
            Shell(str): The shell do be used. Defaults to system shell,
                which is /bin/sh in most linux systems.
                If "Commands" is a list, this variable has no effect as
                the commands are not executed inside a shell
            Environment(dict): Stack-wide environment variables. These
                variables will be set in all actions, unless overridden
                by action-specific variables.

        Example Stack:
            StackType: Shell
            Shell: /bin/bash
            Environment:
              AWS_DEFAULT_REGION: us-west-2
            Actions:
              Create:
                Environment:
                  KMS_KEY: !Cloudformation {stack: kms-stack, output: key_arn}
                Commands: |
                  cmd1
                  cmd2
              Delete:
                Commands: cmd3
        """
        super(ShellStack, self).__init__(**kwargs)

        self.Shell = getattr(self, "Shell", "/bin/bash")
        self.Environment = getattr(self, "Environment", {})

        # Expands shell variables if command is a string
        for k, v in self.Actions.items():
            if isinstance(v["Commands"], str):
                self.Actions[k]["Commands"] = os.path.expandvars(v["Commands"])

    def _execute(self, action):
        """ Executes local commands in the system
        """
        if action not in self.Actions.keys():
            raise SystemExit("Action not available: {}".format(action))

        action_params = self.Actions[action]

        commands = action_params.get("Commands")
        if not commands:
            raise SystemExit(
                "At least one command must be specified in a shell stack"
            )

        if isinstance(commands, str):
            args = {"shell": True, "executable": self.Shell or None}
        elif isinstance(commands, list):
            args = {}
        else:
            raise SystemExit(
                "commands must be non a empty list or str: {}".format(commands)
            )
        # Merge global and action specific environment variables.
        # Action specific variables win.
        environment = dict(os.environ.copy(), **self.Environment)
        environment.update(action_params.get("Environment", {}))
        environment["BUILD_ID"] = self.BuildId

        process = subprocess.Popen(commands, env=environment, **args)
        process.wait()
        if process.returncode:
            logging.error(
                "Command {} exited with return code {}".format(
                    commands,
                    process.returncode
                )
            )
            raise SystemExit(process.returncode)

    def create(self, wait=False):
        self._execute(action="Create")

    def delete(self, wait=False):
        self._execute(action="Delete")

    def update(self, wait=False, review=False):
        self._execute(action="Update")

    def render(self, wait=False):
        print(yaml.dump(self.Actions, indent=2))
