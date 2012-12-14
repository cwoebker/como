#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A minimalistic utility to monitor and log battery health & more.

Homepage and documentation: github.com/cwoebker/coco

Copyright (c) 2012, Cecil Woebker.
License: BSD (see LICENSE for details)
"""

from __future__ import with_statement

__author__ = 'cwoebker'
__version__ = '0.3.1'
__license__ = 'BSD'

from docopt import docopt

import sys
import os
import subprocess
import platform
import json
from datetime import datetime

from clint.textui import puts, indent, colored
if platform.system() == "Darwin":
    from os.path import expanduser
elif platform.system() == "Linux":
    from crontab import CronTab
from tablib import Dataset

NO_DATABASE = 11

COCO_BATTERY_FILE = os.path.expanduser('~/.coco')

locationCodes = ['1C', '2Z', '4H', '5K', '8H', '5D', '7J', 'CK', 'E', 'EE',
'F', 'FC', 'G8', 'GQ', 'PT', 'CY', 'QT', 'QP', 'RN', 'RM',
'SG', 'UV', 'U2', 'V7', 'VM', 'W8', 'WQ', 'XA', 'XB', 'YM']

### www.github.com/kennethreitz/spark.py - this code is taken from kennethreitz python port of holman's original spark

ticks = u'▁▂▃▅▆▇'


def spark_string(ints):
    """Returns a spark string from given iterable of ints."""
    step = ((max(ints)) / float(len(ticks) - 1)) or 1
    return u''.join(ticks[int(round(i / step))] for i in ints)


def spark_print(ints):
    """Prints spark to given stream."""
    puts(spark_string(ints).encode('utf-8'))

##### Platform specific code #####

if platform.system() == "Darwin":
    def serial():
        serial = {}
        cmd = "ioreg -l | awk '/IOPlatformSerialNumber/ { split($0, line, \"\\\"\"); printf(\"%s\\n\", line[4]); }'"
        serial['number'] = subprocess.check_output(cmd, shell=True).translate(None, '\n')
        temp = serial['number']
        for code in locationCodes:
            temp = temp.lstrip(code)
        serial['year'] = int(temp[0])
        serial['week'] = int(temp[1:3])
        return serial

    def battery():
        batList = subprocess.check_output('ioreg -w0 -l | grep Capacity', shell=True).translate(None, ' "|').split('\n')
        temp = subprocess.check_output('ioreg -w0 -l | grep Temperature', shell=True).translate(None, '\n "|').lstrip('Temperature=')
        battery = {}
        battery['serial'] = subprocess.check_output('ioreg -w0 -l | grep BatterySerialNumber', shell=True).translate(None, '\n "|').lstrip('BatterySerialNumber=')
        battery['temp'] = int(temp)
        battery['maxcap'] = int(batList[0].lstrip('MaxCapacity='))
        battery['curcap'] = int(batList[1].lstrip('CurrentCapacity='))
        battery['legacy'] = batList[2].lstrip('LegacyBatteryInfo=')
        battery['cycles'] = int(battery['legacy'].translate(None, '{}=').split(',')[5].lstrip('CycleCount'))
        battery['amperage'] = int(battery['legacy'].translate(None, '{}=').split(',')[0].lstrip('Amperage'))
        battery['voltage'] = int(battery['legacy'].translate(None, '{}=').split(',')[4].lstrip('Voltage'))
        battery['designcap'] = int(batList[3].lstrip('DesignCapacity='))
        return battery

elif platform.system() == "Linux":
    def battery():
        battery = {}
        battery['serial'] = subprocess.check_output("grep \"^serial number\" /proc/acpi/battery/BAT0/info | awk '{ print $3 }'", shell=True).translate(None, '\n')

        battery['state'] = subprocess.check_output("grep \"^charging state\" /proc/acpi/battery/BAT0/state | awk '{ print $3 }'", shell=True)
        battery['maxcap'] = float(subprocess.check_output("grep \"^last full capacity\" /proc/acpi/battery/BAT0/info | awk '{ print $4 }'", shell=True))
        battery['curcap'] = float(subprocess.check_output("grep \"^remaining capacity\" /proc/acpi/battery/BAT0/state | awk '{ print $3 }'", shell=True))
        battery['designcap'] = float(subprocess.check_output("grep \"^design capacity:\" /proc/acpi/battery/BAT0/info | awk '{ print $3 }'", shell=True))

        battery['cycles'] = int(subprocess.check_output("grep \"^cycle count\" /proc/acpi/battery/BAT0/info", shell=True).lstrip("cycle count:").translate(None, ' '))
        return battery


def main():
    bat = battery()

    data = []
    if not os.path.exists(COCO_BATTERY_FILE):
        puts(colored.yellow("Creating ~/.coco"))
        open(COCO_BATTERY_FILE, 'w').close()
    else:
        with open(COCO_BATTERY_FILE, 'r') as coco:
            data = json.loads(coco.read())
    data.append({'time': datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                'maxcap': bat['maxcap'],
                'cycles': bat['cycles'],
    })
    with open(COCO_BATTERY_FILE, 'w') as coco:
        coco.write(json.dumps(data))

    puts(colored.white("Battery Info saved. (%s)" % str(data[-1]['time'])))


def stats():
    with indent(4):
        title = "Coco Statistics"
        puts(colored.green(title))
    puts("-" * (8 + len(title)))

    bat = battery()
    # ser = serial()

    with indent(6, quote=colored.yellow('      ')):
        #puts(colored.yellow("Current:"))
        #with indent(4, quote=colored.yellow('    ')):
        puts("Serial Number: %s" % bat['serial'])
        puts("Number of cycles: %s" % bat['cycles'])
        puts("Design Capacity: %s" % bat['designcap'])
        puts("Max Capacity: %s" % bat['maxcap'])
        puts("Capacity: %s" % bat['curcap'])
        if platform.system() == "Darwin":  # Mac OS only
            puts("Temperature: %s ℃" % (int(bat['temp']) / 100.))
            puts("Voltage: %s" % bat['voltage'])
            puts("Amperage: %s" % bat['amperage'])
        if not os.path.exists(COCO_BATTERY_FILE):
            puts(colored.red("No coco database."))
        else:
            # Gathering data
            with open(COCO_BATTERY_FILE, 'r') as coco:
                data = json.loads(coco.read())
            puts(colored.yellow("Database:"))
            with indent(4, quote=colored.yellow('    ')):
                # puts("Creation Time: %s Year, %s Week" % (ser['year'], ser['week']))
                puts("Number of Entries: %d" % len(data))
                puts("First save: " + str(data[0]['time']))
                puts("Last save: " + str(data[-1]['time']))
                timedelta = datetime.now() - datetime.strptime(data[0]['time'], "%Y-%m-%dT%H:%M:%S")
                puts("Age of Database: %s Days" % str(timedelta.days))
                # History
                puts(colored.yellow("History:"))
                history = []
                for element in data:
                    history.append(int(element['maxcap']))
                spark_print([h - min(history) for h in history])
                # Cycles
                puts(colored.yellow("Cycles:"))
                cycles = []
                for element in data:
                    cycles.append(int(element['cycles']))
                spark_print([c - min(cycles) for c in cycles])


def save():
    if not os.path.exists(COCO_BATTERY_FILE):
        puts(colored.red("No coco database."))
    else:
        with open(COCO_BATTERY_FILE, 'r') as coco:
            data = json.loads(coco.read())
        csv = Dataset()
        for item in data:
            csv.append(item.values())
        csv.headers = ['Cycles', 'Capacity', 'Time']
        with open("coco.csv", "w") as coco:
            coco.write(csv.csv)
        puts(colored.white("saved file to current directory"))


APPLE_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cwoebker.coco</string>
    <key>OnDemand</key>
    <true/>
    <key>RunAtLoad</key>
    <false/>
    <key>Program</key>
    <string>%s</string>
    <key>StartCalendarInterval</key>
    <dict>
      <key>Hour</key>
      <integer>18</integer>
      <key>Minute</key>
      <integer>30</integer>
    </dict>
</dict>
</plist>"""


