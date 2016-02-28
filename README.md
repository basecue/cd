Continuous delivery tool
========================

Install
-------

```bash
$ pip3 install codev
```

Usage
-----
At a high level there is "control" mode, which checks a current version of configuration, creates isolated environment and delegates requested action to codev in "perform" mode in the isolated environment.



Versioning
-----------------
  - major version - Releases with incompatible changes between control and perform modes, it includes different command line interfaces, python versions etc.
  - minor version - Releases with small incompatible changes in configuration.
  - micro versions - Bugfix releases and compatible changes.

Actually Codev is designed to handle with most of incompatible changes, so don't worry!