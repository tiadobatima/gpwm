# Development

## Prerequisites

### Cygwin

* python3.6
* python3.6-devel
* libffi-devel
* openssl-devel

## Development environment setup

The local development environment can be setup with [venv](https://docs.python.org/3/library/venv.html),
which is included with python3 and deprecades the 3rd party package
*virtualenv*.

If *pyvenv* is used:
```
make venv
source venv/bin/activate
make develop
```

To stop and delete your *venv*:
```
deactivate
make clean-venv (or make clean-all)
```


If the system-wide python installation is used, ie *pyvenv* is not used:
```
make develop
```

## Directory Structure

This project adopts the *src/package* directory structure explained
[here](https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure),
and [here](https://docs.pytest.org/en/latest/goodpractices.html#tests-outside-application-code).

```
.
├── docs
│   ├── aws.md
│   ├── development.md
│   ├── emu.png
│   ├── gcp.md
│   ├── gpwm.jpg
│   └── shell.md
├── env
├── examples
│   ├── consumables
│   │   ├── account
│   │   │   └── common.mako
│   │   ├── application
│   │   │   ├── autoscaling.mako
│   │   │   └── rds.mako
│   │   ├── network
│   │   │   ├── securitygroup.mako
│   │   │   ├── subnet.mako
│   │   │   └── vpc.mako
│   │   └── security
│   │       └── accesspolicy.mako
│   └── stacks
│       ├── aws
│       │   ├── account
│       │   │   └── common.mako
│       │   ├── network
│       │   │   ├── citrix-demo-dev.mako
│       │   │   ├── securitygroup-demo-dev.yaml
│       │   │   ├── subnet-demo-dev.mako
│       │   │   ├── vpc-demo-dev.mako
│       │   │   └── vpc-demo-dev.yaml
│       │   └── security
│       │       └── accesspolicy-demo-dev-jira.yaml
│       └── gcp
│           ├── ox.txt
│           ├── vm1.mako
│           └── vm.yaml
├── Makefile
├── README.md
├── requirements
│   ├── deb-build.txt
│   ├── deb-install.txt
│   ├── pip-install.txt
│   └── pip-test.txt
├── setup.cfg
├── setup.py
├── src
│   └── gpwm
│       ├── cli.py
│       ├── __init__.py
│       ├── stacks
│       │   ├── aws.py
│       │   ├── gcp.py
│       │   ├── __init__.py
│       │   └── shell.py
│       └── utils.py
└── tests
    ├── conftest.py
```

## Dependencies

Python doesn't have a really good, unified way of resolving package
dependencies. Setuptool has a lot of problems with dependency resolution,
especially the fact that it tries to download source and build dependencies 
instead of just installing the wheels.

Plus, rarely a piece of software has *python-only* dependencies. A pip package
always depend on a pre-installed *deb* or *rpm* that's not python
related. And on top of that, python packages have at least two sets internal
dependencies:
* one set of dependencies for testing/building
* one set of depencies for installation/deployment

Because of that, the widely used *requirements.txt* has been expanded.

The repository has a *requirements* directory with: 
```
requirements/
|-- pip-install.txt
|-- pip-test.txt
|-- deb-build.txt
|-- deb-install.txt
|-- rpm-build.txt
|-- rpm-install.txt
```

* The file *pip-install.txt* lists the package dependencies for installation, in
a way very similar to setuptools' *install_requires*.
* The file *pip-test.txt* lists package dependencies for testing, since normally
testing packages are not needed in "production".
* The file *deb-build.txt* lists *debian* packages needed for
building/testing the application and normally should not be installed in
"production".
* The file *deb-install.txt* lists *debian* packages that are needed to
run the application.
* The file *rpm-build.txt* lists *rpm* packages needed for
building/testing the application and normally should not be installed in
"production".
* The file *rpm-install.txt* lists *rpm* packages that are needed to
run the application.


### Testing

* Testing is being done with *pytest*.
* Code coverage checks is done with *coverage* package, invoked with *pytest*.
If coverage is below 80%, checks are set to fail.
* Code style checks are with both *flake8*, and *pylint*.

This is how tests are executed:
```
make test
```

### Building

The build process results in a [wheel](http://wheel.readthedocs.io/en/latest/)
 package being created:

```
make dist
```

### Installing

installs the [wheel](http://wheel.readthedocs.io/en/latest/) package from a
build in the system python path or inside the *venv* (if activated)
```
make install
```

### Cleaning up

To clean local python cached pyo/pyc files, build, dist, eggs, etc:
```
make clean
```

To stop and delete your *venv*:
```
deactivate
make clean-venv (or make clean-all)
```

To clean all the above:
```
deactivate
make clean-all
```

