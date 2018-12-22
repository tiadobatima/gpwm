#
# The correct way to setup a dev environment:
#
# $ make venv
# $ source venv/bin/activate
# $ make develop
#

# And the correct way of deleting the dev environment:
# 
# $ deactivate
# $ make clean-venv (or make clean-all)
#

PACKAGE := gpwm
TESTDIR := tests
PYTHON  := python3.7
SHELL   := /bin/bash

help:
	@echo "venv       Create a pyvenv virtual envionment (not virtualenv)"
	@echo "develop    Install dependencies and install package in editable mode"
	@echo "check      Run style checks and coverage: "
	@echo "test       Run pytest"
	@echo "dist       Create wheel package"
	@echo "install    Install wheel package"
	@echo "clean clean-all  Clean up and clean up removing virtualenv"

.ONESHELL:
.PHONY: check check-style check-coverage test dist develop install clean-all clean clean-venv ci-build ci-test ci-upload ci-cleanup install-test-requirements clean-pip-dependencies

prerequisites:
	${PYTHON} -m pip install -r requirements/prerequisites.txt


#install-test-requirements:
#	${PYTHON} -m pip install --upgrade pip
#	${PYTHON} -m pip install -r requirements/pip-test.txt -r requirements/pip-install.txt
#
venv:
	${PYTHON} -m tox -e venv
	@echo "===> IMPORTANT: Activate your venv if you're developing locally:"
	@echo "========># source $@/bin/activate"
	@touch $@

docs:
	sphinx-apidoc -f -o docs/api src/gpwm

test:
	${PYTHON} -m pytest -v

tox:
	${PYTHON} -m tox

#
# style, coverage and tests
#

# installs test requeriments and check code style
check: check-style

# checks code style
check-style:
	${PYTHON} setup.py flake8
#${PYTHON} setup.py lint

# check test coverage
check-coverage:
	${PYTHON} -m pytest --cov=${PACKAGE} ${TESTDIR}/

# tests the tool
#test: check
#	${PYTHON} -m pytest

build:
		${PYTHON} setup.py sdist bdist_wheel

install:
		${PYTHON} -m pip install dist/${PACKAGE}-$$(cat VERSION)-py2.py3-none-any.whl

uninstall:
		${PYTHON} -m pip uninstall ${PACKAGE} -y

upload:
	twine upload dist/*

#
# cleanup
#
clean-all: clean clean-venv

# cleans up python compiled files, built packages, tests results, caches, etc
clean:
	find src/${PACKAGE} \( -path '*__pycache__/*' -o -name __pycache__ \) -delete
	find ${TESTDIR} \( -path '*__pycache__/*' -o -name __pycache__ \) -delete
	rm -rf build dist *.egg-info .cache .eggs .coverage

# cleans up a python virtual environment.
# IMPORTANT: deactivate venv prior to running this!
clean-venv:
	rm -rf venv
