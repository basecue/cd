# codev - continuous delivery tool


There is no stable version (yet). Only beta is available now.

## Installation


Install prerelease version (notice the --pre parameter):

```bash
$ pip3 install codev --pre
```

## Usage

At a high level there is "control" mode, which checks a current version of configuration, creates isolated environment and delegates requested action to codev in "perform" mode in the isolated environment.

There are three basic types of objects, which define the deployment:

 - `environment` - general box, which should include the one or more `infrastructure` objects. 
 - `infrastructure` - defines machines (types, numbers etc.)
 - `installation` - defines source of application (version, branch, commit, directory...)

At first create `.codev` file in the main directory of your git repository and configure your project deployment via this file. 

### Initiate installation project in isolation and start deployment:

```bash
$ codev install -e <environment> -i <infrastructure> -s <installation>
```

### Create transition from one installation to another.

The first use will install the `<source installation>` and next time it will use `<next installation>`.
You can identify this mode in output messages via special 'transition' information `<source installation> -> <next installation>` where current installation is highlighted.

```bash
$ codev install -e <environment> -i <infrastructure> -s <source installation> -n <next installation>
```
 
## Versioning

Version identifier complies with the format defined in [PEP 440] (https://www.python.org/dev/peps/pep-0440/)

  - major version - Releases with incompatible changes between control (isolation) and perform modes, it includes different command line interfaces, python versions etc.
  - minor version - Releases with small incompatible changes in configuration.
  - micro versions - Bugfix releases and compatible changes.
  

Actually Codev is designed to handle with most of incompatible changes, so don't worry!

## Legal

Copyright 2016 by Jan Češpivo (jan.cespivo@gmail.com)

Licensed under the [Apache License, Version 2.0] (http://www.apache.org/licenses/LICENSE-2.0)
