# -*- coding: utf-8 -*-
import ast
import re
from setuptools import setup, find_packages

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('codev/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

REQUIRES = [
    'click==6.6',
    'PyYAML==3.11',
    'colorama==0.3.7',
]

cmdclass = {}
ext_modules = []

setup(
    name='codev',
    version=version,
    description="Continuous delivery tool",
    author="Jan Češpivo (http://www.basecue.com/)",
    author_email="jan.cespivo@gmail.com",
    license="Apache 2.0",
    url="http://www.basecue.com/codev/",
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    scripts=['codev/control/bin/codev', 'codev/perform/bin/codev-perform', 'codev/perform/bin/codev-status'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=REQUIRES,
    cmdclass=cmdclass,
    ext_modules=ext_modules
)
