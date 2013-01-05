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
    require = f.readlines()

tests_require = ['nose']

setup(
    name=APP_NAME,
    version=como.__version__,
    description='battery health & more',
    long_description=como.__doc__,
    author=como.__author__,
    author_email='me@cwoebker.com',
    url='https://github.com/cwoebker/como',
    packages=find_packages(),
    include_package_data=True,
    install_requires=require,
    extras_requires={},
    tests_require=tests_require,
    test_suite='nose.collector',
    #py_modules=['como'],
    scripts=['como.py'],
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'Topic :: Software Development',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ),
    entry_points={
        'console_scripts': [
            'como = como:run',
        ],
    },
    zip_safe=False,
)
