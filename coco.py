#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import tablib
from datetime import datetime

def main():
    info = subprocess.check_output('ioreg -w0 -l | grep Capacity', shell=True)

    batList = info.translate(None, ' "|').split('\n') 

    maxcapacity = batList[0].lstrip('MaxCapacity=')
    currentcapacity = batList[1].lstrip('CurrentCapacity=')
    legacyinfo = batList[2].lstrip('LegacyBatteryInfo=')
    designcapacity = batList[3].lstrip('DesignCapacity=')
    cyclecount = legacyinfo.translate(None, '{}=').split(',')[5].lstrip('CycleCount')

    data = tablib.Dataset(headers=['time', 'maxcap', 'curcap', 'cycles', 'designcap'])
    data.rpush((str(datetime.now()), maxcapacity, currentcapacity, cyclecount, designcapacity))

    with open(os.path.expanduser('~/.coco'), 'a') as coco:
        json_string = data.json + '\n'
        coco.write(json_string)

    print "Battery Info saved."

if __name__ == "__main__":
	main()