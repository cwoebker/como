#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

import coco

APP_NAME = 'coco'


# Grab requirments.
with open('reqs.txt') as f:
    require = f.readlines()

tests_require = ['nose']

setup(
    name=APP_NAME,
    version=coco.__version__,
    description='battery health & more',
    long_description=coco.__doc__,
    author=coco.__author__,
    author_email='cwoebker@gmail.com',
    url='https://cwoebker.github.com/coco',
    install_requires=require,
    tests_require=tests_require,
    test_suite='nose.collector',
    #py_modules=['coco'],
    #scripts=['coco.py'],
    include_package_data=True,
    license='BSD',
    platforms='mac',
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
            'coco = coco:main',
        ],
    },
    zip_safe=False,
)
