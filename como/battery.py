# -*- coding: utf-8 -*-
"""
como.battery - the power connection
"""

# http://www.macrumors.com/2010/04/16/apple-tweaks-serial-number-format-with-new-macbook-pro/

import sys
from datetime import date, datetime

from clint.textui import puts

from .help import is_osx, is_lin, is_win
from como.settings import LOCATION_CODES

# OS dependent imports

if is_osx or is_lin:
    import subprocess

if is_win:
    try:
        import win32api
    except ImportError:
        print "The windows python api isn't installed. Please install pywin32."
        sys.exit(1)
    try:
        import wmi
    except ImportError:
        print "Make sure wmi is installed."
        sys.exit(1)


def get_age():
    """Get age of computer. Only OSX for now"""
    if is_osx:
        serial = {}
        cmd = "ioreg -l | awk '/IOPlatformSerialNumber/ " + \
              "{ split($0, line, \"\\\"\"); printf(\"%s\\n\", line[4]); }'"
        serial['number'] = subprocess.check_output(
            cmd, shell=True).translate(None, '\n')
        temp = serial['number']
        if len(temp) == 11:
            for code in LOCATION_CODES:
                temp = temp.lstrip(code)
            serial['year'] = int(temp[0])
            serial['week'] = int(temp[1:3])
        else:
            serial['year'] = 0
            serial['week'] = 0
            return "N/A"

        creation = str(date.today().year)[:-1] + str(
            serial['year']) + str(serial['week']) + "1"

        timedelta = datetime.utcnow() - datetime.strptime(creation, '%Y%W%w')
        return timedelta.days / 30
    else:
        puts("no age on this operating system")
        sys.exit(0)


def grep_filter(list, term):
    for line in list:
        if term in line:
            yield line


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
        legacy = bat[2].lstrip('LegacyBatteryInfo=')
        battery['cycles'] = int(
            legacy.translate(
                None, '{}=').split(',')[5].lstrip('CycleCount'))
        battery['amperage'] = int(
            legacy.translate(
                None, '{}=').split(',')[0].lstrip('Amperage'))
        if battery['amperage'] > 999999:
            battery['amperage'] -= 18446744073709551615
        battery['voltage'] = int(
            legacy.translate(
                None, '{}=').split(',')[4].lstrip('Voltage'))
        battery['designcap'] = int(bat[3].lstrip('DesignCapacity='))
    elif is_lin:
        battery['serial'] = subprocess.check_output(
            "grep \"^serial number\" " +
            "/proc/acpi/battery/BAT0/info | awk '{ print $3 }'",
            shell=True
        ).translate(None, '\n')
        battery['state'] = subprocess.check_output(
            "grep \"^charging state\" " +
            "/proc/acpi/battery/BAT0/state | awk '{ print $3 }'",
            shell=True
        )
        battery['maxcap'] = float(subprocess.check_output(
            "grep \"^last full capacity\" " +
            "/proc/acpi/battery/BAT0/info | awk '{ print $4 }'",
            shell=True
        ))
        battery['curcap'] = float(subprocess.check_output(
            "grep \"^remaining capacity\" " +
            "/proc/acpi/battery/BAT0/state | awk '{ print $3 }'",
            shell=True
        ))
        battery['designcap'] = float(subprocess.check_output(
            "grep \"^design capacity:\" " +
            "/proc/acpi/battery/BAT0/info | awk '{ print $3 }'",
            shell=True
        ))
        battery['cycles'] = int(subprocess.check_output(
            "grep \"^cycle count\" /proc/acpi/battery/BAT0/info",
            shell=True
        ).lstrip("cycle count:").translate(None, ' '))
    elif is_win:
        # Get power status of the system using ctypes to call GetSystemPowerStatus
        """import ctypes
        from ctypes import wintypes

        class SYSTEM_POWER_STATUS(ctypes.Structure):
            _fields_ = [
                ('ACLineStatus', wintypes.BYTE),
                ('BatteryFlag', wintypes.BYTE),
                ('BatteryLifePercent', wintypes.BYTE),
                ('Reserved1', wintypes.BYTE),
                ('BatteryLifeTime', wintypes.DWORD),
                ('BatteryFullLifeTime', wintypes.DWORD),
            ]

        SYSTEM_POWER_STATUS_P = ctypes.POINTER(SYSTEM_POWER_STATUS)

        GetSystemPowerStatus = ctypes.windll.kernel32.GetSystemPowerStatus
        GetSystemPowerStatus.argtypes = [SYSTEM_POWER_STATUS_P]
        GetSystemPowerStatus.restype = wintypes.BOOL

        status = SYSTEM_POWER_STATUS()
        if not GetSystemPowerStatus(ctypes.pointer(status)):
            raise ctypes.WinError()
        print 'ACLineStatus', status.ACLineStatus
        print 'BatteryFlag', status.BatteryFlag
        print 'BatteryLifePercent', status.BatteryLifePercent
        print 'BatteryLifeTime', status.BatteryLifeTime
        print 'BatteryFullLifeTime', status.BatteryFullLifeTime"""
        #c = wmi.WMI()
        t = wmi.WMI(moniker="//./root/wmi")
        #b = c.Win32_Battery()[0]
        battery['maxcap'] = t.ExecQuery("Select * from BatteryFullChargedCapacity")[0].FullChargedCapacity
        batt = t.ExecQuery("Select * from BatteryStatus where Voltage > 0")[0]
        battery['curcap'] = batt.RemainingCapacity
        battery['voltage'] = batt.Voltage
        battery['amperage'] = batt.ChargeRate
        if batt.Charging:
            battery['amperage'] = batt.ChargeRate
        elif batt.Discharging:
            battery['amperage'] = batt.DischargeRate
        else:
            battery['amperage'] = 0
        battery['serial'] = batt.Name

    return battery