def auto():
    if platform.system() == "Darwin":
        PLIST_PATH = expanduser("~/Library/LaunchAgents/com.cwoebker.coco.plist")
        if os.path.exists(PLIST_PATH):
            os.system("launchctl unload %s" % PLIST_PATH)
            os.remove(PLIST_PATH)
            puts(colored.white("coco will only run manually"))
        else:
            with open(PLIST_PATH, "w") as f:
                f.write(APPLE_PLIST % os.popen('which coco').read().rstrip('\n'))
            os.system("launchctl load %s" % PLIST_PATH)
            puts(colored.white("coco will run automatically"))
    elif platform.system() == "Linux":
        user_cron = CronTab()
        user_cron.read()
        if len(user_cron.find_command("coco")) > 0:
            user_cron.remove_all("coco")
            user_cron.write()
            puts(colored.white("coco will only run manually"))
        else:
            job = user_cron.new(command="coco")
            job.minute.every(2)
            #job.minute.on(0)
            #job.hour.on(19)
            user_cron.write()
            puts(colored.white("coco will run automatically"))


def reset():
    os.remove(COCO_BATTERY_FILE)
    puts(colored.white("cleared history"))


def run():
    if platform.system() not in ['Darwin', 'Linux']:
        puts(colored.red("Operating System not supported."), stream=sys.stderr.write)
        return 1
    define = """coco.

Usage:
  coco.py
  coco.py reset
  coco.py stats
  coco.py save
  coco.py auto
  coco.py -h | --help
  coco.py --version

Options:
  -h, --help
  --version

"""
    args = docopt(define, help=True, version=("coco v" + str(__version__)))
    if args["reset"]:
        sure = raw_input("Are you sure? this will remove everything! [yes/no] ")
        if sure == "yes":
            reset()
    elif args["stats"]:
        stats()
    elif args["save"]:
        save()
    elif args["auto"]:
        auto()
    else:
        main()

if __name__ == "__main__":
    run()
