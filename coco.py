#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
        sys.stdout.write('.')


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'stats':
            stats()
        elif sys.argv[1] == 'rm':
            rm()
        elif sys.argv[1] == 'test':
            test(int(sys.argv[2]))
    else:
        main()
