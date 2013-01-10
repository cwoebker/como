#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A minimalistic utility to monitor and log battery health & more.

Homepage and documentation: github.com/cwoebker/como

Copyright (c) 2012, Cecil Woebker.
License: BSD (see LICENSE for details)
"""

from __future__ import with_statement

__author__ = 'cwoebker'
__version__ = '0.4.5'
__license__ = 'BSD'

from docopt import docopt

import sys
import os
import subprocess
import platform
import json
from datetime import datetime, date
import collections
import zlib

import requests

from clint.textui import puts, indent, colored

if platform.system() == "Darwin":
    from os.path import expanduser
elif platform.system() == "Linux":
    from crontab import CronTab
from tablib import Dataset

NO_DATABASE = 11

DEV_URL = 'http://127.0.0.1:5000'
REAL_URL = 'http://como.cwoebker.com'
SERVER_URL = REAL_URL
COMO_BATTERY_FILE = os.path.expanduser('~/.como')

locationCodes = ['1C', '2Z', '4H', '5K', '8H', '5D', '7J', 'CK', 'E', 'EE',
'F', 'FC', 'G8', 'GQ', 'PT', 'CY', 'QT', 'QP', 'RN', 'RM',
'SG', 'UV', 'U2', 'V7', 'VM', 'W8', 'WQ', 'XA', 'XB', 'YM']

### www.github.com/kennethreitz/spark.py - this code is taken from kennethreitz python port of holman's original spark

ticks = u'▁▂▃▅▆▇'


def spark_string(ints):
    """Returns a spark string from given iterable of ints."""
    step = ((max(i for i in ints if type(i) == int)) / float(len(ticks) - 1)) or 1
    return u''.join(ticks[int(round(i / step))] if i != '-' else '.' for i in ints)


def spark_print(ints):
    """Prints spark to given stream."""
    puts(spark_string(ints).encode('utf-8'))

##### Platform specific code #####

if platform.system() == "Darwin":
    def age():
        serial = {}
        cmd = "ioreg -l | awk '/IOPlatformSerialNumber/ { split($0, line, \"\\\"\"); printf(\"%s\\n\", line[4]); }'"
        serial['number'] = subprocess.check_output(cmd, shell=True).translate(None, '\n')
        temp = serial['number']
        for code in locationCodes:
            temp = temp.lstrip(code)
        serial['year'] = int(temp[0])
        serial['week'] = int(temp[1:3])

        creation = str(date.today().year)[:-1] + str(serial['year']) + str(serial['week']) + "1"

        timedelta = datetime.utcnow() - datetime.strptime(creation, '%Y%W%w')
        return timedelta.days / 30

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
        if battery['amperage'] > 999999:
            battery['amperage'] -= 18446744073709551615
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


def save():
    bat = battery()

    data = []
    if not os.path.exists(COMO_BATTERY_FILE):
        puts(colored.yellow("Creating ~/.como"))
        open(COMO_BATTERY_FILE, 'w').close()
        data = Dataset(headers=['time', 'capacity', 'cycles'])
    else:
        with open(COMO_BATTERY_FILE, 'r') as como:
            data = Dataset(headers=['time', 'capacity', 'cycles'])
            ### WATCH OUT: when directly importing through tablib header order got messed up...
            # http://stackoverflow.com/questions/10206905/how-to-convert-json-string-to-dictionary-and-save-order-in-keys
            data.dict = json.loads(zlib.decompress(como.read()), object_pairs_hook=collections.OrderedDict)  # this ensures right order
    data.append([datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                bat['maxcap'],
                bat['cycles'],
    ])
    with open(COMO_BATTERY_FILE, 'w') as como:
        como.write(zlib.compress(data.json))

    puts(colored.white("battery info saved (%s)" % str(data['time'][-1])))


def stats():
    with indent(4):
        title = "Como Statistics"
        puts(colored.green(title))
    puts("-" * (8 + len(title)))

    bat = battery()

    with indent(6, quote=colored.yellow('      ')):
        puts("Battery Serial: %s" % bat['serial'])
        puts("Age of Computer: %s months" % age())
        puts("Number of cycles: %s" % bat['cycles'])
        puts("Design Capacity: %s" % bat['designcap'])
        puts("Max Capacity: %s" % bat['maxcap'])
        puts("Capacity: %s" % bat['curcap'])
        if platform.system() == "Darwin":  # Mac OS only
            puts("Mac model: %s" % subprocess.check_output("sysctl -n hw.model", shell=True).rstrip("\n"))
            puts("Temperature: %s ℃" % (int(bat['temp']) / 100.))
            puts("Voltage: %s" % bat['voltage'])
            puts("Amperage: %s" % bat['amperage'])
            puts("Wattage: %s" % (bat['voltage'] * bat['amperage'] / 1000000.))
        if not os.path.exists(COMO_BATTERY_FILE):
            puts(colored.red("No como database."))
        else:
            # Gathering data
            with open(COMO_BATTERY_FILE, 'r') as como:
                data = Dataset()
                data.json = zlib.decompress(como.read())
            puts(colored.yellow("Database:"))
            with indent(4, quote=colored.yellow('    ')):
                puts("Number of Entries: %d" % len(data))
                puts("First save: " + str(data['time'][0]))
                puts("Last save: " + str(data['time'][-1]))
                timedelta = datetime.utcnow() - datetime.strptime(data['time'][0], "%Y-%m-%dT%H:%M:%S")
                puts("Age of Database: %s Days" % str(timedelta.days))
                # History
                puts(colored.yellow("History:"))
                history = []
                for element in data['capacity']:
                    history.append(int(element))
                spark_print([h - min(history) for h in history])
                # Cycles
                puts(colored.yellow("Cycles:"))
                cycles = []
                for element in data['cycles']:
                    if element == '-':
                        cycles.append(element)
                    else:
                        cycles.append(int(element))
                spark_print([c - min(c for c in cycles if type(c) == int) if c != '-' else c for c in cycles])


def export_csv():
    if not os.path.exists(COMO_BATTERY_FILE):
        puts(colored.red("No como database."))
    else:
        dataset = Dataset(headers=['time', 'capacity', 'cycles'])
        with open(COMO_BATTERY_FILE, 'r') as como:
            dataset.dict = json.loads(zlib.decompress(como.read()), object_pairs_hook=collections.OrderedDict)
        with open("como.csv", "w") as como:
            como.write(dataset.csv)
        puts(colored.white("saved file to current directory"))


def import_csv(path):
    if not os.path.exists(COMO_BATTERY_FILE):
        puts(colored.yellow("Creating ~/.como"))
        open(COMO_BATTERY_FILE, 'w').close()
        data = []
    else:
        with open(COMO_BATTERY_FILE, 'r') as como:
            data = json.loads(zlib.decompress(como.read()), object_pairs_hook=collections.OrderedDict)
    with open(expanduser(path), "r") as f:
        csv = f.read()
    current_dataset = Dataset(headers=['time', 'capacity', 'cycles'])
    current_dataset.dict = data
    import_dataset = Dataset()
    import_dataset.csv = csv
    new_dict = []  # need to find a way to edit dataset itself, this is stupid
    for element in import_dataset.dict:
        #if 'T' not in element['date']:
        try:
            element['date'] += "T00:00:00"
        except KeyError:
            pass
        new_dict.append(element)
    import_dataset.dict = new_dict
    new = current_dataset.stack(import_dataset).sort('time')

    with open(COMO_BATTERY_FILE, 'w') as como:
        como.write(zlib.compress(new.json))

    puts(colored.white("battery statistics imported"))


def upload():
    if platform.system() == "Darwin":
        UPLOAD_URL = SERVER_URL + "/upload"
        cmd = "ioreg -l | awk '/IOPlatformSerialNumber/ { split($0, line, \"\\\"\"); printf(\"%s\\n\", line[4]); }'"
        computer_serial = subprocess.check_output(cmd, shell=True).translate(None, '\n')
        bat = battery()
        model = subprocess.check_output("sysctl -n hw.model", shell=True).rstrip("\n")
        data = {'computer': computer_serial, 'model': model, 'battery': bat['serial'], 'design': bat['designcap'], 'age': age()}
        files = {'como': open(expanduser("~/.como"), 'rb')}
        r = requests.post(UPLOAD_URL, files=files, data=data)
        if r.status_code == requests.codes.ok:
            puts("data uploaded")
        else:
            puts("upload failed")
    else:
        puts("no uploading on this operating system")


def open_page():
    cmd = "ioreg -l | awk '/IOPlatformSerialNumber/ { split($0, line, \"\\\"\"); printf(\"%s\\n\", line[4]); }'"
    os.system("open %s/battery/%s" % (SERVER_URL, subprocess.check_output(cmd, shell=True).translate(None, '\n')))


def auto_upload():
    APPLE_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cwoebker.como-update</string>
    <key>OnDemand</key>
    <true/>
    <key>RunAtLoad</key>
    <false/>
    <key>Program</key>
    <string>%s upload</string>
    <key>StartCalendarInterval</key>
    <dict>
      <key>Hour</key>
      <integer>11</integer>
      <key>Minute</key>
      <integer>0</integer>
    </dict>
</dict>
</plist>"""
    if platform.system() == "Darwin":
        PLIST_PATH = expanduser("~/Library/LaunchAgents/com.cwoebker.como-update.plist")
        if os.path.exists(PLIST_PATH):
            os.system("launchctl unload %s" % PLIST_PATH)
            os.remove(PLIST_PATH)
            puts(colored.white("como will not upload data"))
        else:
            with open(PLIST_PATH, "w") as f:
                f.write(APPLE_PLIST % os.popen('which como').read().rstrip('\n'))
            os.system("launchctl load %s" % PLIST_PATH)
            puts(colored.white("como will automatically upload the data"))
    elif platform.system() == "Linux":
        user_cron = CronTab()
        user_cron.read()
        if len(user_cron.find_command("como-update")) > 0:
            user_cron.remove_all("como-update")
            user_cron.write()
            puts(colored.white("como will not upload data"))
        else:
            job = user_cron.new(command="como-update")
            job.minute.every(2)
            #job.minute.on(0)
            #job.hour.on(19)
            user_cron.write()
            puts(colored.white("como will automatically upload the data"))


