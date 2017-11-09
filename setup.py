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


from setuptools import find_packages
from setuptools import setup


def get_version():
    with open("VERSION") as f:
        return f.readline().rstrip()


def get_install_requirements():
    with open("requirements/pip-install.txt") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def get_test_requirements():
    with open("requirements/pip-test.txt") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


config = {
    "name": "gpwm",
    "version": get_version(),
    "description": "Multi cloud provider infrastructure-as-code wrapper",
    "author": "Gustavo Baratto",
    "author_email": "gbaratto@gmail.com",
    "url": "https://github.com/tiadobatima/gpwm",
    "packages": find_packages("src"),
    "package_dir": {'': 'src'},
    "entry_points": {
        "console_scripts": ["gpwm=gpwm.cli:main"]
    },
    "setup_requires": ["pytest-runner"],
    "install_requires": get_install_requirements(),
    "tests_require": get_test_requirements()
}


setup(**config)
