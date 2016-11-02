# -*- coding: utf-8 -*-
import imp
from os import path
from setuptools import setup, find_packages

info = imp.load_source('info', path.join('.', 'codev', 'info.py'))

NAME = info.NAME
DESCRIPTION = info.DESCRIPTION
AUTHOR = info.AUTHOR
AUTHOR_EMAIL = info.AUTHOR_EMAIL
URL = info.URL


from git import Repo
repo = Repo()
branch = repo.active_branch.name

if branch == 'master':
    branch_ident = ''
else:
    branch_ident = '-{branch}'.format(
        branch=branch
    )

VERSION = '{version}{branch_ident}'.format(version=info.VERSION, branch_ident=branch_ident)

REQUIRES = ['click==6.6', 'PyYAML==3.11', 'paramiko==2.0.0', 'colorama==0.3.7', 'GitPython==2.0.2']

cmdclass = {}
ext_modules = []

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license="Apache 2.0",
    url=URL,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    scripts=['codev/bin/codev'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    install_requires=REQUIRES,
    cmdclass=cmdclass,
    ext_modules=ext_modules
)
