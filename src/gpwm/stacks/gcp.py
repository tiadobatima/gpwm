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
import time
import yaml


from apiclient.errors import HttpError

import gpwm.stacks
import gpwm.utils


class GCPStack(gpwm.stacks.BaseStack):
    GCP_DEPLOYMENT_BODY_KEYS = [
        "description",
        "fingerprint",
        "labels",
        "name",
        "target"
    ]

    def __init__(self, **kwargs):
        """
        Args:
            All GCP DM supported sections are allowed, plus:
            - BuildId(str): The build ID. This will be merged to the
              parameters dict.
            - project(str): The project the deployment is going to be created
              under

        All arguments provided will be set as object attributes.
        Unlike Clouformation class, the attributes of the object will not be
        used directly to feed the actions, as we need to massage the data quite
        a bit in GCP
        """
        super(GCPStack, self).__init__(**kwargs)

        # make sure "local" is a list of dicts. Making a shallow copy
        # just in case
        self.labels = getattr(self, "labels", {})
        labels = self.labels.copy()
        if isinstance(labels, dict):
            self.labels = [{"key": k, "value": v} for k, v in labels.items()]
        self.labels.append({"key": "build_id", "value": self.BuildId})
        self.target = self.assemble_target()
        self.body = self.assemble_body()

    def assemble_target(self):
        """ Assembles the target argument for DM's resource representation

        In GCP, the arguments mapping provided in a config file don't follow
        the DM's API, so we have to reorder the arguments before feeding them
        to the API.

        """
        # build imports
        imports = []
        for i in getattr(self, "imports", []):
            with open(i["path"]) as f:
                content = f.read().rstrip()
            imports.append(
                {
                    "content": content,
                    "name": i.get("name", i["path"])
                }
            )

        # build config
        config = {}
        for k, v in self.__dict__.items():
            if k in ["imports", "resources", "outputs"]:
                config[k] = v
        return {
            "imports": imports,
            "config": {
                "content": yaml.dump(
                    config,
                    indent=2,
                    default_flow_style=False
                )
            }
        }

    def assemble_body(self):
        """ Assembles the target argument for DM's resource representation

        In GCP, the arguments mapping provided in a config file don't follow
        the DM's API, so we have to reorder the arguments before feeding them
        to the API.

        """
        body = {}
        for k, v in self.__dict__.items():
            if k in self.GCP_DEPLOYMENT_BODY_KEYS:
                body[k] = v
        return body

    def get(self):
        """ Gets the deployment data.

        This method returns an empty dict instead of a 404 exception raised by
        the GCP SDK.
        """

        try:
            return gpwm.utils.GCP_API.deployments().get(
                project=self.project,
                deployment=self.name
            ).execute()
        except HttpError as exc:
            if exc.resp["status"] == "404":
                return {}
            raise SystemExit(
                "HTTP error {}: {}".format(exc.resp["status"], exc.content)
            )

    def wait(self, interval=5, timeout=300):
        """ A waiter for stack completeness

        GCP SDK doesn't provide a waiter, so improvising a quick on here.

        Args:
            interval(int): Interval between probes in seconds
            timeout(int): The total wait timeout in seconds

        """
        n_probes = int(timeout/interval)
        for i in range(0, n_probes):
            time.sleep(interval)
            deployment = self.get()
            if deployment and deployment["operation"]["status"] == "DONE":
                break

    def create(self, wait=False):
        gpwm.utils.GCP_API.deployments().insert(
            project=self.project,
            body=self.body
        ).execute()
        if wait:
            self.wait()

    def delete(self, wait=False):
        if not self.get():
            raise SystemExit("Deployment doesn't exist: {}".format(self.name))
        gpwm.utils.GCP_API.deployments().delete(
            project=self.project,
            deployment=self.name
        ).execute()
        if wait:
            self.wait()

    def update(self, wait=False, review=False):
        gpwm.utils.GCP_API.deployments().insert(
            project=self.project,
            body=self.body
        ).execute()
        if wait:
            self.wait()

    def upsert(self, wait=False):
        if self.get():
            self.update(wait=wait)
        else:
            self.create(wait=wait)

    def render(self):
        deployment = {"project": self.project, "body": self.body}
        print(yaml.safe_dump(deployment, indent=2))

    def validate(self):
        pass
