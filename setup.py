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
VERSION = info.VERSION
REQUIRES = ['click', 'pyyaml', 'paramiko', 'colorama', 'gitpython']

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
        'Development Status :: 2 - Pre-Alpha',
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
