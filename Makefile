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
SHELL = /bin/bash

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


install-test-requirements:
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements/pip-test.txt -r requirements/pip-install.txt


#
# Configure virtual + dev environment
#

# install virtual environment
# IMPORTANT: activate venv after running this
venv:
	python3 -m venv $@
	@echo "===> IMPORTANT: Activate your venv if you're developing locally:"
	@echo "========># source $@/bin/activate"
	@touch $@

# install package in develoment mode (for local dev only!)
develop:
	python3 -m pip install -e .
	$(MAKE) install-test-requirements



#
# style, coverage and tests
#

# installs test requeriments and check code style
check: install-test-requirements check-style

# checks code style
check-style:
	python3 setup.py flake8
#python3 setup.py lint

# check test coverage
check-coverage:
	python3 -m pytest --cov=$(PACKAGE) ${TESTDIR}/

# tests the tool
test: check
	python3 setup.py test


# builds the package
dist: clean
	python3 setup.py sdist
	python3 setup.py bdist_wheel

upload:
	twine upload dist/*

# installs this package and its requirements
install:
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements/pip-install.txt
	python3 setup.py install


#
# cleanup
#
clean-all: clean clean-venv

# cleans up python compiled files, built packages, tests results, caches, etc
clean:
	find src/$(PACKAGE) \( -path '*__pycache__/*' -o -name __pycache__ \) -delete
	find $(TESTDIR) \( -path '*__pycache__/*' -o -name __pycache__ \) -delete
	rm -rf build dist *.egg-info .cache .eggs .coverage

# cleans up a python virtual environment.
# IMPORTANT: deactivate venv prior to running this!
clean-venv:
	rm -rf venv

