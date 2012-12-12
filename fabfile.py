from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm


def test():
    local('nosetests')


def publish():
    confirm("Are you sure?")
    local('python setup.py sdist upload')


def init():
    local('pip install -r reqs.txt --use-mirrors')


def reset():
    local('pip uninstall coco')


def version_raise():
    pass
