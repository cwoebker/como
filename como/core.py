# -*- coding: utf-8 -*-
"""
como.core - the basic ingredients to a great battery
"""

import sys
import os
import json
import zlib
import collections
from datetime import datetime
import subprocess

from clint.textui import puts, colored, indent
from tablib import Dataset
import requests

from .battery import get_battery, get_age
from .settings import COMO_BATTERY_FILE, SERVER_URL
from .help import is_osx, is_lin, spark_print

if is_lin:
    from crontab import CronTab


class ExitStatus:
    """Exit status code constants."""
    OK = 0
    ERROR = 1


def show_error(msg):
    sys.stdout.flush()
    sys.stderr.write(msg + '\n')


def auto_upload():
    apple_plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cwoebker.como-update</string>
    <key>OnDemand</key>
    <true/>
    <key>RunAtLoad</key>
    <false/>
    <key>ProgramArguments</key>
    <array>
        <string>%s</string>
        <string>upload</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
      <key>Hour</key>
      <integer>11</integer>
      <key>Minute</key>
      <integer>0</integer>
    </dict>
</dict>
</plist>"""
    if is_osx:
        plist_path = os.path.expanduser(
            "~/Library/LaunchAgents/com.cwoebker.como-update.plist")
        if os.path.exists(plist_path):
            os.system("launchctl unload %s" % plist_path)
            os.remove(plist_path)
            puts(colored.white("como will not upload data"))
        else:
            with open(plist_path, "w") as plist_file:
                plist_file.write(
                    apple_plist % os.popen('which como').read().rstrip('\n'))
            os.system("launchctl load %s" % plist_path)
            puts(colored.white("como will automatically upload the data"))
    elif is_lin:
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
    apple_plist = """<?xml version="1.0" encoding="UTF-8"?>
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
    if is_osx:
        plist_path = os.path.expanduser(
            "~/Library/LaunchAgents/com.cwoebker.como.plist")
        if os.path.exists(plist_path):
            os.system("launchctl unload %s" % plist_path)
            os.remove(plist_path)
            puts(colored.white("como will only run manually"))
        else:
            with open(plist_path, "w") as plist_file:
                plist_file.write(
                    apple_plist % os.popen('which como').read().rstrip('\n'))
            os.system("launchctl load %s" % plist_path)
            puts(colored.white("como will run automatically"))
    elif is_lin:
        user_cron = CronTab()
        user_cron.read()
        if len(user_cron.find_command("como")) > 0:
            user_cron.remove_all("como")
            user_cron.write()
            puts(colored.white("como will only run manually"))
        else:
            job = user_cron.new(command="como")
            job.minute.every(2)
            #job.minute.on(0)
            #job.hour.on(19)
            user_cron.write()
            puts(colored.white("como will run automatically"))


def cmd_save(args):
    bat = get_battery()

    data = []
    if not os.path.exists(COMO_BATTERY_FILE):
        puts(colored.yellow("Creating ~/.como"))
        open(COMO_BATTERY_FILE, 'w').close()
        data = Dataset(headers=['time', 'capacity', 'cycles'])
    else:
        with open(COMO_BATTERY_FILE, 'r') as como:
            data = Dataset(headers=['time', 'capacity', 'cycles'])
            ### WATCH OUT: when directly importing through tablib header order
            #got messed up...
            # http://stackoverflow.com/questions/10206905/
            # how-to-convert-json-string-to-dictionary-and-save-order-in-keys
            data.dict = json.loads(
                zlib.decompress(como.read()),
                object_pairs_hook=collections.OrderedDict)
    data.append([
        datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
        bat['maxcap'],
        bat['cycles'],
    ])
    with open(COMO_BATTERY_FILE, 'w') as como:
        como.write(zlib.compress(data.json))

    puts(colored.white("battery info saved (%s)" % str(data['time'][-1])))


def cmd_reset(args):
    if os.path.exists(COMO_BATTERY_FILE):
        sure = raw_input("Are you sure? this will remove everything! [yes/no] ")
        if sure == "yes":
            os.remove(COMO_BATTERY_FILE)
            puts(colored.white("cleared history"))
    else:
        puts(colored.white("no como database"))


