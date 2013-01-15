#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

import como

APP_NAME = 'como'


# Grab requirments.
with open('reqs.txt') as f:
    required = f.readlines()

tests_require = ['nose']

settings = dict()


settings.update(
    name=APP_NAME,
    version=como.__version__,
    description='como: batteries complete',
    long_description=open('README.md').read(),
    author=como.__author__,
    author_email='me@cwoebker.com',
    url='como.cwoebker.com',
    download_url='http://github.com/cwoebker/como',
    license=como.__licence__,
    packages=find_packages(),
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
    zip_safe=False,
)

setup(**settings)
