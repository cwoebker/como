#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A minimalistic utillity to monitor and log battery health & more. (Mac only)


Homepage and documentation: cwoebker.github.com/coco

Copyright (c) 2012, Cecil Woebker.
License: BSD (see LICENSE for details)
"""

from __future__ import with_statement

__author__ = 'Cecil Woebker'
__version__ = '0.0.2'
__license__ = 'BSD'

from docopt import docopt

import sys
import os
import subprocess
import json
from datetime import datetime

COCO_BATTERY_FILE = os.path.expanduser('~/.coco')


def main():
    info = subprocess.check_output('ioreg -w0 -l | grep Capacity', shell=True)

    batList = info.translate(None, ' "|').split('\n')

    maxcapacity = batList[0].lstrip('MaxCapacity=')
    currentcapacity = batList[1].lstrip('CurrentCapacity=')
    legacyinfo = batList[2].lstrip('LegacyBatteryInfo=')
    designcapacity = batList[3].lstrip('DesignCapacity=')
    cyclecount = legacyinfo.translate(None, '{}=').split(',')[5].lstrip('CycleCount')

    if not os.path.exists(COCO_BATTERY_FILE):
        print "Creating ~/.coco"
        data = []
        open(COCO_BATTERY_FILE, 'w').close()
    else:
        with open(COCO_BATTERY_FILE, 'r') as coco:
            data = json.loads(coco.read())
    data.append({'time': str(datetime.now()),
                'maxcap': maxcapacity,
                'curcap': currentcapacity,
                'cycles': cyclecount,
                'designcap': designcapacity,
    })
    with open(COCO_BATTERY_FILE, 'w') as coco:
        coco.write(json.dumps(data))

    #print "Battery Info saved."


def stats():
    if not os.path.exists(COCO_BATTERY_FILE):
        print "No coco database."
        return 1
    else:
        print "Coco Statistics"
        with open(COCO_BATTERY_FILE, 'r') as coco:
            data = json.loads(coco.read())
        print "Number of Entries: %d" % len(data)


def rm():
    os.remove(COCO_BATTERY_FILE)


def test(number):
    for i in range(number):
        main()


if __name__ == "__main__":
    define = """coco.

Usage:
  coco.py
  coco.py rm
  coco.py stats
  coco.py test <n>
  coco.py -h | --help
  coco.py --version

Options:
  -h, --help            Show this screen.
  --version             Show version.

"""
    args = docopt(define, help=True, version=("coco v" + str(__version__)))
    if args["rm"]:
        rm()
    elif args["stats"]:
        stats()
    elif args["test"]:
        test(int(args["<n>"]))
    else:
        main()
