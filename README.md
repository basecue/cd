# codev - continuous delivery tool

Highly configurable tool for automatic creating and configuration environments.

codev is designed for ease of use.

It's also:

 * lightweight
 * decentralized
 * extensible
 * backwards compatible

There is no stable version (yet). Only beta is available now.

## Installation

### Ubuntu
```bash
$ apt-get install python3-pip
$ pip3 install setuptools
$ pip3 install codev --pre
```

## Basic usage

### Overview
At a high level there is "control" mode, which checks a current version of settings, creates isolated environment and delegates requested action to codev in "perform" mode in the isolated environment.

There are three basic types of objects, which define the deployment:

 - `environment` - general box, which should include the one or more `configuration` objects. 
 - `configuration` - defines infrastructure, provision, etc.
 - `installation` - defines source of application (version, branch, commit, directory...)

At first create `.codev` file in the main directory of your git repository and configure your project deployment via this file. <!--- TODO link to docs -->

### Initiate installation project in isolation and start deployment:

```bash
$ codev install -e <environment> -c <configuration> -s <installation>
```

### Create transition from one installation to another.

The first use will install the `<source installation>` and next time it will use `<next installation>`.
You can identify this mode in output messages via special 'transition' information `<source installation> -> <next installation>` where current installation is highlighted.

```bash
$ codev install -e <environment> -c <configuration> -s <source installation> -n <next installation>
```
 
## Versioning

Version identifier complies with the format defined in [PEP 440] (https://www.python.org/dev/peps/pep-0440/)

  - major version - Releases with incompatible changes between control (isolation) and perform modes, it includes different command line interfaces, python versions etc.
  - minor version - Releases with small incompatible changes in settings.
  - micro versions - Bugfix releases and compatible changes.
  

Actually Codev is designed to handle with most of incompatible changes, so don't worry!

## Legal

Copyright 2016 by Jan Češpivo (jan.cespivo@gmail.com)

Licensed under the [Apache License, Version 2.0] (http://www.apache.org/licenses/LICENSE-2.0)
