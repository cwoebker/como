# -*- coding: utf-8 -*-
"""
como.battery - the power connection
"""

import sys
import subprocess
from datetime import date, datetime

from clint.textui import puts

from .help import is_osx, is_lin
from .settings import LOCATION_CODES


def get_age():
    """Get age of computer. Only OSX for now"""
    if is_osx:
        serial = {}
        cmd = "ioreg -l | awk '/IOPlatformSerialNumber/ " + \
              "{ split($0, line, \"\\\"\"); printf(\"%s\\n\", line[4]); }'"
        serial['number'] = subprocess.check_output(
            cmd, shell=True).translate(None, '\n')
        temp = serial['number']
        for code in LOCATION_CODES:
            temp = temp.lstrip(code)
        serial['year'] = int(temp[0])
        serial['week'] = int(temp[1:3])

        creation = str(date.today().year)[:-1] + str(
            serial['year']) + str(serial['week']) + "1"

        timedelta = datetime.utcnow() - datetime.strptime(creation, '%Y%W%w')
        return timedelta.days / 30
    else:
        puts("no age on this operating system")
        sys.exit(0)


def get_battery():
    """Gets all information associated with the battery from respective
    system sources"""
    battery = {}
    if is_osx:
        bat = subprocess.check_output(
            'ioreg -w0 -l | grep Capacity',
            shell=True).translate(None, ' "|').split('\n')
        battery['serial'] = subprocess.check_output(
            'ioreg -w0 -l | grep BatterySerialNumber',
            shell=True).translate(None, '\n "|').lstrip('BatterySerialNumber=')
        battery['temp'] = int(subprocess.check_output(
            'ioreg -w0 -l | grep Temperature',
            shell=True).translate(None, '\n "|').lstrip('Temperature='))
        battery['maxcap'] = int(bat[0].lstrip('MaxCapacity='))
        battery['curcap'] = int(bat[1].lstrip('CurrentCapacity='))
        battery['legacy'] = bat[2].lstrip('LegacyBatteryInfo=')
        battery['cycles'] = int(
            battery['legacy'].translate(
                None, '{}=').split(',')[5].lstrip('CycleCount'))
        battery['amperage'] = int(
            battery['legacy'].translate(
                None, '{}=').split(',')[0].lstrip('Amperage'))
        if battery['amperage'] > 999999:
            battery['amperage'] -= 18446744073709551615
        battery['voltage'] = int(
            battery['legacy'].translate(
                None, '{}=').split(',')[4].lstrip('Voltage'))
        battery['designcap'] = int(bat[3].lstrip('DesignCapacity='))
    elif is_lin:
        battery['serial'] = subprocess.check_output(
            "grep \"^serial number\" " + \
            "/proc/acpi/battery/BAT0/info | awk '{ print $3 }'",
            shell=True
        ).translate(None, '\n')
        battery['state'] = subprocess.check_output(
            "grep \"^charging state\" " + \
            "/proc/acpi/battery/BAT0/state | awk '{ print $3 }'",
            shell=True
        )
        battery['maxcap'] = float(subprocess.check_output(
            "grep \"^last full capacity\" " + \
            "/proc/acpi/battery/BAT0/info | awk '{ print $4 }'",
            shell=True
        ))
        battery['curcap'] = float(subprocess.check_output(
            "grep \"^remaining capacity\" " + \
            "/proc/acpi/battery/BAT0/state | awk '{ print $3 }'",
            shell=True
        ))
        battery['designcap'] = float(subprocess.check_output(
            "grep \"^design capacity:\" " + \
            "/proc/acpi/battery/BAT0/info | awk '{ print $3 }'",
            shell=True
        ))
        battery['cycles'] = int(subprocess.check_output(
            "grep \"^cycle count\" /proc/acpi/battery/BAT0/info",
            shell=True
        ).lstrip("cycle count:").translate(None, ' '))
    return battery