def cmd_info(args):
    with indent(4):
        title = "Como Info"
        puts(colored.green(title))
    puts("-" * (8 + len(title)))

    bat = get_battery()

    with indent(6, quote=colored.yellow('      ')):
        puts("Battery Serial: %s" % bat['serial'])
        puts("Age of Computer: %s months" % get_age())
        puts("Number of cycles: %s" % bat['cycles'])
        puts("Design Capacity: %s" % bat['designcap'])
        puts("Max Capacity: %s" % bat['maxcap'])
        puts("Capacity: %s" % bat['curcap'])
        if is_osx:
            puts("Mac model: %s" % subprocess.check_output(
                "sysctl -n hw.model", shell=True).rstrip("\n"))
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
                timedelta = datetime.utcnow() - datetime.strptime(
                    data['time'][0], "%Y-%m-%dT%H:%M:%S")
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
                    if element:
                        cycles.append(int(element))
                    else:
                        cycles.append(element)
                spark_print([c - min(c for c in cycles if type(c) == int)
                            if type(c) == int else c for c in cycles])


def cmd_import(args):
    if not os.path.exists(COMO_BATTERY_FILE):
        puts(colored.yellow("Creating ~/.como"))
        open(COMO_BATTERY_FILE, 'w').close()
        data = []
    else:
        with open(COMO_BATTERY_FILE, 'r') as como:
            data = json.loads(
                zlib.decompress(como.read()),
                object_pairs_hook=collections.OrderedDict)
    with open(os.path.expanduser(args.get(0)), "r") as import_file:
        csv = import_file.read()
    current_dataset = Dataset(headers=['time', 'capacity', 'cycles'])
    current_dataset.dict = data
    import_dataset = Dataset()
    import_dataset.csv = csv
    new_dict = []  # need to find a way to edit dataset itself, this is stupid
    for element in import_dataset.dict:
        #if 'T' not in element['date']:
        try:
            element['date'] += "T00:00:00"
            element['loadcycles'] = None if (
                element['loadcycles'] == '-') else int(element['loadcycles'])
        except KeyError:
            element['cycles'] = None if (
                element['cycles'] == '-') else int(element['cycles'])
        element['capacity'] = int(element['capacity'])
        new_dict.append(element)
    import_dataset.dict = new_dict
    new = current_dataset.stack(import_dataset).sort('time')

    with open(COMO_BATTERY_FILE, 'w') as como:
        como.write(zlib.compress(new.json))

    puts(colored.white("battery statistics imported"))


def cmd_export(args):
    if not os.path.exists(COMO_BATTERY_FILE):
        puts(colored.red("No como database."))
    else:
        dataset = Dataset(headers=['time', 'capacity', 'cycles'])
        with open(COMO_BATTERY_FILE, 'r') as como:
            dataset.dict = json.loads(
                zlib.decompress(como.read()),
                object_pairs_hook=collections.OrderedDict)
        with open("como.csv", "w") as como:
            como.write(dataset.csv)
        puts("saved file to current directory")


def cmd_upload(args):
    if is_osx:
        url = SERVER_URL + "/upload"
        cmd = "ioreg -l | awk '/IOPlatformSerialNumber/ { split($0, line, \"\\\"\"); printf(\"%s\\n\", line[4]); }'"
        computer_serial = subprocess.check_output(
            cmd, shell=True).translate(None, '\n')
        bat = get_battery()
        model = subprocess.check_output(
            "sysctl -n hw.model", shell=True).rstrip("\n")
        data = {
            'computer': computer_serial,
            'model': model,
            'battery': bat['serial'],
            'design': bat['designcap'],
            'age': get_age()
        }
        files = {'como': open(os.path.expanduser("~/.como"), 'rb')}
        response = requests.post(url, files=files, data=data)
        if response.status_code == requests.codes.ok:
            puts("data uploaded")
        else:
            puts("upload failed")
    else:
        puts("no uploading on this operating system")


def cmd_open(args):
    cmd = "ioreg -l | awk '/IOPlatformSerialNumber/ { split($0, line, \"\\\"\"); printf(\"%s\\n\", line[4]); }'"
    os.system("open %s/battery?id=%s" % (SERVER_URL, subprocess.check_output(
        cmd, shell=True).translate(None, '\n')))
