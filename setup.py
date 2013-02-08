#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import como
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Grab requirments.
with open('reqs.txt') as f:
    required = f.readlines()

tests_require = ['nose']

settings = dict()


# Publish Helper.
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()


settings.update(
    name='como',
    version=como.__version__,
    description='como: batteries complete',
    long_description=open('README.md').read(),
    author=como.__author__,
    author_email='me@cwoebker.com',
    url='como.cwoebker.com',
    download_url='http://github.com/cwoebker/como',
    license=como.__licence__,
    packages=['como'],
    install_requires=required,
    entry_points={
        'console_scripts': [
            'como = como.cli:main',
        ],
    },
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Topic :: Software Development',
        'Topic :: Terminals',
        'Topic :: Utilities',
    ),
)

setup(**settings)