def auto():
    APPLE_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cwoebker.como</string>
    <key>OnDemand</key>
    <true/>
    <key>RunAtLoad</key>
    <false/>
    <key>Program</key>
    <string>%s</string>
    <key>StartCalendarInterval</key>
    <array>
        <dict>
          <key>Hour</key>
          <integer>20</integer>
          <key>Minute</key>
          <integer>0</integer>
        </dict>
        <dict>
          <key>Hour</key>
          <integer>14</integer>
          <key>Minute</key>
          <integer>0</integer>
        </dict>
        <dict>
          <key>Hour</key>
          <integer>8</integer>
          <key>Minute</key>
          <integer>0</integer>
        </dict>
    </array>
</dict>
</plist>"""
    if platform.system() == "Darwin":
        PLIST_PATH = expanduser("~/Library/LaunchAgents/com.cwoebker.como.plist")
        if os.path.exists(PLIST_PATH):
            os.system("launchctl unload %s" % PLIST_PATH)
            os.remove(PLIST_PATH)
            puts(colored.white("como will only run manually"))
        else:
            with open(PLIST_PATH, "w") as f:
                f.write(APPLE_PLIST % os.popen('which como').read().rstrip('\n'))
            os.system("launchctl load %s" % PLIST_PATH)
            puts(colored.white("como will run automatically"))
    elif platform.system() == "Linux":
        user_cron = CronTab()
        user_cron.read()
        if len(user_cron.find_command("como")) > 0:
            user_cron.remove_all("como")
            user_cron.writcoe()
            puts(colored.white("como will only run manually"))
        else:
            job = user_cron.new(command="como")
            job.minute.every(2)
            #job.minute.on(0)
            #job.hour.on(19)
            user_cron.write()
            puts(colored.white("como will run automatically"))


def reset():
    if os.path.exists(COMO_BATTERY_FILE):
        sure = raw_input("Are you sure? this will remove everything! [yes/no] ")
        if sure == "yes":
            os.remove(COMO_BATTERY_FILE)
            puts(colored.white("cleared history"))
    else:
        puts(colored.white("no como database"))


def run():
    if platform.system() not in ['Darwin', 'Linux']:
        puts(colored.red("Operating System not supported."), stream=sys.stderr.write)
        return 1
    define = """como.

Usage:
  como
  como reset
  como stats
  como import <file>
  como export
  como upload
  como open
  como auto
  como auto upload
  como -h | --help
  como --version

Options:
  -h, --help
  --version

"""
    args = docopt(define, help=True, version=("como v" + str(__version__)))
    if args["reset"]:
        reset()
    elif args["auto"]:
        if args["upload"]:
            auto_upload()
        else:
            auto()
    elif args["stats"]:
        stats()
    elif args["import"]:
        import_csv(args["<file>"])
    elif args["export"]:
        export_csv()
    elif args["upload"]:
        upload()
    elif args["open"]:
        open_page()
    else:
        save()

if __name__ == "__main__":
    run()
