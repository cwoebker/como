# -*- coding: utf-8 -*-
"""
como.core - the basic ingredients to a great battery
"""

import os
import json
import zlib
import collections
from datetime import datetime
import subprocess
import hashlib

from clint.textui import puts, colored, indent
from tablib import Dataset

from paxo.command import cmd
from paxo.util import is_osx, is_lin, is_win
from paxo.text import spark_string, message, info, title, warning, error

from como.battery import get_battery, get_age
from como.settings import COMO_BATTERY_FILE, SERVER_URL

if is_lin:
    from crontab import CronTab

if is_osx:
    import requests


def create_database():
    warning("Creating ~/.como")
    open(COMO_BATTERY_FILE, 'w').close()
    return Dataset(headers=['time', 'capacity', 'cycles'])


def read_database():
    with open(COMO_BATTERY_FILE, 'r') as como:
        data = Dataset(headers=['time', 'capacity', 'cycles'])
        # http://stackoverflow.com/questions/10206905/
        # how-to-convert-json-string-to-dictionary-and-save-order-in-keys
        data.dict = json.loads(
            zlib.decompress(como.read()),
            object_pairs_hook=collections.OrderedDict)
        return data


def auto_upload():
    apple_plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" """ + \
""" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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
    elif is_win:
        error("Sorry there is no auto-upload for windows.")


def auto_save():
    apple_plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" """ + \
""" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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
    elif is_win:
        error("Sorry there is no auto-upload for windows.")


@cmd(help="Save battery information to database.")
def cmd_save(args):
    bat = get_battery()

    if not os.path.exists(COMO_BATTERY_FILE):
        data = create_database()
    else:
        data = read_database()
    if is_win:
        bat['cycles'] = None
    data.append([
        datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
        bat['maxcap'],
        bat['cycles'],
    ])

    with open(COMO_BATTERY_FILE, 'w') as como:
        como.write(zlib.compress(data.json))

    message("battery info saved (%s)" % str(data['time'][-1]))


@cmd(help="Delete database.")
def cmd_reset(args):
    if os.path.exists(COMO_BATTERY_FILE):
        sure = raw_input("Are you sure? this will remove everything! [y/n] ")
        if sure == "y":
            os.remove(COMO_BATTERY_FILE)
            info("removed database")
    else:
        warning("no como database")


@cmd(help="Show database information.")
def cmd_data(args):
    if not os.path.exists(COMO_BATTERY_FILE):
        puts(colored.yellow("No como database."))
    else:
        data = read_database()
        title("Como Database")
        with indent(6, quote='    '):
            puts("Number of Entries: %d" % len(data))
            puts("First save: " + str(data['time'][0]))
            puts("Last save: " + str(data['time'][-1]))
            timedelta = datetime.utcnow() - datetime.strptime(
                data['time'][0], "%Y-%m-%dT%H:%M:%S")
            puts("Age of Database: %s Days" % str(timedelta.days))
            # History Graphs
            if not is_win:
                history = []
                for element in data['capacity']:
                    history.append(int(element))
                cycles = []
                for element in data['cycles']:
                    if element:
                        cycles.append(int(element))
                    else:
                        cycles.append(element)
                history = [h - min(history) for h in history]
                cycles = [
                    c - min(c for c in cycles if type(c) == int)
                    if type(c) == int else c for c in cycles
                ]
                text1 = str(spark_string(history).encode('utf-8'))
                text2 = str(spark_string(cycles).encode('utf-8'))
                warning("Capacity:")
                puts(text1)
                warning("Cycles:")
                puts(text2)


@cmd(help="Show battery information.")
def cmd_info(args):
    title("Como Info")

    bat = get_battery()

    with indent(6, quote='      '):
        puts("Battery Serial: %s" % bat['serial'])
        puts("Max Capacity: %s" % bat['maxcap'])
        puts("Capacity: %s" % bat['curcap'])
        if is_osx or is_lin:
            puts("Number of cycles: %s" % bat['cycles'])
            puts("Design Capacity: %s" % bat['designcap'])
        if is_osx:
            puts("Mac model: %s" % subprocess.check_output(
                "sysctl -n hw.model", shell=True).rstrip("\n"))
            puts("Age of Computer: %s months" % get_age())
            # puts("Temperature: %s ℃" % (int(bat['temp']) / 100.))
        if is_osx or is_win:
            puts("Voltage: %s" % bat['voltage'])
            puts("Amperage: %s" % bat['amperage'])
            puts("Wattage: %s" % (bat['voltage'] * bat['amperage'] / 1000000.))


def import_format(element):
    try:
        element['date'] += "T00:00:00"
        element['loadcycles'] = None if (
            element['loadcycles'] == '-') else int(element['loadcycles'])
    except KeyError:
        element['cycles'] = None if (
            element['cycles'] == 'None') else int(element['cycles'])
    element['capacity'] = int(element['capacity'])
    return element


@cmd(help="Import data from .csv file.", usage="import <file>")
def cmd_import(args):
    if not os.path.exists(COMO_BATTERY_FILE):
        current_dataset = create_database()
    else:
        current_dataset = read_database()
    if os.path.exists(args.get(0)):
        import_dataset = Dataset()
        with open(os.path.expanduser(args.get(0)), "r") as import_file:
            import_dataset.csv = import_file.read()
        import_dataset.dict = map(import_format, import_dataset.dict)
        new = current_dataset.stack(import_dataset).sort('time')

        with open(COMO_BATTERY_FILE, 'w') as como:
            como.write(zlib.compress(new.json))

        puts(colored.white("battery statistics imported"))
    else:
        error("Couldn't open file: %s" % args.get(0))


@cmd(help="Export data to local .csv file.")
def cmd_export(args):
    if not os.path.exists(COMO_BATTERY_FILE):
        error("No como database.")
    else:
        if os.path.exists("como.csv"):
            sure = raw_input(
                "Do you want to replace the old export file (como.csv)?" +
                " [y/n] ")
            if sure != 'y':
                return
        dataset = read_database()
        with open("como.csv", "w") as como:
            como.write(dataset.csv)
        message("saved file to current directory")


@cmd(help="Upload data to server.")
def cmd_upload(args):
    if not os.path.exists(COMO_BATTERY_FILE):
        error("No como database.")
    else:
        if is_osx:
            url = SERVER_URL + "/upload"
            cmd = "ioreg -l | awk '/IOPlatformSerialNumber/ " + \
                  "{ split($0, line, \"\\\"\"); printf(\"%s\\n\", line[4]); }'"
            computer_serial = subprocess.check_output(
                cmd, shell=True).translate(None, '\n')
            bat = get_battery()
            model = subprocess.check_output(
                "sysctl -n hw.model", shell=True).rstrip("\n")
            data = {
                'computer': hashlib.md5(computer_serial).hexdigest(),
                'model': model,
                'battery': hashlib.md5(bat['serial']).hexdigest(),
                'design': bat['designcap'],
                'age': get_age()
            }
            files = {'como': open(COMO_BATTERY_FILE, 'rb')}
            response = requests.post(url, files=files, data=data)
            if response.status_code == requests.codes.ok:
                puts("data uploaded")
            else:
                puts("upload failed")
        else:
            message("no uploading on this operating system")


@cmd(help="Open your battery page.")
def cmd_open(args):
    cmd = "ioreg -l | awk '/IOPlatformSerialNumber/ " + \
          "{ split($0, line, \"\\\"\"); printf(\"%s\\n\", line[4]); }'"
    out = subprocess.check_output(cmd, shell=True).translate(None, '\n')
    os.system("open %s/battery?id=%s" % (SERVER_URL, out))


@cmd(help="Initialize como.")
def cmd_init(args):
    cmd_save(args)
    cmd_automate(args)
    cmd_save(args)  # double save so user sees actual graph on site
    cmd_upload(args)
    cmd_open(args)


@cmd(help="Automate saving and uploading.")
def cmd_automate(args):
    auto_save()
    auto_upload()
